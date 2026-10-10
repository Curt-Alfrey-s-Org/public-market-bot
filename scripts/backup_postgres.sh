#!/bin/bash
# PostgreSQL Backup Script for market-pie5-bot
# Creates daily backups of the database with automatic compression

set -e  # Exit on error

# Configuration
BACKUP_DIR="./backups"
CONTAINER_NAME="market-pie5-bot-postgres"
DB_NAME="${POSTGRES_DB:-marketbot}"
DB_USER="${POSTGRES_USER:-marketbot_user}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"
BACKUP_FILE_GZ="$BACKUP_FILE.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup..."
echo "  Database: $DB_NAME"
echo "  Container: $CONTAINER_NAME"
echo "  Timestamp: $TIMESTAMP"
echo "  Location: $BACKUP_FILE_GZ"

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: PostgreSQL container '$CONTAINER_NAME' is not running."
    echo "Start the container with (from repo root):"
    echo "  . scripts/export_compose_uid_gid.sh && write_compose_host_user_env \"\$(pwd)\""
    echo "  docker compose --env-file .env.compose-host-user --env-file .env up -d postgres"
    echo "  (drop --env-file .env if you do not use a .env file)"
    exit 1
fi

# Perform backup
docker exec "$CONTAINER_NAME" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    format=plain \
    > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Backup completed: $BACKUP_FILE"
    
    # Compress the backup
    gzip "$BACKUP_FILE"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    echo "✓ Compressed: $BACKUP_FILE_GZ ($BACKUP_SIZE)"
    
    # Clean up old backups (older than RETENTION_DAYS)
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
    
    # List recent backups
    echo ""
    echo "Recent backups:"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz | tail -5
    
    echo ""
    echo "✓ Backup successful"
    exit 0
else
    echo "ERROR: Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi
