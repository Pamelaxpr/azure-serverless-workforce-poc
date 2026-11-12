import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone

from azure.data.tables.aio import TableClient
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue import TextBase64DecodePolicy
from azure.storage.queue.aio import QueueClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("async_worker")

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "stworkforcepoc")
QUEUE_NAME = os.getenv("AZURE_STORAGE_QUEUE_NAME", "queue-workforce-events")
TABLE_NAME = os.getenv("AZURE_STORAGE_TABLE_NAME", "tblworkforceattendance")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

shutdown_event = asyncio.Event()


def handle_shutdown() -> None:
    logger.info("Señal de apagado recibida. Cerrando worker de forma segura...")
    shutdown_event.set()


def build_table_entity(payload: dict, message_id: str) -> dict:
    """Transforma el evento JSON de la cola en una entidad válida para Azure Table Storage."""
    # Limpiamos caracteres no permitidos en RowKey (/, \, #, ?)
    raw_ts = str(payload.get("timestamp", datetime.now(timezone.utc).isoformat()))
    safe_ts = raw_ts.replace("/", "-").replace("\\", "-").replace("#", "").replace("?", "")

    location = payload.get("location") or {}

    return {
        "PartitionKey": str(payload["employee_id"]),
        "RowKey": f"{safe_ts}_{message_id}",
        "EventType": str(payload["event_type"]),
        "EventTimestamp": raw_ts,
        "Latitude": float(location.get("latitude", 0.0)),
        "Longitude": float(location.get("longitude", 0.0)),
        "ProcessedAt": datetime.now(timezone.utc).isoformat(),
        "QueueMessageId": message_id,
    }


async def process_messages() -> None:
    queue_url = f"https://{ACCOUNT_NAME}.queue.core.windows.net"
    table_url = f"https://{ACCOUNT_NAME}.table.core.windows.net"

    credential = DefaultAzureCredential()
    queue_client = QueueClient(
        account_url=queue_url,
        queue_name=QUEUE_NAME,
        credential=credential,
        message_decode_policy=TextBase64DecodePolicy(),
    )
    table_client = TableClient(
        endpoint=table_url,
        table_name=TABLE_NAME,
        credential=credential,
    )

    logger.info(
        "Worker iniciado. Escuchando cola '%s' -> tabla '%s' en '%s'",
        QUEUE_NAME,
        TABLE_NAME,
        ACCOUNT_NAME,
    )

    try:
        while not shutdown_event.is_set():
            messages_found = False

            # Leemos lotes de hasta 10 mensajes ocultándolos 30s mientras se procesan
            async for msg in queue_client.receive_messages(
                messages_per_page=10, visibility_timeout=30
            ):
                messages_found = True
                try:
                    payload = json.loads(msg.content)
                    entity = build_table_entity(payload, msg.id)

                    # 1. Persistir en Table Storage (operación idempotente)
                    await table_client.upsert_entity(entity=entity)

                    # 2. Eliminar de la cola SOLO tras confirmar el guardado en base de datos
                    await queue_client.delete_message(msg)

                    logger.info(
                        "Fichaje persistido: Empleado=%s | Tipo=%s | RowKey=%s",
                        entity["PartitionKey"],
                        entity["EventType"],
                        entity["RowKey"],
                    )
                except Exception as exc:
                    # Si falla, no borramos el mensaje; volverá a ser visible tras 30s
                    logger.error("Error procesando mensaje %s: %s", msg.id, exc)

            if not messages_found:
                try:
                    await asyncio.wait_for(
                        shutdown_event.wait(), timeout=POLL_INTERVAL_SECONDS
                    )
                except asyncio.TimeoutError:
                    pass
    finally:
        await queue_client.close()
        await table_client.close()
        await credential.close()
        logger.info("Conexiones con Azure cerradas correctamente.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown)
        except NotImplementedError:
            pass
    loop.run_until_complete(process_messages())