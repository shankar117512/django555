#!/bin/bash
# scripts/restore-db.sh
# Usage: ./scripts/restore-db.sh [backup_file] [environment]

set -e

BACKUP_FILE="${1}"
ENVIRONMENT="${2:-production}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="logs/restore.log"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [environment]"
    echo "Example: $0 /var/backups/django/production_django_production_20260101_120000.sql.gz production"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# SAFETY: Require confirmation for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  WARNING: You are about to restore the PRODUCTION database!"
    echo "    This will OVERWRITE all current production data."
    read -p "Type 'RESTORE PRODUCTION' to confirm: " CONFIRM
    if [ "$CONFIRM" != "RESTORE PRODUCTION" ]; then
        echo "Restore cancelled."
        exit 0
    fi
fi

# Load env
case "$ENVIRONMENT" in
    production) source envs/.env.production; DB_NAME="django_production" ;;
    staging)    source envs/.env.staging; DB_NAME="django_staging" ;;
    dev)        source envs/.env.dev; DB_NAME="django_dev" ;;
esac

# Parse DATABASE_URL
DB_USER=$(echo "$DATABASE_URL" | sed 's|postgres://||' | cut -d: -f1)
DB_PASS=$(echo "$DATABASE_URL" | cut -d: -f3 | cut -d@ -f1)
DB_HOST=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f2 | cut -d/ -f1)

echo "[$TIMESTAMP] RESTORE started: $BACKUP_FILE → $ENVIRONMENT" >> "$LOG_FILE"

# Step 1: Create pre-restore backup
echo "Creating pre-restore safety backup..."
SAFETY_BACKUP="logs/pre_restore_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql.gz"
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom | gzip > "$SAFETY_BACKUP"
echo "Safety backup: $SAFETY_BACKUP"

# Step 2: Drop & recreate DB
echo "Dropping existing database connections..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME';"

# Step 3: Restore
echo "Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASS" pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-acl \
    --no-owner \
    --clean \
    --if-exists

echo "✅ Restore complete."
echo "[$TIMESTAMP] RESTORE SUCCESS: $BACKUP_FILE → $ENVIRONMENT" >> "$LOG_FILE"

# Step 4: Run Django migrations to ensure schema is current
echo "Running Django migrations..."
ENVIRONMENT="$ENVIRONMENT" python manage.py migrate --noinput

echo "Restore and migration complete."
