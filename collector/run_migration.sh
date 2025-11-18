#!/bin/bash
# Run database migration on Railway
# This script runs the migration using Railway CLI

set -e

echo "🚂 Running database migration on Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    echo "Please install Railway CLI:"
    echo "  npm i -g @railway/cli"
    echo "  OR"
    echo "  brew install railway"
    exit 1
fi

# Check if linked to a service
if ! railway status &> /dev/null; then
    echo "⚠️  Not linked to Railway service. Linking..."
    echo "Please run: railway link"
    exit 1
fi

echo "✅ Railway CLI found and linked"
echo ""
echo "📦 Running migration script..."
echo ""

# Run the migration script via Railway
railway run python migrate_add_stripe_columns.py

echo ""
echo "✅ Migration complete!"
echo ""
echo "🔍 Verify migration:"
echo "   Check Railway logs or test the API to confirm columns were added"

