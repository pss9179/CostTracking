#!/bin/bash
# Quick script to publish JavaScript SDK to npm

set -e  # Exit on error

echo "🚀 Publishing llmobserve to npm..."

cd sdk/js

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ node_modules/.cache/

# Build the package
echo "📦 Building package..."
npm run build

# Check if logged in
if ! npm whoami &> /dev/null; then
    echo "❌ Not logged in to npm. Run: npm login"
    exit 1
fi

# Ask for confirmation
read -p "📤 Publish to npm? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "📤 Publishing to npm..."
    npm publish
    echo "✅ Published! Users can now: npm install llmobserve"
else
    echo "❌ Cancelled. Build files are in dist/"
fi

