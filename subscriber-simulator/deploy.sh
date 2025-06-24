#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Subscriber Simulator Deployment Script ---"

# 1. Check for kubectl and docker
if ! command -v kubectl &> /dev/null
then
    echo "kubectl could not be found. Please install kubectl."
    exit 1
fi

if ! command -v docker &> /dev/null
then
    echo "docker could not be found. Please install Docker."
    exit 1
fi

# 2. Load environment variables from .env file
ENV_FILE="./.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE..."
    # Use 'set -a' to export all variables loaded from .env
    set -a
    source "$ENV_FILE"
    set +a
    echo "Environment variables loaded."
else
    echo "WARNING: .env file not found at $ENV_FILE. Please ensure your VastDB credentials and DOCKER_REGISTRY are set as environment variables."
    echo "Example .env content:"
    echo "VASTDB_ENDPOINT=your_vastdb_endpoint"
    echo "VASTDB_ACCESS_KEY=your_vastdb_access_key"
    echo "VASTDB_SECRET_KEY=your_vastdb_secret_key"
    echo "DOCKER_REGISTRY=your_docker_registry_url (e.g., ghcr.io/your-username or your-ecr-repo-url)"
fi

# 3. Validate VastDB credentials and Docker Registry
if [ -z "$VASTDB_ENDPOINT" ] || [ -z "$VASTDB_ACCESS_KEY" ] || [ -z "$VASTDB_SECRET_KEY" ]; then
    echo "ERROR: VastDB credentials (VASTDB_ENDPOINT, VASTDB_ACCESS_KEY, VASTDB_SECRET_KEY) are not set."
    echo "Please set them in your .env file or as environment variables before running this script."
    exit 1
fi

if [ -z "$DOCKER_REGISTRY" ]; then
    echo "ERROR: DOCKER_REGISTRY environment variable is not set."
    echo "Please set it in your .env file or as an environment variable (e.g., DOCKER_REGISTRY=ghcr.io/your-username)."
    exit 1
fi

# Define the full image name with registry
IMAGE_NAME="$DOCKER_REGISTRY/subscriber-simulator:latest"

# 4. Create/Update Kubernetes Secret for VastDB Credentials
echo "Creating/Updating Kubernetes secret 'vastdb-secrets'..."
kubectl create secret generic vastdb-secrets \
  --from-literal=VASTDB_ENDPOINT="$VASTDB_ENDPOINT" \
  --from-literal=VASTDB_ACCESS_KEY="$VASTDB_ACCESS_KEY" \
  --from-literal=VASTDB_SECRET_KEY="$VASTDB_SECRET_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Kubernetes secret 'vastdb-secrets' created/updated."

# 5. Build and Push the Docker Image
echo "Building Docker image '$IMAGE_NAME'..."
docker build -t "$IMAGE_NAME" .
echo "Docker image built successfully."

echo "Logging in to Docker registry (if required)..."
# You might need to run 'docker login your_docker_registry_url' manually before this script
# or configure Kubernetes ImagePullSecrets if using a private registry.
# This script assumes you are already logged in or using a public registry.

echo "Pushing Docker image '$IMAGE_NAME' to registry..."
docker push "$IMAGE_NAME"
echo "Docker image pushed successfully."

# 6. Deploy to Kubernetes
echo "Applying Kubernetes deployment and service manifests..."
# Ensure k8s-deployment.yaml is updated to use the full image name
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
echo "Kubernetes manifests applied successfully."

# 7. Verify Deployment
echo "Verifying deployment status..."
kubectl get deployments subscriber-simulator
kubectl get pods -l app=subscriber-simulator
kubectl get services subscriber-simulator-service

echo "Deployment process completed."
echo "You can access the API via the Kubernetes service. If using minikube, you might use 'minikube service subscriber-simulator-service --url' to get the URL."
