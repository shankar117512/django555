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
    # Update domain if it changed (e.g. new Railway deployment URL)
    from products.models import Domain
    t = Client.objects.get(schema_name='public')
    d = Domain.objects.filter(tenant=t, is_primary=True).first()
    if d and d.domain != hostname:
        d.domain = hostname
        d.save()
        print(f'Public tenant domain updated to {hostname}')
    else:
        print('Public tenant already exists')
"

# Determine the command to run
APP_PORT="${PORT:-8000}"

if [ "$#" -gt 0 ]; then
    CMD=("$@")
else
    CMD=(
        gunicorn config.wsgi:application
        --bind "0.0.0.0:${APP_PORT}"
        --workers 2
        --timeout 120
        --access-logfile -
        --error-logfile -
    )
fi

echo "==> Starting server: ${CMD[*]}"

# Start in background only to run the health check, then exec to make it PID 1
"${CMD[@]}" &
GUNICORN_PID=$!

echo "==> Testing health endpoint on port ${APP_PORT}"
HEALTH_OK=0
for i in $(seq 1 15); do
    if curl -sf "http://localhost:${APP_PORT}/health/" > /dev/null 2>&1; then
        echo "==> Health check passed on attempt $i"
        HEALTH_OK=1
        break
    fi
    echo "Waiting for server... ($i/15)"
    sleep 2
done

if [ "$HEALTH_OK" -eq 0 ]; then
    echo "ERROR: Health check never passed. Aborting."
    kill "$GUNICORN_PID" 2>/dev/null || true
    exit 1
fi

# Hand off: wait for gunicorn (keeps container alive, propagates exit code)
wait "$GUNICORN_PID"
