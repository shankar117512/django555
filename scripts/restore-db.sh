#!/bin/bash
# scripts/restore-db.sh — staging only
# Usage: ./scripts/restore-db.sh <backup_file>

set -e

BACKUP_FILE="${1}"
ENVIRONMENT="staging"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="logs/restore.log"

# ── Validate arguments ────────────────────────────────────────────────────────
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /var/backups/django/staging_django_staging_20260628_000651.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# ── Load env ──────────────────────────────────────────────────────────────────
source envs/.env.staging
mkdir -p "$(dirname "$LOG_FILE")"

# ── Validate DATABASE_URL ─────────────────────────────────────────────────────
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set in envs/.env.staging"
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

# ── Detect server version ─────────────────────────────────────────────────────
SERVER_VERSION=$(PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -tAc "SHOW server_version;" 2>/dev/null || echo "unknown")
echo "Server PostgreSQL version: $SERVER_VERSION"

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

# ── Peek inside the backup to detect dump-time client version ────────────────
DUMP_CLIENT_VER=$(gunzip -c "$BACKUP_FILE" 2>/dev/null | head -20 \
    | grep "^-- Dumped by pg_dump" | grep -oP '\d+\.\d+' | head -1 || echo "unknown")
echo "Backup was created by pg_dump: $DUMP_CLIENT_VER"

# ── Confirm before destructive restore ───────────────────────────────────────
echo ""
echo "⚠️  WARNING: This will OVERWRITE all data in '$DB_NAME' on $ENVIRONMENT."
echo "   Host:        $DB_HOST:$DB_PORT"
echo "   Backup file: $BACKUP_FILE"
echo ""
read -r -p "   Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "[$TIMESTAMP] RESTORE started: $BACKUP_FILE → $ENVIRONMENT ($DB_NAME)" >> "$LOG_FILE"

# ── Pre-restore safety backup ─────────────────────────────────────────────────
echo "Creating pre-restore safety backup..."
mkdir -p logs
SAFETY_BACKUP="logs/pre_restore_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql.gz"
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-acl --no-owner --format=plain \
    | grep -v "^SET transaction_timeout" \
    | gzip > "$SAFETY_BACKUP"
echo "Safety backup saved: $SAFETY_BACKUP"

# ── Terminate active connections ──────────────────────────────────────────────
echo "Dropping existing database connections..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -c "SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '$DB_NAME'
          AND pid <> pg_backend_pid();" > /dev/null

# ── Drop and recreate public schema (clean slate) ────────────────────────────
echo "Dropping public schema and recreating (clean slate)..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# ── Restore — strip lines that only newer PostgreSQL servers understand ───────
# Specifically: SET transaction_timeout was introduced in PG17/18.
# Piping through grep -v removes those lines before psql sees them,
# making dumps from pg_dump 17/18 safely restorable onto PG16 servers.
echo "Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" \
    | grep -v "^SET transaction_timeout" \
    | PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --single-transaction \
        -v ON_ERROR_STOP=1

echo "✅ Restore complete."
echo "[$TIMESTAMP] RESTORE SUCCESS: $BACKUP_FILE → $ENVIRONMENT ($DB_NAME)" >> "$LOG_FILE"
