#!/bin/bash
# scripts/deploy-production.sh

set -e
echo "🚀 Deploying to PRODUCTION environment..."

# Ensure on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "ERROR: Must be on main branch. Currently on: $CURRENT_BRANCH"
    exit 1
fi

# Final confirmation
read -p "Deploy to PRODUCTION? This is LIVE traffic. (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Run tests first
echo "Running tests..."
ENVIRONMENT=production DJANGO_SETTINGS_MODULE=config.settings.production \
    pytest --tb=short -q || { echo "Tests failed. Aborting deploy."; exit 1; }

# Push to trigger GitHub Actions
echo "Pushing to origin/main..."
git push origin main

echo "✅ Pushed. GitHub Actions will deploy to Railway production environment."
echo "   Monitor: https://github.com/$(git remote get-url origin | sed 's|.*github.com/||' | sed 's|\.git||')/actions"
