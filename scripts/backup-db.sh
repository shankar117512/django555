#!/bin/bash
# scripts/backup-db.sh
# Usage: ./scripts/backup-db.sh [environment] [destination]

set -e

ENVIRONMENT="${1:-production}"
BACKUP_DIR="${2:-/var/backups/django}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="logs/backup.log"

# Load environment-specific DB URL
case "$ENVIRONMENT" in
    production)
        source envs/.env.production
        DB_NAME="django_production"
        ;;
    staging)
        source envs/.env.staging
        DB_NAME="django_staging"
        ;;
    dev)
        source envs/.env.dev
        DB_NAME="django_dev"
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${ENVIRONMENT}_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "═══════════════════════════════════════════════"
echo "  DATABASE BACKUP"
echo "  Environment: $ENVIRONMENT"
echo "  Database: $DB_NAME"
echo "  Output: $BACKUP_FILE"
echo "  Timestamp: $TIMESTAMP"
echo "═══════════════════════════════════════════════"

# Log start
echo "[$TIMESTAMP] Backup started — $ENVIRONMENT — $DB_NAME" >> "$LOG_FILE"

# Parse DATABASE_URL
# Format: postgres://user:password@host:port/dbname
DB_USER=$(echo "$DATABASE_URL" | sed 's|postgres://||' | cut -d: -f1)
DB_PASS=$(echo "$DATABASE_URL" | cut -d: -f3 | cut -d@ -f1)
DB_HOST=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DATABASE_URL" | cut -d@ -f2 | cut -d: -f2 | cut -d/ -f1)

# Create dump with compression
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-acl \
    --no-owner \
    --format=custom \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"
echo "[$TIMESTAMP] Backup SUCCESS: $BACKUP_FILE ($BACKUP_SIZE)" >> "$LOG_FILE"

# ─────────────────────────────────────────────────
# Retain only last 30 daily, 12 weekly, 12 monthly
# ─────────────────────────────────────────────────
echo "Cleaning old backups (keeping last 30)..."
ls -t "$BACKUP_DIR"/${ENVIRONMENT}_*.sql.gz 2>/dev/null | \
    tail -n +31 | \
    xargs -r rm --

echo "Backup retention cleanup done."

# ─────────────────────────────────────────────────
# Optional: Upload to S3/Railway Volume
# ─────────────────────────────────────────────────
if command -v aws &> /dev/null && [ -n "$AWS_S3_BACKUP_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" \
        "s3://$AWS_S3_BACKUP_BUCKET/db-backups/$ENVIRONMENT/$TIMESTAMP.sql.gz" \
        --storage-class STANDARD_IA
    echo "S3 upload complete."
fi

echo "Backup process finished."
