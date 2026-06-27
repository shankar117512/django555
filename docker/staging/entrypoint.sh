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

tenant, tenant_created = Client.objects.get_or_create(
    schema_name='public',
    defaults={
        'name': 'Public Tenant',
        'paid_until': '2099-12-31',
        'on_trial': False,
    }
)
if tenant_created:
    print(f'Public tenant created.')
else:
    print(f'Public tenant already exists.')

domain, domain_created = Domain.objects.update_or_create(
    domain=hostname,
    defaults={'tenant': tenant, 'is_primary': True},
)
if domain_created:
    print(f'Primary domain created: {hostname}')
else:
    print(f'Primary domain updated/confirmed: {domain.domain}')
"

# ── Start server ─────────────────────────────────────────────────────────────
APP_PORT="${PORT:-8080}"

if [ "$#" -gt 0 ]; then
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
