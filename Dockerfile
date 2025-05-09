# Etapa 1: construir entorno
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalar
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código
COPY . /app/

# Comando para ejecutar el servidor
CMD ["gunicorn", "DjangoProject.wsgi:application", "--bind", "0.0.0.0:8000"]
