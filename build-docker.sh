#!/bin/bash

set -e  # Exit on any error

TAG_NAME=${1:-"default-rate-backend"}

echo "🔧 Building Docker image: $TAG_NAME"

build_with_retry() {
    local dockerfile=$1
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "📦 Attempt $((retry_count + 1)) of $max_retries..."
        
        if docker build -f "$dockerfile" -t "$TAG_NAME" .; then
            echo "✅ Docker build successful!"
            return 0
        else
            echo "❌ Build attempt $((retry_count + 1)) failed"
            retry_count=$((retry_count + 1))
            
            if [ $retry_count -lt $max_retries ]; then
                echo "⏳ Waiting 10 seconds before retry..."
                sleep 10
            fi
        fi
    done
    
    echo "💥 All build attempts failed"
    return 1
}

echo "🔄 Attempting to pull base image..."
docker pull python:3.11-slim || echo "⚠️  Could not pull base image, proceeding with build..."

if ! docker info &>/dev/null; then
    echo "❌ Docker daemon is not running or accessible"
    exit 1
fi

echo "🏗️  Building with primary Dockerfile..."
if build_with_retry "Dockerfile"; then
    echo "🎉 Build completed successfully with primary Dockerfile!"
    exit 0
fi

if [ -f "Dockerfile.alt" ]; then
    echo "🔄 Primary build failed, trying alternative Dockerfile..."
    if build_with_retry "Dockerfile.alt"; then
        echo "🎉 Build completed successfully with alternative Dockerfile!"
        exit 0
    fi
fi

echo "💥 All Docker build attempts failed"
echo "📋 Troubleshooting suggestions:"
echo "   1. Check Docker Hub status: https://status.docker.com/"
echo "   2. Try docker login if you have Docker Hub account"
echo "   3. Check your internet connection"
echo "   4. Try building again in a few minutes (rate limiting)"
exit 1
