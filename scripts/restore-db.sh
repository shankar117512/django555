#!/bin/bash
# scripts/restore-db.sh — production only
# Usage: ./scripts/restore-db.sh [/path/to/backup.dump|.sql|.sql.gz]
#   If no path is given, prefers $BACKUP_DIR/production_backup.dump,
#   falling back to the most recent timestamped archive.

set -e
set -o pipefail

ENVIRONMENT="production"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/django}"
ARCHIVE_DIR="$BACKUP_DIR/archive"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/restore.log"

# ── Load env ──────────────────────────────────────────────────────────────────
ENV_FILE=".env.production"

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
    if [[ -f "$BACKUP_DIR/production_backup.dump" ]]; then
        echo "No backup file specified — using $BACKUP_DIR/production_backup.dump ..."
        BACKUP_FILE="$BACKUP_DIR/production_backup.dump"
    else
        echo "No backup file specified and no production_backup.dump found —"
        echo "falling back to most recent archive in $ARCHIVE_DIR ..."
        BACKUP_FILE=$(ls -t "$ARCHIVE_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | head -n 1 || true)
        if [[ -z "$BACKUP_FILE" ]]; then
            echo "ERROR: No backup files found (checked $BACKUP_DIR/production_backup.dump and $ARCHIVE_DIR)"
            exit 1
        fi
    fi
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Using backup file: $BACKUP_FILE"

# ── Detect backup format ──────────────────────────────────────────────────────
# .dump         -> pg_dump custom format -> restore with pg_restore
# .sql.gz       -> gzip-compressed plain SQL -> gunzip | psql
# .sql          -> plain SQL -> psql
case "$BACKUP_FILE" in
    *.dump)
        FORMAT="custom"
        ;;
    *.sql.gz)
        FORMAT="plain_gz"
        if ! file "$BACKUP_FILE" | grep -q "gzip"; then
            echo "ERROR: $BACKUP_FILE does not appear to be a gzip-compressed file."
            exit 1
        fi
        ;;
    *.sql)
        FORMAT="plain"
        ;;
    *)
        # Fall back to content sniffing
        if file "$BACKUP_FILE" | grep -qi "PostgreSQL custom database dump"; then
            FORMAT="custom"
        elif file "$BACKUP_FILE" | grep -q "gzip"; then
            FORMAT="plain_gz"
        else
            FORMAT="plain"
        fi
        ;;
esac
echo "Detected format: $FORMAT"

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
echo "   Restoring from: $BACKUP_FILE (format: $FORMAT)"
echo ""
read -r -p "Type 'yes' to continue, anything else to abort: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

# ── Drop & recreate database ──────────────────────────────────────────────────
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
echo "[$TIMESTAMP] Restore started — $ENVIRONMENT — $DB_NAME — file: $BACKUP_FILE (format: $FORMAT)" >> "$LOG_FILE"

case "$FORMAT" in
    custom)
        PGPASSWORD="$DB_PASS" pg_restore \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-acl \
            "$BACKUP_FILE"
        ;;
    plain_gz)
        gunzip -c "$BACKUP_FILE" \
            | PGPASSWORD="$DB_PASS" psql \
                -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                --single-transaction \
                -v ON_ERROR_STOP=1
        ;;
    plain)
        PGPASSWORD="$DB_PASS" psql \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --single-transaction \
            -v ON_ERROR_STOP=1 \
            -f "$BACKUP_FILE"
        ;;
esac

echo "✅ Restore complete: $DB_NAME"
echo "[$TIMESTAMP] Restore SUCCESS: $DB_NAME from $BACKUP_FILE" >> "$LOG_FILE"
