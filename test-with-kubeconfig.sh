#!/bin/bash
# Test the Docker image with local kubeconfig
#
# This script demonstrates how to properly mount a kubeconfig file into the
# GlueLinks-API Docker container for testing with a real Kubernetes cluster.
#
# IMPORTANT NOTES:
# - Uses --mount type=bind (NOT -v) to avoid directory creation issues
# - Kubeconfig is copied to .kubeconfig-test (gitignored)
# - K8s cluster must be accessible from Docker's network
# - Localhost clusters (127.0.0.1) won't work from inside container
#
# Usage:
#   ./test-with-kubeconfig.sh
#
# To use with remote cluster or --network host, modify docker run command below.

set -e

echo "=== Testing GlueLinks-API Docker Image with Kubernetes ===" 

# Stop and remove existing container if running
docker stop gluelinks-kubetest 2>/dev/null || true
docker rm gluelinks-kubetest 2>/dev/null || true

# Create a temporary kubeconfig file in current directory (Docker can access this)
# Must be in workspace directory, not /tmp (devcontainer volume isolation)
TEMP_KUBECONFIG="$(pwd)/.kubeconfig-test"
cp ~/.kube/config "$TEMP_KUBECONFIG"
chmod 644 "$TEMP_KUBECONFIG"

echo "Starting container with kubeconfig from: $TEMP_KUBECONFIG"
echo ""
echo "Note: If your K8s cluster is on 127.0.0.1 (like k3d), it won't be"
echo "      accessible from inside the Docker container. This is expected."
echo "      Mock endpoints will still work for testing."
echo ""

# Run container with kubeconfig and env file mounted
# CRITICAL: Use --mount with type=bind to mount files (NOT -v which creates directories)
docker run -d \
  --name gluelinks-kubetest \
  -p 8001:8000 \
  --mount type=bind,source="$TEMP_KUBECONFIG",target=/app/kubeconfig,readonly \
  --mount type=bind,source="$(pwd)/.env.local",target=/app/.env.local,readonly \
  -e KUBECONFIG=/app/kubeconfig \
  ghcr.io/glueops/gluelinks-api:latest

echo "Waiting for container to start..."
sleep 5

echo "=== Container logs ==="
docker logs gluelinks-kubetest 2>&1 | tail -20

echo ""
echo "=== Testing health endpoint ==="
curl -s http://localhost:8001/api/v1/health | jq .

echo ""
echo "=== Testing readiness endpoint ==="
curl -s http://localhost:8001/api/v1/ready | jq .

echo ""
echo "=== Testing real application endpoint ==="
echo "Replace with your actual app name and namespace:"
echo "curl -s http://localhost:8001/api/v1/applications/YOUR-APP/links -H 'Argocd-Application-Name: YOUR-NAMESPACE:YOUR-APP' | jq ."

echo ""
echo "=== Testing mock endpoint ==="
curl -s http://localhost:8001/api/v1/fixtures/all-ok | jq '{app: .app_name, categories: (.categories | map({id, status, links_count: (.links | length)}))}' 

echo ""
echo "=== Container running on http://localhost:8001 ==="
echo "To stop: docker stop gluelinks-kubetest && docker rm gluelinks-kubetest"
echo "To view logs: docker logs -f gluelinks-kubetest"
echo "Temp kubeconfig: $TEMP_KUBECONFIG (cleanup: rm $TEMP_KUBECONFIG)"
