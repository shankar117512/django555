#!/bin/bash
# docker/staging/entrypoint.sh
set -e

echo "==> [STAGING ENTRYPOINT] Environment: $ENVIRONMENT"

# Wait for PostgreSQL
python << 'PYTHON'
import time, psycopg2, os, dj_database_url
db = dj_database_url.parse(os.environ["DATABASE_URL"])
for i in range(30):
    try:
        c = psycopg2.connect(
            host=db["HOST"], port=db["PORT"],
            user=db["USER"], password=db["PASSWORD"], dbname=db["NAME"]
        )
        c.close()
        print("DB ready.")
        break
    except Exception as e:
        print(f"DB not ready ({i+1}/30), retrying in 2s...", e)
        time.sleep(2)
else:
    print("ERROR: DB never became ready.")
    exit(1)
PYTHON

echo "==> Running shared schema migrations"
python manage.py migrate_schemas --shared --noinput

echo "==> Running tenant schema migrations"
python manage.py migrate_schemas --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Ensuring public tenant exists"
python manage.py shell -c "
from products.models import Client, Domain
import os

hostname = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')

if not Client.objects.filter(schema_name='public').exists():
    t = Client(schema_name='public', name='Public Tenant', paid_until='2099-12-31', on_trial=False)
    t.save(verbosity=0)
    d = Domain(domain=hostname, tenant=t, is_primary=True)
    d.save()
    print(f'Public tenant created for {hostname}')
else:
    print('Public tenant already exists')
"

# Determine the command to run
if [ "$#" -gt 0 ]; then
    CMD="$@"
else
    CMD="gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile - --error-logfile -"
fi

echo "==> Starting server in background for health check: $CMD"
$CMD &
GUNICORN_PID=$!

echo "==> Testing health endpoint"
for i in $(seq 1 10); do
    if curl -sf http://localhost:${PORT:-8000}/health/; then
        echo "Health check passed"
        break
    fi
    echo "Waiting for server... ($i/10)"
    sleep 2
done

# Hand off — wait for gunicorn to exit (keeps container alive)
wait $GUNICORN_PID
