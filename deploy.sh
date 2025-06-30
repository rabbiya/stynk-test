#!/bin/bash

IMAGE_NAME="usheru-dev:latest"
CONTAINER_NAME="usheru-dev"
HOST_PORT=8001
CONTAINER_PORT=8000

echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Checking if container exists..."
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f $CONTAINER_NAME
fi

echo "Running new container on port $HOST_PORT:$CONTAINER_PORT..."
docker run -d --name $CONTAINER_NAME -p $HOST_PORT:$CONTAINER_PORT --restart always $IMAGE_NAME

echo " Cleaning up unused images..."
docker image prune -f

echo "Deployment complete!"

