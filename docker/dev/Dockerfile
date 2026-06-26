# docker/dev/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=dev
ENV DJANGO_SETTINGS_MODULE=config.settings.dev
ENV DEBUG=True

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ ./requirements/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/dev.txt

COPY . .

RUN mkdir -p /app/logs /app/staticfiles /app/media

COPY docker/dev/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 4 --timeout 120"]
