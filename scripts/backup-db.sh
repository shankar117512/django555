#!/bin/bash
# scripts/backup-db.sh — staging only
# Usage: ./scripts/backup-db.sh

set -e
set -o pipefail

ENVIRONMENT="staging"
BACKUP_DIR="/var/backups/django"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/backup.log"

# ── Load env ─────────────────────────────────────────────────────────────────
source envs/.env.staging
mkdir -p "$BACKUP_DIR"
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

# ── Test connection before dumping ────────────────────────────────────────────
echo "Testing DB connection..."
if ! PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT 1;" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to $DB_NAME as $DB_USER@$DB_HOST:$DB_PORT"
    echo ""
    echo "  Troubleshooting checklist:"
    echo "  1. Is the Railway database service running? (check Railway dashboard)"
    echo "  2. Is your IP whitelisted? Railway may restrict external connections."
    echo "  3. Run manually to see the real error:"
    echo "     PGPASSWORD='$DB_PASS' psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    exit 1
fi
echo "Connection OK."

# ── Run backup (plain SQL so restore is straightforward) ──────────────────────
# Using --format=plain so the .sql.gz can be restored with psql, not pg_restore
BACKUP_FILE="$BACKUP_DIR/${ENVIRONMENT}_${DB_NAME}_${TIMESTAMP}.sql.gz"
echo "Backing up $DB_NAME → $BACKUP_FILE"
echo "[$TIMESTAMP] Backup started — $ENVIRONMENT — $DB_NAME" >> "$LOG_FILE"

PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-acl --no-owner --format=plain \
    | gzip > "$BACKUP_FILE"

# ── Validate the backup file isn't empty ─────────────────────────────────────
if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty — something went wrong."
    rm -f "$BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"
echo "[$TIMESTAMP] Backup SUCCESS: $BACKUP_FILE ($BACKUP_SIZE)" >> "$LOG_FILE"

# ── Rotate old backups (keep last 30) ─────────────────────────────────────────
echo "Cleaning old backups (keeping last 30)..."
ls -t "$BACKUP_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
echo "Done."
