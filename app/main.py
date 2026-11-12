from fastapi import FastAPI, HTTPException, status
from app.schemas.checkin import CheckInRequest
from app.services.totp_service import verify_totp

app = FastAPI(
    title="Azure Workforce Ingestion API",
    version="1.0.0"
)

# Mock temporal de claves Base32 (en producción se obtendrán de Key Vault / Base de Datos)
MOCK_EMPLOYEE_KEYS = {
    "EMP-9482": "JBSWY3DPEHPK3PXP"
}

@app.post("/api/v1/check-in", status_code=status.HTTP202_ACCEPTED)
async def process_check_in(payload: CheckInRequest):
    # 1. Recuperar clave secreta del empleado
    secret_key = MOCK_EMPLOYEE_KEYS.get(payload.employee_id)
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP404_NOT_FOUND,
            detail=f"El empleado '{payload.employee_id}' no existe o no tiene token 2FA asignado."
        )

    # 2. Validar token TOTP del QR dinámico
    is_valid = verify_totp(secret_key=secret_key, code=payload.totp_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP401_UNAUTHORIZED,
            detail="Código TOTP inválido o expirado."
        )

    # 3. Payload y TOTP válidos (Aquí se conectará el encolado en Storage Queue)
    return {
        "status": "accepted",
        "message": "Fichaje validado correctamente y aceptado para procesamiento.",
        "employee_id": payload.employee_id,
        "event_type": payload.event_type
    }