import math
from datetime import datetime, time, timedelta

# Cuadrante simulado por empleado (horarios en UTC y coordenadas de sede)
MOCK_ROSTER = {
    "EMP-9482": {
        "shift_name": "Mañana (09:00-18:00)",
        "start_time": time(9, 0),
        "end_time": time(18, 0),
        "tolerance_minutes": 15,
        "workplace": "Madrid - Sede Central",
        "target_lat": 40.4168,
        "target_lon": -3.7038,
        "max_radius_meters": 250,
    },
    "EMP-9445": {
        "shift_name": "Intensivo (08:00-17:00)",
        "start_time": time(8, 0),
        "end_time": time(17, 0),
        "tolerance_minutes": 15,
        "workplace": "Madrid - Hub Operaciones",
        "target_lat": 40.4168,
        "target_lon": -3.7038,
        "max_radius_meters": 250,
    },
}


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en metros entre dos coordenadas GPS (Fórmula de Haversine)."""
    earth_radius_m = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(earth_radius_m * c, 2)


def evaluate_attendance(payload: dict) -> dict:
    """
    Cruza el evento de fichaje con el cuadrante simulado y devuelve
    el dictamen ('VALIDO' o 'ANOMALO') con sus metadatos de auditoría.
    """
    employee_id = str(payload.get("employee_id", ""))
    event_type = str(payload.get("event_type", "CHECK_IN")).upper()
    raw_ts = str(payload.get("timestamp", ""))
    location = payload.get("location") or {}

    roster = MOCK_ROSTER.get(employee_id)
    if not roster:
        return {
            "ValidationStatus": "ANOMALO",
            "AnomalyReason": "SIN_TURNO_ASIGNADO",
            "AssignedShift": "NO_PLANIFICADO",
            "DistanceMeters": -1.0,
        }

    reasons = []
    event_dt = datetime.fromisoformat(raw_ts)
    event_date = event_dt.date()
    tz = event_dt.tzinfo

    # 1. Validación de horario según el cuadrante
    tolerance = timedelta(minutes=roster["tolerance_minutes"])

    if event_type == "CHECK_IN":
        expected_start = datetime.combine(event_date, roster["start_time"], tzinfo=tz)
        if event_dt > (expected_start + tolerance):
            delay_min = int((event_dt - expected_start).total_seconds() // 60)
            reasons.append(f"RETRASO_ENTRADA ({delay_min} min)")
        elif event_dt < (expected_start - timedelta(minutes=60)):
            reasons.append("ENTRADA_DEMASIADO_TEMPRANA")

    elif event_type == "CHECK_OUT":
        expected_end = datetime.combine(event_date, roster["end_time"], tzinfo=tz)
        if event_dt < (expected_end - tolerance):
            early_min = int((expected_end - event_dt).total_seconds() // 60)
            reasons.append(f"SALIDA_ANTICIPADA ({early_min} min)")

    # 2. Validación de perímetro GPS (Geofencing)
    lat = float(location.get("latitude", 0.0))
    lon = float(location.get("longitude", 0.0))
    distance_m = calculate_distance_meters(
        lat, lon, roster["target_lat"], roster["target_lon"]
    )

    if distance_m > roster["max_radius_meters"]:
        reasons.append(f"UBICACION_FUERA_DE_RANGO ({int(distance_m)}m)")

    status = "VALIDO" if not reasons else "ANOMALO"
    reason_text = "NINGUNA" if not reasons else " | ".join(reasons)

    return {
        "ValidationStatus": status,
        "AnomalyReason": reason_text,
        "AssignedShift": roster["shift_name"],
        "DistanceMeters": distance_m,
    }