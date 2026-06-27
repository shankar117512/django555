#!/bin/bash
# scripts/deploy-staging.sh

set -e
echo "🚀 Deploying to STAGING environment..."

# Ensure on staging branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "staging" ]; then
    echo "ERROR: Must be on staging branch. Currently on: $CURRENT_BRANCH"
    exit 1
fi

# Run tests first
echo "Running tests..."
ENVIRONMENT=staging DJANGO_SETTINGS_MODULE=config.settings.staging \
    pytest --tb=short -q || { echo "Tests failed. Aborting deploy."; exit 1; }

# Push to trigger GitHub Actions
echo "Pushing to origin/staging..."
git push origin staging

echo "✅ Pushed. GitHub Actions will deploy to Railway staging environment."
echo "   Monitor: https://github.com/$(git remote get-url origin | sed 's|.*github.com/||' | sed 's|\.git||')/actions"
