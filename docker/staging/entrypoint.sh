#!/bin/bash
# docker/staging/entrypoint.sh
set -e

echo "==> [STAGING ENTRYPOINT] Environment: ${ENVIRONMENT}"

# ── Wait for PostgreSQL ──────────────────────────────────────────────────────
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
        print(f"DB not ready ({i+1}/30), retrying in 2s... {e}")
        time.sleep(2)
else:
    print("ERROR: DB never became ready.")
    exit(1)
PYTHON

# ── Migrations ───────────────────────────────────────────────────────────────
echo "==> Running shared schema migrations"
python manage.py migrate_schemas --shared --noinput

echo "==> Running tenant schema migrations"
python manage.py migrate_schemas --noinput

# ── Static files ─────────────────────────────────────────────────────────────
echo "==> Collecting static files"
python manage.py collectstatic --noinput

# ── Public tenant bootstrap ──────────────────────────────────────────────────
echo "==> Ensuring public tenant exists"
python manage.py shell -c "
from products.models import Client, Domain
import os

hostname = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')

if not Client.objects.filter(schema_name='public').exists():
    t = Client(
        schema_name='public',
        name='Public Tenant',
        paid_until='2099-12-31',
        on_trial=False
    )
    t.save(verbosity=0)
    d = Domain(domain=hostname, tenant=t, is_primary=True)
    d.save()
    print(f'Public tenant created for {hostname}')
else:
    t = Client.objects.get(schema_name='public')
    d = Domain.objects.filter(tenant=t, is_primary=True).first()
    if d and d.domain != hostname:
        d.domain = hostname
        d.save()
        print(f'Public tenant domain updated to {hostname}')
    else:
        print('Public tenant already exists')
"

# ── Start server ─────────────────────────────────────────────────────────────
APP_PORT="${PORT:-8000}"

if [ "$#" -gt 0 ]; then
    # Allow overriding the command (e.g. for celery workers)
    echo "==> Running custom command: $*"
    exec "$@"
else
    echo "==> Starting gunicorn on 0.0.0.0:${APP_PORT}"
    exec gunicorn config.wsgi:application \
        --bind "0.0.0.0:${APP_PORT}" \
        --workers 2 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi
