# PostgreSQL Backup Strategy - Market Bot

## Overview

Automated daily backups ensure database resilience and enable point-in-time recovery.

## Backup Configuration

### Backup Schedule
- **Frequency:** Daily at 02:00 AM
- **Retention:** 30 days rolling
- **Compression:** gzip (reduces size ~80%)
- **Location:** `./backups/`

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add this line for 2 AM daily backups
0 2 * * * cd /home/operator/market-pie5-bot && ./scripts/backup_postgres.sh >> logs/backup.log 2>&1
```

### Verify Cron Job

```bash
# List scheduled jobs
crontab -l | grep backup_postgres

# Monitor backups
tail -f logs/backup.log
```

## Backup Scripts

### Manual Backup

```bash
# Create immediate backup
./scripts/backup_postgres.sh

# Output:
# Starting PostgreSQL backup...
#   Database: marketbot
#   Container: market-pie5-bot-postgres
#   Timestamp: 20260212_143000
#   Location: backups/backup_20260212_143000.sql.gz
# ✓ Backup completed
# ✓ Compressed: backups/backup_20260212_143000.sql.gz (2.5M)
# ✓ Backup successful
```

### List Backups

```bash
# View all backups with size
ls -lh ./backups/backup_*.sql.gz

# Example output:
# -rw-r--r-- 1 user user 2.5M Feb 12 02:00 backup_20260212_020000.sql.gz
# -rw-r--r-- 1 user user 2.4M Feb 11 02:00 backup_20260211_020000.sql.gz
# -rw-r--r-- 1 user user 2.6M Feb 10 02:00 backup_20260210_020000.sql.gz
```

### Manual Restore

**⚠️ WARNING: Restore will overwrite all data in the database**

```bash
# Restore from specific backup
./scripts/restore_postgres.sh backups/backup_20260212_143000.sql.gz

# Interactive prompts:
# Starting PostgreSQL restore...
#   Database: marketbot
#   Container: market-pie5-bot-postgres
#   Backup file: backups/backup_20260212_143000.sql.gz
# 
# ⚠️  WARNING: This will overwrite all data in database 'marketbot'
# Continue? (yes/no): yes
# 
# ✓ Restore completed successfully
```

### Restore from Uncompressed Backup

```bash
# If backup is not compressed
./scripts/restore_postgres.sh backups/backup_20260212_143000.sql
```

## Health Check API

The `/api/health` endpoint includes backup metadata:

```bash
curl -H "X-API-Key: $BOT_API_KEY" http://localhost:8004/api/health
```

Response:
```json
{
  "status": "healthy",
  "api_version": "1.0.0",
  "database": {
    "status": "connected",
    "name": "marketbot"
  },
  "last_backup": {
    "timestamp": "2026-02-12T02:00:00Z",
    "age_hours": 1.5,
    "status": "current"
  },
  "alerts": []
}
```

### Backup Status Indicators

| Status | Meaning | Action |
|--------|---------|--------|
| `current` | Backup < 24 hours old | ✓ All good |
| `warning` | Backup 1-2 days old | ⚠️ Check backup job |
| `stale` | Backup > 2 days old | 🔴 Investigate backup failure |

## Automated Backup Monitoring

Check if last backup is current:

```bash
# Get last backup timestamp
LAST_BACKUP=$(stat -c %Y ./backups/backup_*.sql.gz | sort -1 | tail -1)
NOW=$(date +%s)
AGE_HOURS=$(( ($NOW - $LAST_BACKUP) / 3600 ))

if [ $AGE_HOURS -gt 24 ]; then
    echo "⚠️  Backup is $AGE_HOURS hours old (expected: < 24 hours)"
    # Send alert
fi
```

## Backup Verification

### Check Backup Integrity

```bash
# Verify gzip file is not corrupted
gzip -t ./backups/backup_20260212_143000.sql.gz
echo $?  # 0 = OK, 1 = corrupted

# Decompress to verify
gunzip -c ./backups/backup_20260212_143000.sql.gz | head -20
```

### Test Restore (Before Production Use)

```bash
# Create test database
docker exec market-pie5-bot-postgres psql -U postgres \
  -c "CREATE DATABASE marketbot_test;"

# Restore to test database
docker exec -i market-pie5-bot-postgres psql -U marketbot_user \
  -d marketbot_test < <(gunzip -c ./backups/backup_20260212_143000.sql.gz)

