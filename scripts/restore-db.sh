#!/bin/bash
# scripts/restore-db.sh
# Restores PostgreSQL database from a compressed backup (.sql.gz)

set -euo pipefail

ENVIRONMENT="dev"
LOG_FILE="logs/restore.log"

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
# Check Required Programs
#############################################

if ! command -v psql >/dev/null 2>&1; then
    echo "ERROR: psql not installed."
    exit 1
fi

if ! command -v gunzip >/dev/null 2>&1; then
    echo "ERROR: gunzip not installed."
    exit 1
fi

#############################################
# Check Backup File
#############################################

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "./scripts/restore-db.sh /path/to/backup.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found:"
    echo "$BACKUP_FILE"
    exit 1
fi

#############################################
# Confirmation
#############################################

echo ""
echo "==============================================="
echo "WARNING!"
echo "This will completely overwrite database:"
echo "  $DB_NAME"
echo "Host: $DB_HOST"
echo "==============================================="
echo ""

read -p "Continue? (yes/no): " ANSWER

if [[ "$ANSWER" != "yes" ]]; then
    echo "Restore cancelled."
    exit 0
fi

#############################################
# Restore
#############################################

mkdir -p "$(dirname "$LOG_FILE")"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "[$TIMESTAMP] Restore Started" >> "$LOG_FILE"

echo ""
echo "Restoring database..."
echo "Backup file: $BACKUP_FILE"

PGPASSWORD="$DB_PASS" gunzip -c "$BACKUP_FILE" | \
psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME"

echo ""
echo "Restore completed successfully."

echo "[$TIMESTAMP] SUCCESS ($BACKUP_FILE)" >> "$LOG_FILE"

echo "Done."
