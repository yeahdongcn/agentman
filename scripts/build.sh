#!/bin/bash

# Quick build and check script
# Usage: ./scripts/build.sh

set -e

echo "🔨 Building agentman package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
uv sync --extra publish

# Build the package
echo "🏗️  Building wheel and source distribution..."
uv run python -m build

# Check the built package
echo "🔍 Checking built package..."
uv run python -m twine check dist/*

# List built files
echo "📄 Built files:"
ls -la dist/

echo "✅ Build completed successfully!"
echo ""
echo "📁 Built files are in the 'dist/' directory"
echo "🚀 To publish: ./scripts/publish.sh [testpypi|pypi]"
