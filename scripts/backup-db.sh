#!/bin/bash
# scripts/backup-db.sh
# Creates compressed PostgreSQL backup (.sql.gz)

set -euo pipefail

ENVIRONMENT="dev"
BACKUP_DIR="/var/backups/django"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/backup.log"

#############################################
# Load Environment Variables
#############################################

ENV_FILE=".env.dev"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found."
    exit 1
fi

source "$ENV_FILE"

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL not found in $ENV_FILE"
    exit 1
fi

#############################################
# Parse DATABASE_URL
#############################################

URL="${DATABASE_URL#postgres://}"

DB_USER="${URL%%:*}"
URL="${URL#*:}"

DB_PASS="${URL%%@*}"
URL="${URL#*@}"

DB_HOST="${URL%%:*}"
URL="${URL#*:}"

DB_PORT="${URL%%/*}"
DB_NAME="${URL#*/}"

#############################################
# Validate
#############################################

if [[ -z "$DB_USER" || -z "$DB_PASS" || -z "$DB_HOST" || -z "$DB_PORT" || -z "$DB_NAME" ]]; then
    echo "ERROR: Failed to parse DATABASE_URL"
    exit 1
fi

#############################################
# Check pg_dump
#############################################

if ! command -v pg_dump >/dev/null 2>&1; then
    echo "ERROR: pg_dump not installed."
    exit 1
fi

#############################################
# Check Database Exists
#############################################

if ! PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -lqt \
    2>/dev/null \
    | cut -d '|' -f1 \
    | grep -qw "$DB_NAME"; then

    echo "ERROR: Database \"$DB_NAME\" does not exist."
    exit 1
fi

#############################################
# Create Backup Folder
#############################################

mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

BACKUP_FILE="$BACKUP_DIR/${ENVIRONMENT}_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backing up $DB_NAME..."
echo "Destination: $BACKUP_FILE"

echo "[$TIMESTAMP] Backup Started" >> "$LOG_FILE"

#############################################
# Backup
#############################################

PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    | gzip > "$BACKUP_FILE"

#############################################
# Verify Backup
#############################################

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup failed."
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "Backup completed successfully."
echo "File: $BACKUP_FILE"
echo "Size: $SIZE"

echo "[$TIMESTAMP] SUCCESS ($SIZE)" >> "$LOG_FILE"

#############################################
# Keep Last 30 Backups
#############################################

echo "Removing old backups..."

ls -tp "$BACKUP_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null \
    | tail -n +31 \
    | xargs -r rm --

echo "Backup rotation completed."

echo "Done."
