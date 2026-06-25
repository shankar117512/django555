#!/bin/bash
# scripts/rollback.sh
# STAGING-ONLY rollback script.
# Rolls back via Railway's GraphQL API (v2).
#
# Usage:   ./scripts/rollback.sh ["<reason>"]
# Example: ./scripts/rollback.sh "Bad migration in latest deploy"
#
# Requires:
#   RAILWAY_TOKEN_STAGING    – a Railway PERSONAL account token (from railway.com/account/tokens).
#                              Must be the "team token" style (token_xxx), NOT a project token.
#   RAILWAY_PROJECT_TOKEN    – a Railway PROJECT token (from Project Settings → Tokens).
#                              Used for querying deployments with Project-Access-Token header.
#   RAILWAY_PROJECT_ID       – the project UUID for your staging project.
#   RAILWAY_SERVICE_ID       – the service UUID for 'charming-passion'.
#   RAILWAY_ENVIRONMENT_ID   – the environment UUID for 'staging'.
#
# Get UUIDs from the Railway dashboard:
#   Cmd/Ctrl + K → "Copy Project ID" / "Copy Service ID" / "Copy Environment ID"
#
# Get Personal Token from: https://railway.com/account/tokens
# Get Project Token from:  Project → Settings → Tokens
#
# Export them before running:
#   export RAILWAY_TOKEN_STAGING="..."      # personal token (for mutations/redeploy)
#   export RAILWAY_PROJECT_TOKEN="..."      # project token  (for querying deployments)
#   export RAILWAY_PROJECT_ID="..."
#   export RAILWAY_SERVICE_ID="..."
#   export RAILWAY_ENVIRONMENT_ID="..."

set -euo pipefail

ENVIRONMENT="staging"
SERVICE_NAME="charming-passion"
HEALTH_URL="https://charming-passion-staging.up.railway.app/health/"
REASON="${1:-Manual rollback}"
# ✅ FIX 1: Correct API endpoint (.com not .app)
GQL="https://backboard.railway.com/graphql/v2"

# ── Pre-flight checks ────────────────────────────────────────────────────────

for VAR in RAILWAY_TOKEN_STAGING RAILWAY_PROJECT_TOKEN RAILWAY_PROJECT_ID RAILWAY_SERVICE_ID RAILWAY_ENVIRONMENT_ID; do
  if [ -z "${!VAR:-}" ]; then
    echo "❌ $VAR is not set. Export it first."
    exit 1
  fi
done

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required. Install it: sudo apt-get install -y jq"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl is required."
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo "  ROLLBACK SCRIPT (staging only)"
echo "  Service:     $SERVICE_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Reason:      $REASON"
echo "═══════════════════════════════════════════════"

read -r -p "Are you sure you want to rollback $ENVIRONMENT? Type CONFIRM: " CONFIRM
if [ "$CONFIRM" != "CONFIRM" ]; then
  echo "Rollback cancelled."
  exit 0
fi

mkdir -p logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] ROLLBACK initiated for $ENVIRONMENT by ${USER:-unknown} — Reason: $REASON" >> logs/rollback.log

# ── Helper: check response for GraphQL errors ─────────────────────────────────

check_gql_response() {
  local response="$1"
  local context="$2"

  if [ -z "$response" ]; then
    echo "❌ Empty response from Railway API ($context)."
    return 1
  fi

  if echo "$response" | jq -e '.errors // empty' > /dev/null 2>&1; then
    echo "❌ GraphQL error ($context):"
    echo "$response" | jq '.errors'
    return 1
  fi

  if echo "$response" | jq -e '.data == null' > /dev/null 2>&1; then
    echo "❌ API returned null data ($context). Full response:"
    echo "$response" | jq .
    return 1
  fi

  return 0
}

# ── Step 1: List recent deployments ──────────────────────────────────────────
# ✅ FIX 2: Use project-nested query with Project-Access-Token header.
#           The top-level deployments() query requires a personal token and
#           returns "Not Authorized". The nested project → deployments query
#           works correctly with a Project-Access-Token header.
# ✅ FIX 3: Added serviceId and environmentId filters inside the nested query.
# ✅ FIX 4: Use 'first: 10' pagination argument for enough history.

