# 🚀 Azure Serverless Workforce PoC: Arquitectura B2B de Control de Presencia y Geolocalización

Este repositorio contiene una Prueba de Concepto (PoC) de grado de producción para un ecosistema de **Microservicios Híbridos Orientados a Eventos**. 

El proyecto resuelve un problema real en las operaciones de Recursos Humanos: la gestión del fichaje, la validación de geolocalización y el control de asistencia para plantillas distribuidas, mitigando el fraude (spoofing), garantizando la trazabilidad legal y permitiendo a los supervisores reaccionar en tiempo real a las anomalías del servicio.

## 🧠 El Enfoque Arquitectónico (Engineering Mindset)

A diferencia de los monolitos tradicionales, este sistema aplica principios de Ingeniería de Fiabilidad (SRE) y un diseño 100% desacoplado para asegurar que la ingesta de datos nunca bloquee la operativa del negocio, manteniendo los costes de infraestructura optimizados en **Microsoft Azure**.

### Reglas de Diseño Implementadas:
1. **Desacoplamiento mediante Colas:** El dispositivo móvil nunca espera a la validación de la base de datos. La ingesta y el procesamiento están separados por colas de mensajes.
2. **Agnosticismo de Entrada & Seguridad Anti-Spoofing:** Soporte para validación GPS (trabajadores móviles) y códigos TOTP dinámicos generados en tablets de los centros de trabajo (prevención de fraude en trabajadores fijos).
3. **Optimización de Costes (Serverless):** Uso estratégico de *Azure Container Apps* con controles de réplicas (`min_replicas = 1`, `max_replicas = 3`) para evitar tiempos de arranque en frío (*Cold Start*) sin incurrir en facturación descontrolada por autoescalado infinito.
4. **Infraestructura Inmutable:** Todo el entorno se provisiona exclusivamente a través de **Terraform** con un estado remoto seguro.

---

## 🏗️ Topología del Sistema (Las 3 Fases)

El ecosistema se divide lógicamente en tres componentes independientes:

### 1️⃣ Fase 1: Perímetro de Ingesta (API)
- **Tecnología:** Python (FastAPI) en Azure Container Apps.
- **Función:** Actúa como *Router* ultrarrápido. Recibe el *payload* del empleado (ID, GPS/TOTP, Timestamp), verifica de forma ligera contra una caché de asignaciones y empuja el evento crudo a una **Azure Storage Queue**. Tiempo de respuesta < 100ms.

### 2️⃣ Fase 2: El Cerebro Asíncrono (Worker)
- **Tecnología:** Python (Proceso Worker).
- **Función:** Consume los mensajes de la cola en segundo plano. Aplica lógica de negocio compleja (ej. tolerancia de desviación de reloj, validación de cuadrantes, análisis de retrasos) y persiste el resultado definitivo de forma inmutable en **Azure Table Storage**.

### 3️⃣ Fase 3: Panel de Operaciones (Supervisor UI)
- **Tecnología:** Python (Streamlit / HTML-Jinja).
- **Función:** Interfaz B2B para mandos intermedios. Permite monitorizar ausencias en tiempo real, aprobar fichajes anómalos, generar fichajes delegados por fallos en los dispositivos de los operarios, y reasignar destinos dinámicamente.

---

## 🛠️ Stack Tecnológico

*   **Lenguaje:** Python 3.11+
*   **Frameworks:** FastAPI, Streamlit.
*   **Contenerización:** Docker (Imágenes ligeras *slim*).
*   **Infraestructura como Código (IaC):** Terraform (Azure Provider).
*   **Automatización CI/CD:** GitHub Actions.
*   **Nube (Microsoft Azure):**
    *   *Azure Container Apps* (Orquestación Serverless).
    *   *Azure Container Registry* (ACR).
    *   *Azure Storage Account* (Queues & Tables para persistencia de bajo coste).

---

## 📂 Estructura del Repositorio

```text
azure-serverless-workforce-poc/
├── .github/workflows/       # Pipelines de CI/CD (Construcción y Despliegue)
├── infrastructure/          # Código Terraform para aprovisionar Azure
│   ├── modules/             # (Opcional) Módulos reutilizables
│   ├── main.tf              # Orquestación de IaC
│   ├── variables.tf         # Variables de entorno
│   └── backend.tf           # Configuración del estado remoto en Azure Blob
└── src/                     # Código fuente de la aplicación
    ├── api_ingestion/       # Código FastAPI y Dockerfile (Fase 1)
    ├── async_worker/        # Código del procesador de colas (Fase