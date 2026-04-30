#!/bin/bash
# scripts/deploy-dev.sh

set -e
echo "🚀 Deploying to DEV environment..."

# Ensure on dev branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo "ERROR: Must be on dev branch. Currently on: $CURRENT_BRANCH"
    exit 1
fi

# Run tests first
echo "Running tests..."
ENVIRONMENT=dev DJANGO_SETTINGS_MODULE=config.settings.dev \
    pytest --tb=short -q || { echo "Tests failed. Aborting deploy."; exit 1; }

# Push to trigger GitHub Actions
echo "Pushing to origin/dev..."
git push origin dev

echo "✅ Pushed. GitHub Actions will deploy to Railway dev environment."
echo "   Monitor: https://github.com/$(git remote get-url origin | sed 's|.*github.com/||' | sed 's|\.git||')/actions"
