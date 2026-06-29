#!/bin/bash
# scripts/restore-db.sh — staging only
# Usage: ./scripts/restore-db.sh [/path/to/backup.sql.gz]
#   If no path is given, the most recent backup in BACKUP_DIR is used.

set -e
set -o pipefail

ENVIRONMENT="staging"
BACKUP_DIR="/var/backups/django"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/restore.log"

# ── Load env ──────────────────────────────────────────────────────────────────
ENV_FILE=".env.staging"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found."
    exit 1
fi

source "$ENV_FILE"

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL not found in $ENV_FILE"
    exit 1
fi

mkdir -p "$(dirname "$LOG_FILE")"

# ── Resolve backup file ───────────────────────────────────────────────────────
if [[ -n "${1:-}" ]]; then
    BACKUP_FILE="$1"
else
    echo "No backup file specified — using most recent backup in $BACKUP_DIR ..."
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | head -n 1 || true)
    if [[ -z "$BACKUP_FILE" ]]; then
        echo "ERROR: No backup files found in $BACKUP_DIR matching ${ENVIRONMENT}_*.sql.gz"
        exit 1
    fi
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Using backup file: $BACKUP_FILE"

# ── Validate it looks like a gzip file ───────────────────────────────────────
if ! file "$BACKUP_FILE" | grep -q "gzip"; then
    echo "ERROR: $BACKUP_FILE does not appear to be a gzip-compressed file."
    exit 1
fi

# ── Parse DATABASE_URL (handles both postgres:// and postgresql://) ───────────
eval "$(python3 -c "
from urllib.parse import urlparse
u = urlparse('$DATABASE_URL')
print('DB_USER=' + (u.username or ''))
print('DB_PASS=' + (u.password or ''))
print('DB_HOST=' + (u.hostname or ''))
print('DB_PORT=' + str(u.port or 5432))
print('DB_NAME=' + u.path.lstrip('/'))
")"

# ── Sanity-check parsed values ────────────────────────────────────────────────
if [ -z "$DB_USER" ] || [ -z "$DB_HOST" ] || [ -z "$DB_PASS" ] || [ -z "$DB_NAME" ]; then
    echo "ERROR: Could not parse DATABASE_URL. Got:"
    echo "  USER=$DB_USER  HOST=$DB_HOST  PORT=$DB_PORT  DB=$DB_NAME"
    echo "  Check the format: postgresql://user:pass@host:port/dbname"
    exit 1
fi

echo "Parsed connection → user=$DB_USER  host=$DB_HOST  port=$DB_PORT  db=$DB_NAME"

# ── Test connection ───────────────────────────────────────────────────────────
echo "Testing DB connection..."
if ! PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT 1;" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to $DB_NAME as $DB_USER@$DB_HOST:$DB_PORT"
    echo ""
    echo "  Troubleshooting checklist:"
    echo "  1. Is the database service running?"
    echo "  2. Is your IP whitelisted? Railway may restrict external connections."
    echo "  3. Run manually to see the real error:"
    echo "     PGPASSWORD='...' psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    exit 1
fi
echo "Connection OK."

# ── Safety prompt ─────────────────────────────────────────────────────────────
echo ""
echo "⚠️  WARNING: This will DESTROY and recreate the database '$DB_NAME' on $DB_HOST."
echo "   All existing data will be permanently lost."
echo ""
read -r -p "Type 'yes' to continue, anything else to abort: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

# ── Drop & recreate database ──────────────────────────────────────────────────
# Connect to the default 'postgres' maintenance DB to drop/recreate the target DB.
echo "Dropping and recreating database '$DB_NAME'..."

PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"

PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"

echo "Database recreated."

# ── Restore from backup ───────────────────────────────────────────────────────
echo "Restoring $BACKUP_FILE → $DB_NAME ..."
echo "[$TIMESTAMP] Restore started — $ENVIRONMENT — $DB_NAME — file: $BACKUP_FILE" >> "$LOG_FILE"

gunzip -c "$BACKUP_FILE" \
    | PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --single-transaction \
        -v ON_ERROR_STOP=1

echo "✅ Restore complete: $DB_NAME"
echo "[$TIMESTAMP] Restore SUCCESS: $DB_NAME from $BACKUP_FILE" >> "$LOG_FILE"
