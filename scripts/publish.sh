#!/bin/bash

# Build and publish script for agentman package
# Usage: ./scripts/publish.sh [testpypi|pypi]

set -e

TARGET=${1:-testpypi}

echo "🚀 Building and publishing agentman to $TARGET..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info/

# Install publishing dependencies
echo "📦 Installing publishing dependencies..."
uv sync --extra publish

# Build the package
echo "🔨 Building package..."
uv run python -m build

# Check the package
echo "🔍 Checking package..."
uv run python -m twine check dist/*

# Upload based on target
if [ "$TARGET" = "pypi" ]; then
    echo "📤 Uploading to PyPI..."
    uv run python -m twine upload dist/*
elif [ "$TARGET" = "testpypi" ]; then
    echo "📤 Uploading to TestPyPI..."
    uv run python -m twine upload --repository testpypi dist/*
else
    echo "❌ Unknown target: $TARGET"
    echo "Usage: $0 [testpypi|pypi]"
    exit 1
fi

echo "✅ Successfully published to $TARGET!"

if [ "$TARGET" = "testpypi" ]; then
    echo ""
    echo "🧪 To test the installation:"
    echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentman"
elif [ "$TARGET" = "pypi" ]; then
    echo ""
    echo "🎉 Package is now available on PyPI:"
    echo "pip install agentman-mcp"
fi
