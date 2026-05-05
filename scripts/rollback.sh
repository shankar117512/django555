#!/bin/bash
# scripts/rollback.sh
# Usage: ./scripts/rollback.sh [environment] [deployment_id]
# Example: ./scripts/rollback.sh production

set -e

ENVIRONMENT="${1:-production}"
REASON="${2:-Manual rollback}"

echo "═══════════════════════════════════════════════"
echo "  ROLLBACK SCRIPT"
echo "  Environment: $ENVIRONMENT"
echo "  Reason: $REASON"
echo "═══════════════════════════════════════════════"

# Confirmation prompt
read -p "Are you sure you want to rollback $ENVIRONMENT? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

# Record rollback event
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] ROLLBACK initiated for $ENVIRONMENT by $USER" >> logs/rollback.log
echo "Reason: $REASON" >> logs/rollback.log

# Execute Railway rollback
echo "Executing Railway rollback..."
railway rollback \
    --environment "$ENVIRONMENT" \
    --service django-web

# Wait for rollback to complete
echo "Waiting for rollback to stabilize..."
sleep 60

# Health check after rollback
if [ "$ENVIRONMENT" = "production" ]; then
    URL="https://yourapp.com"
elif [ "$ENVIRONMENT" = "staging" ]; then
    URL="https://staging.yourapp.up.railway.app"
else
    URL="https://dev.yourapp.up.railway.app"
fi

echo "Running health check at $URL..."
if curl -f "$URL/health/" --silent --output /dev/null; then
    echo "✅ Rollback successful. Service is healthy."
    echo "[$TIMESTAMP] ROLLBACK SUCCESS for $ENVIRONMENT" >> logs/rollback.log
else
    echo "❌ Rollback failed. Health check returned error."
    echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT" >> logs/rollback.log
    exit 1
fi
