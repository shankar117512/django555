#!/bin/bash
# scripts/restore-db.sh — dev only
# Usage: ./scripts/restore-db.sh <backup_file>

set -e

BACKUP_FILE="${1}"
ENVIRONMENT="dev"
DB_NAME="django_dev"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="logs/restore.log"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /var/backups/django/dev_django_dev_20260619_173822.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

source envs/.env.dev

DB_USER=$(echo "$DATABASE_URL" | sed 's|postgres://||' | cut -d: -f1)
DB_PASS=$(echo "$DATABASE_URL" | cut -d: -f3 | cut -d@ -f1)
DB_HOST=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f2 | cut -d/ -f1)

echo "[$TIMESTAMP] RESTORE started: $BACKUP_FILE → $ENVIRONMENT" >> "$LOG_FILE"

echo "Creating pre-restore safety backup..."
SAFETY_BACKUP="logs/pre_restore_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql.gz"
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom | gzip > "$SAFETY_BACKUP"
echo "Safety backup: $SAFETY_BACKUP"

echo "Dropping existing database connections..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME';"

echo "Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASS" pg_restore \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --no-acl --no-owner --clean --if-exists

echo "✅ Restore complete."
echo "[$TIMESTAMP] RESTORE SUCCESS: $BACKUP_FILE → $ENVIRONMENT" >> "$LOG_FILE"

echo "Running Django migrations..."
ENVIRONMENT="$ENVIRONMENT" python manage.py migrate --noinput
echo "Restore and migration complete."
