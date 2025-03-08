#!/bin/bash
set -e

until mongosh --host mongodb --username admin --password admin_password --authenticationDatabase admin --eval "print(\"waited for connection\")"
do
    echo "Waiting for mongodb to be ready..."
    sleep 2
done

echo "MongoDB is ready! Running initialization script..."
mongosh --host mongodb --username admin --password admin_password --authenticationDatabase admin /docker-entrypoint-initdb.d/init.js 