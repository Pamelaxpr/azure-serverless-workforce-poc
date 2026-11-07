from fastapi import FastAPI

app = FastAPI(title="Workforce Ingestion API")

@app.get("/health")
async def health_check():
    """
    Endpoint de diagnóstico. 
    Si Azure o un balanceador de carga llama aquí, sabrá que el contenedor está vivo.
    """
    return {"status": "ok", "service": "api_ingestion"}