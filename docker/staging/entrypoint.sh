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
        c = psycopg2.connect(host=db["HOST"], port=db["PORT"],
                             user=db["USER"], password=db["PASSWORD"],
                             dbname=db["NAME"])
        c.close(); break
    except: time.sleep(2)
PYTHON

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
