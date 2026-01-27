#!/bin/bash

# Configuration
IMAGE_NAME="log-analyzer"
# Default to a placeholder user if not provided
DOCKER_USER="${1:-your_username}"
TAG="${2:-latest}"

FULL_IMAGE_NAME="$DOCKER_USER/$IMAGE_NAME:$TAG"

echo "Building for user: $DOCKER_USER"
echo "Image: $FULL_IMAGE_NAME"

# 1. Create a new builder instance if it doesn't exist
if ! docker buildx inspect mybuilder > /dev/null 2>&1; then
    echo "Creating new buildx builder..."
    docker buildx create --name mybuilder --use
    docker buildx inspect --bootstrap
else
    echo "Using existing buildx builder..."
    docker buildx use mybuilder
fi

# 2. Build and Push for both AMD64 and ARM64
echo "Starting multi-arch build (amd64, arm64)..."
docker buildx build --platform linux/amd64,linux/arm64 \
  -t "$FULL_IMAGE_NAME" \
  --push \
  .

echo "Done! Image pushed to: $FULL_IMAGE_NAME"
