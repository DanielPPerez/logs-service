# Dockerfile

# 1. Usar una imagen base oficial de Python
FROM python:3.11-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar solo el archivo de requerimientos e instalarlos
# Esto aprovecha el cache de Docker. Solo se reinstalará si requirements.txt cambia.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código de la aplicación
COPY ./src ./src
COPY main.py .

# 5. Exponer el puerto en el que FastAPI se ejecutará
EXPOSE 8000

# 6. El comando para iniciar la aplicación cuando el contenedor se ejecute
# Usamos 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]