echo ""
echo "Fetching recent deployments for $SERVICE_NAME ($ENVIRONMENT)..."

DEPLOYMENTS_BODY=$(jq -n \
  --arg pid "$RAILWAY_PROJECT_ID" \
  --arg sid "$RAILWAY_SERVICE_ID" \
  --arg eid "$RAILWAY_ENVIRONMENT_ID" \
  '{
    query: "query Deployments($pid: String!, $sid: String!, $eid: String!) {
      project(id: $pid) {
        deployments(
          first: 10,
          input: { serviceId: $sid, environmentId: $eid }
        ) {
          edges {
            node {
              id
              status
              createdAt
              url
            }
          }
        }
      }
    }",
    variables: {
      pid: $pid,
      sid: $sid,
      eid: $eid
    }
  }')

DEPLOYMENTS_RESPONSE=$(curl -s \
  --max-time 30 \
  -X POST "$GQL" \
  -H "Project-Access-Token: $RAILWAY_PROJECT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DEPLOYMENTS_BODY")

if ! check_gql_response "$DEPLOYMENTS_RESPONSE" "fetch deployments"; then
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (could not list deployments)" >> logs/rollback.log
  exit 1
fi

EDGE_COUNT=$(echo "$DEPLOYMENTS_RESPONSE" | jq '.data.project.deployments.edges | length')
if [ "$EDGE_COUNT" -eq 0 ]; then
  echo "❌ No deployments found for this service/environment. Check your IDs."
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (no deployments found)" >> logs/rollback.log
  exit 1
fi

echo ""
echo "Recent deployments (newest first):"
echo "$DEPLOYMENTS_RESPONSE" | jq -r '
  .data.project.deployments.edges[] | .node |
  "  \(.id)  status=\(.status)  createdAt=\(.createdAt)"
'

# ── Step 2: Pick rollback target ──────────────────────────────────────────────

CURRENT_ID=$(echo "$DEPLOYMENTS_RESPONSE" | jq -r \
  '.data.project.deployments.edges[0].node.id // empty')

