#!/bin/bash
# PostgreSQL Restore Script for market-pie5-bot
# Restores database from backup file

set -e  # Exit on error

# Configuration
CONTAINER_NAME="market-pie5-bot-postgres"
DB_NAME="${POSTGRES_DB:-marketbot}"
DB_USER="${POSTGRES_USER:-marketbot_user}"

# Validate arguments
if [ -z "$1" ]; then
    echo "Usage: ./restore_postgres.sh <backup_file>"
    echo ""
    echo "Examples:"
    echo "  ./restore_postgres.sh backups/backup_20260212_143000.sql.gz"
    echo "  ./restore_postgres.sh backups/backup_20260212_143000.sql"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/backup_*.sql.gz 2>/dev/null | awk '{print "  " $NF}' || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Determine if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup file..."
    TEMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: PostgreSQL container '$CONTAINER_NAME' is not running."
    echo "Start the container with (from repo root):"
    echo "  . scripts/export_compose_uid_gid.sh && write_compose_host_user_env \"\$(pwd)\""
    echo "  docker compose --env-file .env.compose-host-user --env-file .env up -d postgres"
    echo "  (drop --env-file .env if you do not use a .env file)"
    [ -n "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
    exit 1
fi

echo "Starting PostgreSQL restore..."
echo "  Database: $DB_NAME"
echo "  Container: $CONTAINER_NAME"
echo "  Backup file: $BACKUP_FILE"
echo ""
echo "⚠️  WARNING: This will overwrite all data in database '$DB_NAME'"
echo -n "Continue? (yes/no): "
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    [ -n "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
    exit 0
fi

# Drop existing connections and database
echo "Preparing database..."
docker exec "$CONTAINER_NAME" psql \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid != pg_backend_pid();" \
    > /dev/null 2>&1 || true

docker exec "$CONTAINER_NAME" psql \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" \
    > /dev/null 2>&1 || true

# Create fresh database
docker exec "$CONTAINER_NAME" psql \
    -U "$DB_USER" \
    -d postgres \
    --no-password \
    -c "CREATE DATABASE $DB_NAME;"

echo "Database prepared. Restoring from backup..."

# Perform restore
docker exec -i "$CONTAINER_NAME" psql \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-password \
    < "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Restore completed successfully"
    echo "  Database: $DB_NAME"
    echo "  Restored from: $BACKUP_FILE"
    
    # Verify restore
    echo ""
    echo "Verifying restore..."
    COUNT=$(docker exec "$CONTAINER_NAME" psql \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-password \
        -t \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    echo "✓ Tables in database: $COUNT"
    
    exit 0
else
    echo "ERROR: Restore failed"
    exit 1
fi

# Cleanup
[ -n "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
