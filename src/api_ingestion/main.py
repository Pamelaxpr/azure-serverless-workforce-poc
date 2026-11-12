import os
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import pyotp

from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueClient
from azure.storage.queue import TextBase64EncodePolicy

# Variables de entorno inyectadas en Azure (con fallback local)
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "stworkforcepoc")
QUEUE_NAME = os.getenv("AZURE_STORAGE_QUEUE_NAME", "queue-workforce-events")
QUEUE_SERVICE_URL = f"https://{STORAGE_ACCOUNT_NAME}.queue.core.windows.net"

# Clientes asíncronos globales de Azure
credential: DefaultAzureCredential = None
queue_client: QueueClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global credential, queue_client
    # 1. Inicialización de la credencial y el cliente al arrancar el servidor
    credential = DefaultAzureCredential()
    queue_client = QueueClient(
        account_url=QUEUE_SERVICE_URL,
        queue_name=QUEUE_NAME,
        credential=credential,
        message_encode_policy=TextBase64EncodePolicy()  # Codifica en Base64 para compatibilidad total en Azure
    )
    yield
    # 2. Cierre explícito de conexiones al apagar el servidor
    await queue_client.close()
    await credential.close()

app = FastAPI(
    title="Azure Workforce Ingestion API",
    version="1.0.0",
    lifespan=lifespan
)

# Diccionario de prueba con claves secretas Base32 por empleado
MOCK_EMPLOYEE_KEYS = {
    "EMP-9482": "JBSWY3DPEHPK3PXP"
}

# --- ESQUEMAS PYDANTIC ---
class EventType(str, Enum):
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud GPS")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud GPS")

class CheckInRequest(BaseModel):
    employee_id: str = Field(..., min_length=3, max_length=50)
    event_type: EventType
    timestamp: datetime
    totp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    location: GeoLocation

    @field_validator("totp_code")
    @classmethod
    def validate_numeric_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código TOTP debe contener únicamente caracteres numéricos.")
        return v

# --- LÓGICA TOTP ---
def verify_totp(secret_key: str, code: str, window: int = 1) -> bool:
    totp = pyotp.TOTP(secret_key)
    return totp.verify(code, valid_window=window)

# --- RUTAS DE LA API ---
@app.get("/")
def health_check():
    return {"status": "ok", "service": "api_ingestion"}

@app.post("/api/v1/check-in", status_code=status.HTTP_202_ACCEPTED)
async def process_check_in(payload: CheckInRequest):
    # 1. Buscar clave del empleado
    secret_key = MOCK_EMPLOYEE_KEYS.get(payload.employee_id)
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El empleado '{payload.employee_id}' no existe."
        )

    # 2. Verificar código TOTP
    if not verify_totp(secret_key=secret_key, code=payload.totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código TOTP inválido o expirado."
        )

    # 3. Serializar payload a JSON
    message_content = payload.model_dump_json()

    # 4. Enviar mensaje de forma asíncrona a Azure Storage Queue
    try:
        sent_message = await queue_client.send_message(message_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al publicar el evento en Azure Storage Queue: {str(e)}"
        )

    # 5. Respuesta de confirmación con el ID asignado por Azure
    return {
        "status": "accepted",
        "message": "Fichaje validado y encolado correctamente en Azure Storage Queue.",
        "employee_id": payload.employee_id,
        "event_type": payload.event_type,
        "message_id": sent_message.id
    }