#!/bin/bash
# scripts/backup-db-staging.sh — staging only
# Usage: ./scripts/backup-db-staging.sh

set -e

ENVIRONMENT="staging"
DB_NAME="django_staging"
BACKUP_DIR="/var/backups/django"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/backup.log"

source envs/.env.staging

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${ENVIRONMENT}_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backing up $DB_NAME → $BACKUP_FILE"
echo "[$TIMESTAMP] Backup started — $ENVIRONMENT — $DB_NAME" >> "$LOG_FILE"

DB_USER=$(echo "$DATABASE_URL" | sed 's|postgres://||' | cut -d: -f1)
DB_PASS=$(echo "$DATABASE_URL" | cut -d: -f3 | cut -d@ -f1)
DB_HOST=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f2 | cut -d/ -f1)

PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --no-acl --no-owner --format=custom \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"
echo "[$TIMESTAMP] Backup SUCCESS: $BACKUP_FILE ($BACKUP_SIZE)" >> "$LOG_FILE"

echo "Cleaning old backups (keeping last 30)..."
ls -t "$BACKUP_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
