# ============================================================
# Terminal Terrestre — Dockerfile (backend)
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente
COPY . .

# Variables de entorno por defecto (sobrescribir en .env)
ENV DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Puerto de Waitress
EXPOSE 8000

CMD ["python", "-m", "waitress", "--host=0.0.0.0", "--port=8000", "config.wsgi:application"]
