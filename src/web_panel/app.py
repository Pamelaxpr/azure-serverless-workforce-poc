import os
from datetime import datetime, timezone
import pandas as pd
import pyotp
import requests
import streamlit as st

# URL de tu API desplegada en Azure Container Apps (permite override por variable de entorno)
API_BASE_URL = os.getenv(
    "WORKFORCE_API_URL",
    "https://ca-workforce-api.icysand-5b9d1ec8.spaincentral.azurecontainerapps.io",
)

# Clave secreta de prueba sincronizada con MOCK_EMPLOYEE_KEYS de la API
MOCK_SECRETS = {
    "EMP-9482": "JBSWY3DPEHPK3PXP",
}

PRESET_LOCATIONS = {
    "Madrid - Sede Central (Válida - 3m)": (40.4168, -3.7038),
    "Madrid - Ubicación Remota (Anómala - >250m)": (40.4350, -3.6900),
}

st.set_page_config(
    page_title="Workforce Control Horario - Azure POC",
    page_icon="⏱️",
    layout="wide",
)

st.title("⏱️ Sistema Serverless de Control Horario y Auditoría")
st.caption(f"Conectado a Azure Container Apps: `{API_BASE_URL}`")

tab_checkin, tab_audit = st.tabs(
    ["📲 Terminal de Fichaje (Empleado)", "📊 Panel de Auditoría (RR. HH.)"]
)

# ==============================================================================
# PESTAÑA 1: SIMULADOR DE FICHAJE (POST /api/v1/check-in)
# ==============================================================================
with tab_checkin:
    st.subheader("Registrar evento de jornada")

    col1, col2 = st.columns(2)

    with col1:
        employee_id = st.selectbox("Empleado", options=list(MOCK_SECRETS.keys()))
        event_type = st.radio(
            "Tipo de movimiento",
            options=["CHECK_IN", "CHECK_OUT"],
            horizontal=True,
        )
        location_label = st.selectbox(
            "Ubicación GPS simulada",
            options=list(PRESET_LOCATIONS.keys()),
        )
        lat, lon = PRESET_LOCATIONS[location_label]
        st.info(f"Coordenadas seleccionadas: **Lat:** `{lat}` | **Lon:** `{lon}`")

    with col2:
        use_current_time = st.checkbox("Usar hora actual UTC", value=True)
        if use_current_time:
            event_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            custom_time = st.text_input(
                "Timestamp ISO-8601 UTC (ej. 09:05 para simular fichaje en hora)",
                value="2026-11-14T09:05:00Z",
            )
            event_ts = custom_time

        # Generación automática de código TOTP válido para facilitar pruebas
        totp_generator = pyotp.TOTP(MOCK_SECRETS[employee_id])
        auto_totp = totp_generator.now()
        totp_input = st.text_input(
            "Código TOTP (6 dígitos - autogenerado)",
            value=auto_totp,
            max_chars=6,
        )

    if st.button("Enviar fichaje a Azure", type="primary"):
        payload = {
            "employee_id": employee_id,
            "event_type": event_type,
            "timestamp": event_ts,
            "totp_code": totp_input,
            "location": {"latitude": lat, "longitude": lon},
        }

        with st.spinner("Validando TOTP y publicando evento en Azure Storage Queue..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/check-in",
                    json=payload,
                    timeout=15,
                )
                if response.status_code == 202:
                    data = response.json()
                    st.success(
                        f"Fichaje aceptado (HTTP 202). ID en cola: `{data['message_id']}`"
                    )
                    st.json(data)
                else:
                    st.error(f"Error HTTP {response.status_code}: {response.text}")
            except requests.RequestException as exc:
                st.error(f"Error de conexión con la API: {exc}")

# ==============================================================================
# PESTAÑA 2: AUDITORÍA DE FICHAJES (GET /api/v1/attendance/{employee_id})
# ==============================================================================
with tab_audit:
    st.subheader("Consulta de registros procesados por el Worker")

    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    with filter_col1:
        query_emp = st.text_input("ID de Empleado a auditar", value="EMP-9482")
    with filter_col2:
        only_anomalies = st.checkbox("Mostrar solo fichajes ANÓMALOS", value=False)
    with filter_col3:
        st.write("")
        st.write("")
        refresh_clicked = st.button("🔄 Actualizar datos")

    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/attendance/{query_emp.strip()}",
            params={"only_anomalies": str(only_anomalies).lower()},
            timeout=15,
        )
        if resp.status_code == 200:
            result = resp.json()
            records = result.get("records", [])

            # Métricas superiores
            total = len(records)
            anomalies_count = sum(
                1 for r in records if r.get("validation_status") == "ANOMALO"
            )
            valid_count = sum(
                1 for r in records if r.get("validation_status") == "VALIDO"
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Registros", total)
            m2.metric("Fichajes Válidos", valid_count)
            m3.metric("Anomalías Detectadas", anomalies_count)

            if records:
                df = pd.DataFrame(records)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No se encontraron registros para los filtros seleccionados.")
        else:
            st.error(f"Error HTTP {resp.status_code}: {resp.text}")
    except requests.RequestException as exc:
        st.error(f"No se pudo conectar con la API de auditoría: {exc}")