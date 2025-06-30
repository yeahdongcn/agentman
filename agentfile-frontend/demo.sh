#!/bin/bash

# Demo script showing how Agentfile frontend could work with docker buildx
# This is a proof-of-concept that simulates the future integration

set -e

AGENTFILE="$1"
OUTPUT_DIR="${2:-./output}"
IMAGE_NAME="${3:-agentfile-demo}"

if [ -z "$AGENTFILE" ]; then
    echo "Usage: $0 <agentfile> [output_dir] [image_name]"
    echo ""
    echo "Example:"
    echo "  $0 ../examples/agno-example/Agentfile ./build my-agent"
    exit 1
fi

if [ ! -f "$AGENTFILE" ]; then
    echo "Error: Agentfile not found: $AGENTFILE"
    exit 1
fi

echo "🚀 Agentfile Docker Build Demo"
echo "================================"
echo "Agentfile: $AGENTFILE"
echo "Output: $OUTPUT_DIR"
echo "Image: $IMAGE_NAME"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Step 1: Parse Agentfile and generate Dockerfile
echo "📝 Step 1: Parsing Agentfile..."
./agentfile-frontend "$AGENTFILE" > "$OUTPUT_DIR/Dockerfile"
echo "✅ Generated Dockerfile"

# Step 2: Copy context files
echo ""
echo "📂 Step 2: Preparing build context..."
AGENTFILE_DIR=$(dirname "$AGENTFILE")

# Copy agent files if they exist
if [ -d "$AGENTFILE_DIR/agent" ]; then
    cp -r "$AGENTFILE_DIR/agent" "$OUTPUT_DIR/"
    echo "✅ Copied agent/ directory"
fi

# Copy prompt.txt if it exists
if [ -f "$AGENTFILE_DIR/prompt.txt" ]; then
    cp "$AGENTFILE_DIR/prompt.txt" "$OUTPUT_DIR/"
    echo "✅ Copied prompt.txt"
fi

# Copy other files
if [ -f "$AGENTFILE_DIR/README.md" ]; then
    cp "$AGENTFILE_DIR/README.md" "$OUTPUT_DIR/"
    echo "✅ Copied README.md"
fi

# Step 3: Build Docker image
echo ""
echo "🔨 Step 3: Building Docker image..."
cd "$OUTPUT_DIR"

# Remove the syntax directive for now since we don't have a real frontend yet
sed -i.bak '1d' Dockerfile  # Remove first line (syntax directive)

# Build the image
docker build -t "$IMAGE_NAME" .
echo "✅ Image built successfully: $IMAGE_NAME"

# Step 4: Show results
echo ""
echo "🎉 Build Complete!"
echo "=================="
echo "Generated files:"
echo "  📄 $OUTPUT_DIR/Dockerfile"
if [ -d "$OUTPUT_DIR/agent" ]; then
    echo "  📁 $OUTPUT_DIR/agent/"
fi
if [ -f "$OUTPUT_DIR/prompt.txt" ]; then
    echo "  📄 $OUTPUT_DIR/prompt.txt"
fi
echo ""
echo "Docker image: $IMAGE_NAME"
echo ""
echo "To run the container:"
echo "  docker run --rm -it $IMAGE_NAME"
echo ""
echo "To inspect the image:"
echo "  docker run --rm -it $IMAGE_NAME sh"
echo ""

# Step 5: Show how it would work with real buildx frontend
echo "🔮 Future Integration with Docker Buildx:"
echo "==========================================="
echo "Once published as a real frontend, you could use:"
echo ""
echo "# syntax=yeahdongcn/agentfile-frontend:latest"
cat "$AGENTFILE" | head -10
echo "..."
echo ""
echo "And build with:"
echo "  docker buildx build -f Agentfile -t my-agent ."
echo "  # OR"
echo "  docker build -f Agentfile -t my-agent ."
