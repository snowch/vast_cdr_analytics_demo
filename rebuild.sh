#!/usr/bin/env bash

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Remove existing stack if it exists
if docker stack ls | grep -q telco_demo; then
  docker stack rm telco_demo
else
  echo "Stack telco_demo does not exist, skipping removal."
fi

# Build images
docker build --build-arg CACHEBUST=$(date +%s) -t telco-generator:latest telco-generator
docker build --build-arg CACHEBUST=$(date +%s) -t vast-db-connector:latest vast-db-connector

# Wait for the network to be removed
echo -n "Waiting for network telco_demo_default to be removed ."
while docker network inspect telco_demo_default >/dev/null 2>&1; do
  echo -n "."
  sleep 2
done

docker stack deploy -c docker-stack.yml telco_demo