ROLLBACK_ID=$(echo "$DEPLOYMENTS_RESPONSE" | jq -r '
  .data.project.deployments.edges[1:] |
  map(select(.node.status == "SUCCESS")) |
  .[0].node.id // empty
')

if [ -z "$ROLLBACK_ID" ]; then
  echo ""
  echo "❌ No previous SUCCESS deployment found to roll back to."
  echo "   (Current deployment: ${CURRENT_ID:-unknown})"
  echo "   Only SUCCESS deployments are safe rollback targets."
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (no eligible SUCCESS deployment)" >> logs/rollback.log
  exit 1
fi

ROLLBACK_CREATED_AT=$(echo "$DEPLOYMENTS_RESPONSE" | jq -r \
  --arg id "$ROLLBACK_ID" \
  '.data.project.deployments.edges[] | select(.node.id == $id) | .node.createdAt')

echo ""
echo "Current deployment : $CURRENT_ID"
echo "Rollback target    : $ROLLBACK_ID  (created $ROLLBACK_CREATED_AT)"
echo ""
read -r -p "Proceed with rollback to $ROLLBACK_ID? Type YES: " CONFIRM2
if [ "$CONFIRM2" != "YES" ]; then
  echo "Rollback cancelled at deployment selection."
  exit 0
fi

# ── Step 3: Trigger redeploy of the chosen snapshot ──────────────────────────
# ✅ FIX 5: Redeploy mutation uses PERSONAL token (Authorization: Bearer),
#           NOT the project token. Mutations require personal-level auth.

echo ""
echo "Triggering redeploy of snapshot $ROLLBACK_ID ..."

REDEPLOY_BODY=$(jq -n \
  --arg id "$ROLLBACK_ID" \
  '{
    query: "mutation Redeploy($id: String!) { deploymentRedeploy(id: $id) { id status } }",
    variables: { id: $id }
  }')

REDEPLOY_RESPONSE=$(curl -s \
  --max-time 30 \
  -X POST "$GQL" \
  -H "Authorization: Bearer $RAILWAY_TOKEN_STAGING" \
  -H "Content-Type: application/json" \
  -d "$REDEPLOY_BODY")

if ! check_gql_response "$REDEPLOY_RESPONSE" "deploymentRedeploy"; then
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (redeploy mutation error)" >> logs/rollback.log
  exit 1
fi

NEW_DEPLOYMENT_ID=$(echo "$REDEPLOY_RESPONSE" | jq -r \
  '.data.deploymentRedeploy.id // empty')

if [ -z "$NEW_DEPLOYMENT_ID" ]; then
  echo "❌ Redeploy response is missing a deployment id."
  echo "$REDEPLOY_RESPONSE" | jq .
  echo "[$TIMESTAMP] ROLLBACK FAILED for $ENVIRONMENT (no deployment id in redeploy response)" >> logs/rollback.log
  exit 1
fi

echo "✅ Redeploy triggered. New deployment ID: $NEW_DEPLOYMENT_ID"

# ── Step 4: Poll until new deployment is SUCCESS or FAILED ───────────────────
# ✅ FIX 6: Status polling also uses Project-Access-Token (read query).

echo ""
echo "Polling deployment status (up to 10 minutes)..."
MAX_WAIT=600
INTERVAL=15
ELAPSED=0
DEP_STATUS="UNKNOWN"

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  STATUS_BODY=$(jq -n \
    --arg id "$NEW_DEPLOYMENT_ID" \
    '{
      query: "query DeploymentStatus($id: String!) { deployment(id: $id) { id status } }",
      variables: { id: $id }
    }')

  STATUS_RESPONSE=$(curl -s \
    --max-time 30 \
    -X POST "$GQL" \
    -H "Project-Access-Token: $RAILWAY_PROJECT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STATUS_BODY")

  if ! check_gql_response "$STATUS_RESPONSE" "poll status" 2>/dev/null; then
    echo "  [${ELAPSED}s] Warning: could not read status, retrying..."
  else
    DEP_STATUS=$(echo "$STATUS_RESPONSE" | jq -r \
      '.data.deployment.status // "UNKNOWN"')
    echo "  [${ELAPSED}s] Status: $DEP_STATUS"

    case "$DEP_STATUS" in
      SUCCESS)
        echo ""
        echo "✅ Deployment reached SUCCESS."
        break
        ;;
      FAILED|CRASHED|REMOVED)
        echo ""
        echo "❌ Rollback deployment ended with status: $DEP_STATUS"
        echo "[$TIMESTAMP] ROLLBACK DEPLOYMENT $DEP_STATUS for $ENVIRONMENT (deployment $NEW_DEPLOYMENT_ID)" >> logs/rollback.log
        exit 1
        ;;
    esac
  fi

  sleep "$INTERVAL"
  ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$ELAPSED" -ge "$MAX_WAIT" ] && [ "$DEP_STATUS" != "SUCCESS" ]; then
  echo "❌ Timed out after ${MAX_WAIT}s waiting for SUCCESS (last status: $DEP_STATUS)."
  echo "[$TIMESTAMP] ROLLBACK TIMEOUT for $ENVIRONMENT (deployment $NEW_DEPLOYMENT_ID)" >> logs/rollback.log
  exit 1
fi

# ── Step 5: Health check ──────────────────────────────────────────────────────

echo ""
echo "Running health check at $HEALTH_URL ..."

sleep 5

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  --max-time 15 "$HEALTH_URL" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Health check passed (HTTP $HTTP_CODE)."
  echo "✅ Rollback complete. Service is healthy."
  echo "[$TIMESTAMP] ROLLBACK SUCCESS for $ENVIRONMENT (snapshot=$ROLLBACK_ID new_deployment=$NEW_DEPLOYMENT_ID)" >> logs/rollback.log
else
  echo "❌ Health check returned HTTP $HTTP_CODE (expected 200)."
  echo "   Service may still be starting — check Railway dashboard."
  echo "[$TIMESTAMP] ROLLBACK HEALTH CHECK FAILED for $ENVIRONMENT (HTTP $HTTP_CODE, deployment $NEW_DEPLOYMENT_ID)" >> logs/rollback.log
  exit 1
fi
