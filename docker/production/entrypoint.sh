#!/bin/bash
# docker/production/entrypoint.sh
set -e

echo "==> [ENTRYPOINT] Environment: $ENVIRONMENT"
echo "==> [ENTRYPOINT] Settings: $DJANGO_SETTINGS_MODULE"

echo "==> [ENTRYPOINT] Waiting for PostgreSQL..."
python << 'PYTHON'
import time
import psycopg2
import os
import dj_database_url

db_config = dj_database_url.parse(os.environ["DATABASE_URL"])
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(
            host=db_config["HOST"],
            port=db_config["PORT"],
            user=db_config["USER"],
            password=db_config["PASSWORD"],
            dbname=db_config["NAME"],
        )
        conn.close()
        print("PostgreSQL is ready.")
        break
    except psycopg2.OperationalError as e:
        print(f"Attempt {i+1}/{max_retries}: PostgreSQL not ready. Retrying in 2s...")
        time.sleep(2)
else:
    print("ERROR: PostgreSQL did not become ready.")
    exit(1)
PYTHON

echo "==> [ENTRYPOINT] Running shared schema migrations..."
python manage.py migrate_schemas --shared --noinput

echo "==> [ENTRYPOINT] Ensuring public tenant + domain exist..."
python manage.py create_public_tenant

echo "==> [ENTRYPOINT] Running tenant schema migrations..."
python manage.py migrate_schemas --noinput

echo "==> [ENTRYPOINT] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> [ENTRYPOINT] Checking superuser..."
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@yourapp.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
PYEOF

echo "==> [ENTRYPOINT] Starting application..."
exec "$@"