# Test queries
docker exec market-pie5-bot-postgres psql -U marketbot_user \
  -d marketbot_test \
  -c "SELECT COUNT(*) FROM trades;"

# Cleanup test database
docker exec market-pie5-bot-postgres psql -U postgres \
  -c "DROP DATABASE marketbot_test;"
```

## Restore Procedures

### Full Database Restore

```bash
# 1. Stop the application
docker compose down

# 2. Restore from backup
./scripts/restore_postgres.sh backups/backup_20260212_143000.sql.gz

# 3. Restart application
docker compose up -d

# 4. Verify health
curl -H "X-API-Key: $BOT_API_KEY" http://localhost:8004/api/health
```

### Point-in-Time Recovery

PostgreSQL allows recovery to a specific time using WAL (Write-Ahead Logs):

```bash
# List available transactions
docker exec market-pie5-bot-postgres pg_waldump pg_wal/000000010000000000000001 | head -20

# Restore and stop at specific timestamp
docker exec -i market-pie5-bot-postgres pg_restore \
  --exit-on-error \
  < ./backups/backup_20260212_143000.sql.gz
```

## Monitoring and Alerts

### Backup Log

Backups are logged to `logs/backup.log`:

```bash
# Monitor backup activity
tail -f logs/backup.log

# Example logs:
# 2026-02-12 02:00:01: Starting PostgreSQL backup...
# 2026-02-12 02:00:15: ✓ Backup completed: backups/backup_20260212_020000.sql
# 2026-02-12 02:00:22: ✓ Compressed: backups/backup_20260212_020000.sql.gz (2.5M)
# 2026-02-12 02:00:22: ✓ Backup successful
```

### Alert Conditions

Configure alerts if:

1. **No backup in 24 hours**
   ```bash
   LAST_BACKUP_TIME=$(stat -c %Y ./backups/backup_*.sql.gz | sort -1 | tail -1)
   NOW=$(date +%s)
   if [ $((NOW - LAST_BACKUP_TIME)) -gt 86400 ]; then
       # Send alert
   fi
   ```

2. **Backup file corrupted**
   ```bash
   if ! gzip -t ./backups/backup_*.sql.gz; then
       # Send alert
   fi
   ```

3. **Low disk space**
   ```bash
   FREE_SPACE=$(df ./backups | awk 'NR==2 {print $4}')
   if [ "$FREE_SPACE" -lt 1000000 ]; then  # Less than 1GB
       # Send alert and clean old backups
   fi
   ```

## Backup Retention

Backups older than 30 days are automatically deleted:

```bash
# Manual cleanup (keeps last 30 days)
find ./backups -name "backup_*.sql.gz" -mtime "+30" -delete

# To change retention period, edit RETENTION_DAYS in backup_postgres.sh
```

## Storage Estimation

| Database Size | Compressed | 30-day Retention |
|---------------|-----------|------------------|
| 10 MB | ~2 MB | 60 MB |
| 50 MB | ~10 MB | 300 MB |
| 100 MB | ~20 MB | 600 MB |
| 500 MB | ~100 MB | 3 GB |

## Disaster Recovery

### Complete Recovery Steps

1. **Check backups exist:**
   ```bash
   ls -lh ./backups/backup_*.sql.gz
   ```

2. **Stop all services:**
   ```bash
   docker compose down
   ```

3. **Remove corrupted database:**
   ```bash
   docker volume rm market-pie5-bot-postgres_data  # Only if necessary!
   ```

4. **Restore backup:**
   ```bash
   ./scripts/restore_postgres.sh backups/backup_20260212_143000.sql.gz
   ```

5. **Restart application:**
   ```bash
   docker compose up -d
   ```

6. **Verify system health:**
   ```bash
   sleep 10
   curl -H "X-API-Key: $BOT_API_KEY" http://localhost:8004/api/health
   ```

## External Backup Storage

For production, consider backing up to external storage:

```bash
# Backup to AWS S3
aws s3 cp ./backups/backup_latest.sql.gz \
  s3://my-backup-bucket/market-bot-backups/ --sse AES256

# Backup to Google Cloud Storage
gsutil cp ./backups/backup_latest.sql.gz \
  gs://my-backup-bucket/market-bot-backups/

# Backup to remote server
rsync -avz ./backups/ backup@backup-server:/backups/market-bot/
```

## References

- [PostgreSQL pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [PostgreSQL pg_restore Documentation](https://www.postgresql.org/docs/current/app-pgrestore.html)
- [PostgreSQL Point-in-Time Recovery](https://www.postgresql.org/
