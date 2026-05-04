# docker/staging/Dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements/ ./requirements/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/staging.txt

FROM python:3.12-slim AS staging

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=staging
ENV DJANGO_SETTINGS_MODULE=config.settings.staging
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

COPY --chown=appuser:appuser . .
RUN mkdir -p /app/logs /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/logs /app/staticfiles /app/media

COPY --chown=appuser:appuser docker/staging/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers 2 --timeout 120"]
