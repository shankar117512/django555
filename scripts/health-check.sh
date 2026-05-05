#!/bin/bash
# scripts/health-check.sh

set -e

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ENDPOINTS=(
    "https://yourapp.com/health/"
    "https://charming-passion-staging.up.railway.app/"
    "https://dev.yourapp.up.railway.app/health/"
)
FAILED=0

for ENDPOINT in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" \
        --max-time 10 "$ENDPOINT" || echo "000")

    if [ "$HTTP_CODE" != "200" ]; then
        echo "[$TIMESTAMP] ❌ UNHEALTHY: $ENDPOINT (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))

        # Send alert
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 Health check FAILED: $ENDPOINT (HTTP $HTTP_CODE) at $TIMESTAMP\"}" \
            --silent || true
    else
        echo "[$TIMESTAMP] ✅ HEALTHY: $ENDPOINT"
    fi
done

exit $FAILED
