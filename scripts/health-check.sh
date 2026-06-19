#!/bin/bash
# scripts/health-check.sh

set -e

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ENV=${1:-all}   # Accept env argument: dev | staging | production | all
FAILED=0

declare -A ENDPOINTS=(
    [production]="https://yourapp.com/health/"
    [staging]="https://staging.yourapp.up.railway.app/health/"
    [dev]="https://django555-dev.up.railway.app/health/"
)

# Build list of endpoints to check
if [ "$ENV" = "all" ]; then
    TARGETS=("production" "staging" "dev")
elif [[ -v ENDPOINTS[$ENV] ]]; then
    TARGETS=("$ENV")
else
    echo "Unknown environment: $ENV"
    echo "Usage: $0 [dev|staging|production|all]"
    exit 1
fi

for TARGET in "${TARGETS[@]}"; do
    ENDPOINT="${ENDPOINTS[$TARGET]}"
    HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" \
        --max-time 10 "$ENDPOINT" || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo "[$TIMESTAMP] ✅ HEALTHY ($TARGET): $ENDPOINT"
    else
        echo "[$TIMESTAMP] ❌ UNHEALTHY ($TARGET): $ENDPOINT (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 Health check FAILED for $TARGET: $ENDPOINT (HTTP $HTTP_CODE) at $TIMESTAMP\"}" \
            --silent || true
    fi
done

exit $FAILED
