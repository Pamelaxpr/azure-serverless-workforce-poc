# 1. Imagen base oficial de Python (versión slim para que pese menos)
FROM python:3.11-slim

# 2. Optimizaciones de Python en contenedores
# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1 
# Fuerza a que el output de consola vaya directo a la terminal (útil para ver los logs en Azure)
ENV PYTHONUNBUFFERED=1

# 3. Definimos la carpeta de trabajo dentro del contenedor
WORKDIR /app

# 4. SEGURIDAD: Creamos un usuario de sistema sin privilegios de root
RUN addgroup --system appgroup && adduser --system --group appuser

# 5. CACHÉ: Copiamos solo los requirements primero
COPY requirements.txt .

# 6. Instalamos las dependencias sin guardar la caché del instalador (pip) para ahorrar espacio
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copiamos el resto del código fuente a la carpeta /app
COPY . .

# 8. SEGURIDAD: Entregamos la propiedad de los archivos al usuario no-root
RUN chown -R appuser:appgroup /app

# 9. SEGURIDAD: Le decimos a Docker que ejecute todo lo siguiente como este usuario
USER appuser

# 10. Exponemos el puerto de red
EXPOSE 8000

# 11. El comando definitivo que arranca el servidor (0.0.0.0 permite que Azure enrute el tráfico)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]