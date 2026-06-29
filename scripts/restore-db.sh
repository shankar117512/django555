#!/bin/bash
# scripts/restore-db.sh — dev only
# Usage: ./scripts/restore-db.sh <backup_file.sql.gz>
#   e.g. ./scripts/restore-db.sh /var/backups/django/dev_django_dev_20240101_120000.sql.gz

set -e
set -o pipefail

ENVIRONMENT="dev"
BACKUP_DIR="/var/backups/django"
LOG_FILE="logs/restore.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# ── Argument check ────────────────────────────────────────────────────────────
if [[ -z "${1:-}" ]]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "  Available dev backups:"
    ls -t "$BACKUP_DIR"/dev_*.sql.gz 2>/dev/null | head -10 || echo "  (none found in $BACKUP_DIR)"
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [[ "$BACKUP_FILE" != *.sql.gz ]]; then
    echo "ERROR: Expected a .sql.gz file, got: $BACKUP_FILE"
    exit 1
fi

# ── Load env ──────────────────────────────────────────────────────────────────
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

mkdir -p "$(dirname "$LOG_FILE")"

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

# ── Detect server version ─────────────────────────────────────────────────────
SERVER_VERSION=$(PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -tAc "SHOW server_version;" 2>/dev/null || echo "unknown")
echo "Server PostgreSQL version: $SERVER_VERSION"

CLIENT_VERSION=$(psql --version | awk '{print $3}')
echo "Client psql version:       $CLIENT_VERSION"

# ── Test connection before restoring ─────────────────────────────────────────
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

# ── Safety confirmation ───────────────────────────────────────────────────────
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "⚠️  WARNING: This will DROP and recreate the '$DB_NAME' database on $ENVIRONMENT."
echo ""
echo "  Environment : $ENVIRONMENT"
echo "  Target DB   : $DB_NAME @ $DB_HOST:$DB_PORT"
echo "  Backup file : $BACKUP_FILE ($BACKUP_SIZE)"
echo ""
read -rp "Type 'yes' to continue: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

echo "[$TIMESTAMP] Restore started — $ENVIRONMENT — $DB_NAME — $BACKUP_FILE" >> "$LOG_FILE"

# ── Drop and recreate the target database ────────────────────────────────────
# Connect to the default 'postgres' maintenance DB to drop/create the target DB.
echo "Dropping existing database '$DB_NAME'..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"

echo "Creating fresh database '$DB_NAME'..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
    -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"

# ── Restore from backup ───────────────────────────────────────────────────────
echo "Restoring $BACKUP_FILE → $DB_NAME ..."
gunzip -c "$BACKUP_FILE" \
    | grep -v "^SET transaction_timeout" \
    | PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --single-transaction \
        -v ON_ERROR_STOP=1

# ── Verify restore ────────────────────────────────────────────────────────────
TABLE_COUNT=$(PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo ""
echo "✅ Restore complete."
echo "   Tables in public schema: $TABLE_COUNT"
echo "[$TIMESTAMP] Restore SUCCESS: $BACKUP_FILE → $DB_NAME (tables: $TABLE_COUNT)" >> "$LOG_FILE"
