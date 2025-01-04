#!/bin/bash

set -e

# Set variables
BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/data/pg_backups/${BACKUP_DATE}"
S3_BUCKET="pg-backups-to-update"
PG_USER="pgusername"
DOCKER_CONTAINER="postgres_container"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Get list of all databases excluding template0, template1, and postgres
databases=$(docker exec ${DOCKER_CONTAINER} psql -U ${PG_USER} -t -c "SELECT datname FROM pg_database WHERE datname NOT IN ('template0', 'template1', 'postgres');")

# Backup each database
for db in ${databases}
do
    echo "Backing up database: ${db}"
    docker exec ${DOCKER_CONTAINER} pg_dump -U ${PG_USER} -Fc ${db} > "${BACKUP_DIR}/${db}.dump"
done

# Upload to S3
aws s3 sync ${BACKUP_DIR} s3://${S3_BUCKET}/${BACKUP_DATE}/

# Clean up local backups
rm -rf ${BACKUP_DIR}
