#!/bin/bash
# scripts/backup-db.sh — production only
# Usage: ./scripts/backup-db.sh
#
# Produces on every run:
#   $BACKUP_DIR/production_backup.dump   -> pg_dump custom format (for pg_restore)
#   $BACKUP_DIR/production_backup.sql    -> pg_dump plain SQL format (for psql / diffing)
#   $BACKUP_DIR/archive/<env>_<db>_<ts>.sql.gz  -> timestamped, rotated history (last 30)
#   $BACKUP_DIR/deployments.json         -> append-only JSON log of every backup run

set -e
set -o pipefail

ENVIRONMENT="production"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/django}"
ARCHIVE_DIR="$BACKUP_DIR/archive"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/backup.log"
DEPLOYMENTS_FILE="$BACKUP_DIR/deployments.json"

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

mkdir -p "$BACKUP_DIR"
mkdir -p "$ARCHIVE_DIR"
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

CLIENT_VERSION=$(pg_dump --version | awk '{print $3}')
echo "Client pg_dump version:    $CLIENT_VERSION"

# ── Test connection before dumping ────────────────────────────────────────────
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

# ── Run backups ────────────────────────────────────────────────────────────────
DUMP_FILE="$BACKUP_DIR/production_backup.dump"
SQL_FILE="$BACKUP_DIR/production_backup.sql"
ARCHIVE_FILE="$ARCHIVE_DIR/${ENVIRONMENT}_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[$TIMESTAMP] Backup started — $ENVIRONMENT — $DB_NAME" >> "$LOG_FILE"

echo "Creating custom-format dump (for pg_restore) → $DUMP_FILE"
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-acl --no-owner --format=custom \
    --file="$DUMP_FILE"

echo "Creating plain-SQL dump → $SQL_FILE"
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-acl --no-owner --format=plain \
    | grep -v "^SET transaction_timeout" > "$SQL_FILE"

echo "Writing timestamped archive copy → $ARCHIVE_FILE"
gzip -c "$SQL_FILE" > "$ARCHIVE_FILE"

# ── Validate none of the backup files are empty ───────────────────────────────
for f in "$DUMP_FILE" "$SQL_FILE" "$ARCHIVE_FILE"; do
    if [ ! -s "$f" ]; then
        echo "ERROR: Backup file is empty — something went wrong: $f"
        echo "[$TIMESTAMP] Backup FAILED: $f empty" >> "$LOG_FILE"
        exit 1
    fi
done

DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
SQL_SIZE=$(du -h "$SQL_FILE" | cut -f1)
DUMP_SHA=$(sha256sum "$DUMP_FILE" | awk '{print $1}')
SQL_SHA=$(sha256sum "$SQL_FILE" | awk '{print $1}')

GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
DJANGO_VERSION=$(python3 -c "import django; print(django.get_version())" 2>/dev/null || echo "unknown")

echo "✅ Backup complete:"
echo "   dump: $DUMP_FILE ($DUMP_SIZE)"
echo "   sql:  $SQL_FILE ($SQL_SIZE)"
echo "[$TIMESTAMP] Backup SUCCESS: dump=$DUMP_FILE ($DUMP_SIZE) sql=$SQL_FILE ($SQL_SIZE)" >> "$LOG_FILE"

# ── Record this run in deployments.json (append-only, no secrets included) ────
export DEPLOYMENTS_FILE TIMESTAMP ENVIRONMENT DB_NAME DB_HOST DB_PORT DB_USER \
       DUMP_FILE SQL_FILE ARCHIVE_FILE DUMP_SIZE SQL_SIZE DUMP_SHA SQL_SHA \
       SERVER_VERSION CLIENT_VERSION GIT_COMMIT DJANGO_VERSION

python3 <<'PYEOF'
import json, os, datetime

path = os.environ["DEPLOYMENTS_FILE"]

entry = {
    "timestamp": os.environ["TIMESTAMP"],
    "datetime_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "environment": os.environ["ENVIRONMENT"],
    "database": {
        "name": os.environ["DB_NAME"],
        "host": os.environ["DB_HOST"],
        "port": os.environ["DB_PORT"],
        "user": os.environ["DB_USER"],
    },
    "files": {
        "dump": {
            "path": os.environ["DUMP_FILE"],
            "size": os.environ["DUMP_SIZE"],
            "sha256": os.environ["DUMP_SHA"],
        },
        "sql": {
            "path": os.environ["SQL_FILE"],
            "size": os.environ["SQL_SIZE"],
            "sha256": os.environ["SQL_SHA"],
        },
        "archive": os.environ["ARCHIVE_FILE"],
    },
    "postgres": {
        "server_version": os.environ["SERVER_VERSION"],
        "pg_dump_version": os.environ["CLIENT_VERSION"],
    },
    "git_commit": os.environ["GIT_COMMIT"],
    "django_version": os.environ["DJANGO_VERSION"],
    "status": "success",
}

data = []
if os.path.exists(path):
    try:
        with open(path) as f:
            loaded = json.load(f)
        if isinstance(loaded, list):
            data = loaded
    except (json.JSONDecodeError, ValueError):
        data = []

data.append(entry)
data = data[-100:]  # keep the last 100 deployment/backup records

tmp_path = path + ".tmp"
with open(tmp_path, "w") as f:
    json.dump(data, f, indent=2)
os.replace(tmp_path, path)

print(f"Recorded deployment entry in {path} ({len(data)} total records)")
PYEOF

# ── Rotate old timestamped archives (keep last 30) ────────────────────────────
echo "Cleaning old archives (keeping last 30)..."
ls -t "$ARCHIVE_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
echo "Done."
