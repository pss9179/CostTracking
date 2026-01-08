#!/bin/bash
# Quick script to publish Python SDK to PyPI

set -e  # Exit on error

echo "🚀 Publishing llmobserve to PyPI..."

cd sdk/python

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "📦 Building package..."
python -m build

# Check the build
echo "✅ Checking build..."
twine check dist/*

# Ask for confirmation
read -p "📤 Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "📤 Uploading to PyPI..."
    twine upload dist/*
    echo "✅ Published! Users can now: pip install llmobserve"
else
    echo "❌ Cancelled. Build files are in dist/"
fi

