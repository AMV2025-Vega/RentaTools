# Utilizar una imagen oficial liviana de Python
FROM python:3.12-slim

# Establecer directorio de trabajo en el contenedor
WORKDIR /app

# Evitar la creación de archivos .pyc y forzar stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema mínimas si fueran requeridas (opcional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias primero (aprovechando caché de capas de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del microservicio
COPY . .

# Exponer el puerto 5000
EXPOSE 5000

# invocamos la fábrica de Flask directamente
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]