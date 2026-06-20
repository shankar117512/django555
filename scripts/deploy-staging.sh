#!/bin/bash
# scripts/deploy-staging.sh

set -e
echo "🚀 Deploying to STAGING environment..."

CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "staging" ]; then
    echo "Switching to staging branch..."
    git checkout staging
fi

echo "Merging from dev..."
git merge dev --no-edit

echo "Pushing to origin/staging..."
git push origin staging

echo "✅ Pushed. GitHub Actions will deploy to Railway staging."
