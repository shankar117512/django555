#!/bin/bash
# scripts/rollback.sh
# STAGING-ONLY rollback script. Mirrors the logic used in
# .github/workflows/rollback.yml, since the Railway CLI has no
# `rollback` subcommand — rollback must go through Railway's GraphQL API.
#
# Usage: ./scripts/rollback.sh "<reason>"
# Example: ./scripts/rollback.sh "Bad migration in latest deploy"
#
# Requires: RAILWAY_TOKEN_STAGING (a Railway *project* access token for the
# staging environment) to be set in your shell before running, e.g.:
#   export RAILWAY_TOKEN_DEV="xxxxx"

set -euo pipefail

ENVIRONMENT="staging"
SERVICE="charming-passion"
HEALTH_URL="https://charming-passion-staging.up.railway.app/health/"
REASON="${1:-Manual rollback}"

if [ -z "${RAILWAY_TOKEN_STAGING:-}" ]; then
  echo "❌ RAILWAY_TOKEN_STAGING is not set. Export it first:"
  echo '   export RAILWAY_TOKEN_STAGING="your-staging-project-token"'
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo "  ROLLBACK SCRIPT (staging only)"
echo "  Service:     $SERVICE"
echo "  Environment: $ENVIRONMENT"
echo "  Reason:      $REASON"
echo "═══════════════════════════════════════════════"

# Confirmation prompt
read -r -p "Are you sure you want to rollback $ENVIRONMENT? Type CONFIRM: " CONFIRM
if [ "$CONFIRM" != "CONFIRM" ]; then
  echo "Rollback cancelled."
  exit 0
fi

mkdir -p logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] ROLLBACK initiated for $ENVIRONMENT by ${USER:-unknown}" >> logs/rollback.log
echo "Reason: $REASON" >> logs/rollback.log

# --- Find the previous deployable deployment (SUCCESS or REMOVED) ---
echo "Fetching recent deployments for $SERVICE ($ENVIRONMENT)..."
if ! command -v railway >/dev/null 2>&1; then
  echo "❌ Railway CLI not found. Install it: npm install -g @railway/cli"
  exit 1
fi

RAILWAY_TOKEN="$RAILWAY_TOKEN_STAGING" railway deployment list \
  --service "$SERVICE" \
  --environment "$ENVIRONMENT" \
  --json --limit 10 > deployments.json

ROLLBACK_ID=$(jq -r '
  [.[] | select(.status=="SUCCESS" or .status=="REMOVED")][1].id // empty
' deployments.json)

if [ -z "$ROLLBACK_ID" ]; then
  echo "❌ No earlier deployment found to roll back to."
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (no candidate deployment)" >> logs/rollback.log
  exit 1
fi
echo "Rolling back to deployment: $ROLLBACK_ID"

# --- Execute rollback via Railway GraphQL API (no CLI 'rollback' command exists) ---
RESPONSE=$(curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Project-Access-Token: $RAILWAY_TOKEN_STAGING" \
  -H "Content-Type: application/json" \
  --data-binary @- <<EOF
{
  "query": "mutation deploymentRollback(\$id: String!) { deploymentRollback(id: \$id) }",
  "variables": { "id": "$ROLLBACK_ID" }
}
EOF
)
echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "❌ Rollback request failed:"
  echo "$RESPONSE" | jq '.errors'
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT" >> logs/rollback.log
  exit 1
fi

OK=$(echo "$RESPONSE" | jq -r '.data.deploymentRollback')
if [ "$OK" != "true" ]; then
  echo "❌ Rollback call returned no errors but did not report success: $RESPONSE"
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT" >> logs/rollback.log
  exit 1
fi
echo "Rollback triggered successfully for deployment $ROLLBACK_ID."

# --- Wait and health check ---
echo "Waiting for rollback deployment to come up..."
sleep 60

echo "Running health check at $HEALTH_URL..."
if curl -f "$HEALTH_URL" --silent --output /dev/null; then
  echo "✅ Rollback successful. Service is healthy."
  echo "[$TIMESTAMP] ROLLBACK SUCCESS for $ENVIRONMENT (deployment $ROLLBACK_ID)" >> logs/rollback.log
else
  echo "❌ Rollback triggered, but health check failed."
  echo "[$TIMESTAMP] ROLLBACK HEALTH CHECK FAILED for $ENVIRONMENT (deployment $ROLLBACK_ID)" >> logs/rollback.log
  exit 1
fi
