#!/bin/bash

echo "Waiting for services to be ready..."

for service in api-gateway:8000 auth-service:8000 recording-service:8000 transcription-service:8000 summarization-service:8000
do
  until curl -s http://${service}/health > /dev/null; do
    echo "Waiting for ${service}..."
    sleep 5
  done
done

echo "All services are ready. Starting tests..."
python main.py 