# docker/staging/entrypoint.sh
#!/bin/bash
set -e

echo "==> [STAGING ENTRYPOINT] Environment: $ENVIRONMENT"

# Wait for PostgreSQL
python << 'PYTHON'
import time, psycopg2, os, dj_database_url
db = dj_database_url.parse(os.environ["DATABASE_URL"])
for i in range(30):
    try:
        c = psycopg2.connect(
            host=db["HOST"],
            port=db["PORT"],
            user=db["USER"],
            password=db["PASSWORD"],
            dbname=db["NAME"]
        )
        c.close()
        break
    except Exception as e:
        print("DB not ready, retrying...", e)
        time.sleep(2)
PYTHON

echo "==> Running migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8001} \
  --workers ${WEB_CONCURRENCY:-2} \
  --timeout 120
