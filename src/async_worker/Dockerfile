# 1. Imagen base oficial de Python (ligera)
FROM python:3.11-slim

# 2. Evita archivos .pyc y fuerza la salida directa de logs hacia Azure Log Analytics
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo
WORKDIR /app

# 4. Usuario de sistema sin privilegios de root
RUN addgroup --system appgroup && adduser --system --group appuser

# 5. Instalación de dependencias aprovechando la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia del código fuente y asignación de permisos
COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

# 7. Arranque directo del consumidor asíncrono
CMD ["python", "worker.py"]