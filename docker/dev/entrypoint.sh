# docker/dev/entrypoint.sh
#!/bin/bash
set -e

echo "==> [DEV ENTRYPOINT] Starting..."

# Wait for DB
echo "==> Waiting for DB..."
while ! pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-devuser}" 2>/dev/null; do
    echo "DB not ready, waiting..."
    sleep 2
done
echo "==> DB ready."

# Run migrations
python manage.py migrate --noinput

# Load fixtures if present
if [ -f "fixtures/dev_data.json" ]; then
    python manage.py loaddata fixtures/dev_data.json
fi

echo "==> Dev server starting..."
exec "$@"
