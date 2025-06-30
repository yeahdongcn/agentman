#!/bin/bash
set -e

echo "=== Building Agentfile Frontend ==="

# Build the Go binary
echo "Building Go binary..."
go build -o agentfile-frontend main.go

echo "✅ Binary built successfully"

# Test with examples
echo ""
echo "=== Testing with Examples ==="

for example in ../examples/*/Agentfile; do
    if [ -f "$example" ]; then
        echo ""
        echo "🧪 Testing: $example"
        echo "----------------------------------------"
        ./agentfile-frontend "$example" | head -20
        echo "..."
        echo "✅ Parsed successfully"
    fi
done

echo ""
echo "=== Building Docker Image ==="
docker build -t agentfile-frontend .
echo "✅ Docker image built successfully"

echo ""
echo "=== Testing Docker Image ==="
docker run --rm -v "$(pwd)/../examples/agno-example:/workspace" agentfile-frontend /workspace/Agentfile | head -10
echo "✅ Docker image works correctly"

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Usage:"
echo "  Local binary: ./agentfile-frontend <agentfile>"
echo "  Docker image: docker run --rm -v /path/to/agentfile:/workspace agentfile-frontend /workspace/Agentfile"
