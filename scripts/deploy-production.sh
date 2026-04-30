#!/bin/bash
# scripts/deploy-production.sh

set -e
echo "🚀 Deploying to PRODUCTION environment..."

CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Switching to main branch..."
    git checkout main
fi

# Final confirmation
read -p "Deploy to PRODUCTION? This is LIVE traffic. (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo "Merging from staging..."
git merge staging --no-edit

echo "Tagging release..."
VERSION="v$(date +%Y.%m.%d.%H%M)"
git tag -a "$VERSION" -m "Production release $VERSION"

echo "Pushing to origin/main..."
git push origin main
git push origin "$VERSION"

echo "✅ Pushed. GitHub Actions will deploy to Railway production."
echo "   Tag: $VERSION"
