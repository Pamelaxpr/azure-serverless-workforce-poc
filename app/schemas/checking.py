from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"


class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud GPS")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud GPS")


class CheckInRequest(BaseModel):
    employee_id: str = Field(
        ..., min_length=3, max_length=50, example="EMP-9482"
    )
    event_type: EventType
    timestamp: datetime = Field(
        ..., description="Timestamp UTC del momento del fichaje"
    )
    totp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Código de 6 dígitos numéricos del QR dinámico",
    )
    location: GeoLocation

    @field_validator("totp_code")
    @classmethod
    def validate_numeric_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código TOTP debe contener únicamente caracteres numéricos.")
        return v