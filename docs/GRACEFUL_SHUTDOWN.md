# Graceful Shutdown - Market Bot

## Overview

Graceful shutdown ensures:
- Active trades are properly marked
- Database connections are closed cleanly
- No data loss during container termination
- Unfinished operations are safely halted

## Docker Compose Configuration

The docker-compose.yml includes graceful shutdown settings:

```yaml
market-bot-api:
  stop_signal: SIGTERM        # Send SIGTERM (not SIGKILL) for graceful shutdown
  stop_grace_period: 30s      # Wait up to 30 seconds before forcing termination

postgres:
  stop_signal: SIGTERM        # PostgreSQL handles SIGTERM cleanly
  stop_grace_period: 10s      # Shorter grace for database
```

## Shutdown Sequence

When stopping the application:

```bash
docker compose down
```

Sequence of events (30 seconds):

1. **Seconds 0-1:** SIGTERM signal sent to containers
2. **Seconds 1-5:** Application shutdown event handlers execute
3. **Seconds 5-10:** Database connections closed
4. **Seconds 10-20:** In-flight trades marked as pending
5. **Seconds 20-30:** Waiting for graceful exit
6. **Second 30:** SIGKILL sent if still running (forced termination)

## Shutdown Handler

The application's shutdown handler in `api/main.py`:

```python
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== SERVER SHUTTING DOWN ===")
    
    # Save bot state to file
    if hasattr(app.state, 'bot_state'):
        save_bot_state(app.state.bot_state)
        logger.info("Bot state saved")
    
    # Close database connections
    await session.close()
    logger.info("Database connections closed")
    
    # Mark in-flight trades as 'pending'
    mark_pending_trades_if_any()
    logger.info("Pending trades marked")
    
    logger.info("=== SHUTDOWN COMPLETE ===")
```

## Shutdown Verification

### Check Logs for Clean Shutdown

```bash
# View application shutdown logs
docker logs market-pie5-bot-api | tail -50 | grep -E "SHUTTING DOWN|SHUTDOWN COMPLETE|closed"

# Expected output:
# 2026-02-12 14:30:00 - api.main - INFO - === SERVER SHUTTING DOWN ===
# 2026-02-12 14:30:01 - api.main - INFO - Bot state saved
# 2026-02-12 14:30:02 - api.main - INFO - Database connections closed
# 2026-02-12 14:30:03 - api.main - INFO - Pending trades marked
# 2026-02-12 14:30:03 - api.main - INFO - === SHUTDOWN COMPLETE ===
```

### Check for Error-Free Termination

```bash
# View exit codes (0 = clean, non-zero = error)
docker inspect market-pie5-bot-api | grep "ExitCode"

# Expected if stopped cleanly:
# "ExitCode": 0
```

## Shutdown Procedures

### Normal Shutdown (Recommended)

```bash
# Graceful shutdown with 30-second timeout
docker compose down

# Output:
# [+] Running 3/3
#  ✔ Container market-pie5-bot-frontend Stopped    (0.5s)
#  ✔ Container market-pie5-bot-api      Stopped    (2.1s)
#  ✔ Container market-pie5-bot-postgres Stopped    (0.3s)
```

### Restart Services (Preserves Data)

```bash
# Graceful stop and restart specific service
docker compose restart market-pie5-bot-api

# This is equivalent to:
# 1. docker compose stop market-pie5-bot-api
# 2. docker compose start market-pie5-bot-api
```

### Force Shutdown (Emergency Only)

```bash
# Force immediate termination (skips grace period)
# ⚠️ Only use if application is hung or unresponsive
docker compose kill

# Or for specific container:
docker kill market-pie5-bot-api

# WARNING: This may cause:
# - Pending trades to be lost
# - Database corruption if writes in progress
# - Inconsistent state
```

## Shutdown Events

The application handles shutdown gracefully through:

1. **SIGTERM Handler:**
   ```python
   - Listens for SIGTERM signal
   - Calls shutdown event handlers
   - Waits for background tasks to complete
   - Closes database connections
   - Exits cleanly with code 0
   ```

2. **Graceful Task Completion:**
   ```python
   - Running requests are allowed to finish
   - New requests are rejected (503 Service Unavailable)
   - Database operations complete in-flight
   - Long-running tasks are given time to finalize
   ```

3. **Database Cleanup:**
   ```python
   - Active connections are closed
   - Pending transactions are committed or rolled back
   - Connection pool is drained
   - Files are flushed and synced
   ```

## Monitoring Shutdown Health

### Dashboard Shutdown Check

```python
# GET /api/health during shutdown
{
  "status": "shutting_down",
  "api_version": "1.0.0",
  "shutdown_progress": {
    "phase": "saving_state",
    "elapsed_seconds": 2,
    "timeout_seconds": 30
  }
}
```

### Logs During Shutdown

```bash
# Real-time log monitoring during shutdown
docker logs -f market-pie5-bot-api &
sleep 5
docker compose down

# You'll see:
# 2026-02-12 14:30:00 - api.main - INFO - === SERVER SHUTTING DOWN ===
# 2026-02-12 14:30:00 - api.main - INFO - Saving bot state...
# 2026-02-12 14:30:01 - api.main - INFO - Bot state saved
# 2026-02-12 14:30:01 - api.main - INFO - Closing database connections...
# 2026-02-12 14:30:02 - api.main - INFO - Database connections closed
```

## Shutdown Timing

### Expected Shutdown Times

| Component | Time | Notes |
|-----------|------|-------|
| API Server | 2-5 seconds | Closes HTTP server |
| Database Pool | 3-8 seconds | Flushes pending transactions |
| File Operations | <1 second | Syncs bot_state.json |
| Total | 5-15 seconds | Should complete well before 30s timeout |

### If Shutdown Takes > 30 Seconds

Possible issues:

1. **Stuck Database Connection:**
   ```bash
   docker exec market-pie5-bot-postgres \
     psql -U marketbot_user -d marketbot \
     -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"
   ```

2. **Long-Running Request:**
   ```bash
   # Check active HTTP connections
   docker logs market-pie5-bot-api | grep -i "connection\|timeout\|hung"
   ```

3. **File I/O Bottleneck:**
   ```bash
   # Check if bot_state.json is readable/writable
   ls -la bot_state.json
   ```

## Best Practices

### ✓ DO

- Always use `docker compose down` for controlled shutdown
- Verify "SHUTDOWN COMPLETE" in logs
- Allow at least 30 seconds before forcing termination
- Run regular shutdown tests in pre-production
- Monitor shutdown times to detect issues early

### ✗ DON'T

- Use `docker kill` in production (force termination)
- Use `docker rm -f` without stopping first (data loss risk)
- Interrupt shutdown early with Ctrl+C repeatedly
- Shutdown during active trades without marking them
- Shutdown without verifying logs

## Testing Graceful Shutdown

### Basic Shutdown Test

```bash
#!/bin/bash
echo "Starting shutdown test..."
docker compose up -d

echo "Waiting 10s for services to stabilize..."
sleep 10

echo "Starting graceful shutdown..."
START=$(date +%s)
docker compose down
END=$(date +%s)

DURATION=$((END - START))
echo "Shutdown took ${DURATION}s (expected < 30s)"

echo ""
echo "Checking for clean shutdown markers in logs..."
docker logs market-pie5-bot-api | grep -q "SHUTDOWN COMPLETE" && \
  echo "✓ Shutdown completed cleanly" || \
  echo "⚠️  Shutdown markers not found"
```

### Load Shutdown Test

```bash
#!/bin/bash
# Test shutdown during active operations

echo "Starting application..."
docker compose up -d
sleep 10

# Generate some activity
echo "Generating background load..."
for i in {1..10}; do
  curl -s http://localhost:8004/api/health &
done

# Shutdown while activity ongoing
echo "Shutting down while handling requests..."
docker compose down

echo "Checking graceful completion..."
docker logs market-pie5-bot-api | tail -20
```

### Verification Checklist

```bash
#!/bin/bash
# Post-shutdown verification

echo "Post-Shutdown Verification"
echo "=========================="

# Check exit codes
EXIT_CODE=$(docker inspect market-pie5-bot-api | grep -oP '"ExitCode": \K[0-9]+')
[ "$EXIT_CODE" = "0" ] && echo "✓ Clean exit (code 0)" || echo "✗ Error exit (code $EXIT_CODE)"

# Check logs for shutdown sequence
echo -n "✓ Shutdown sequence in logs: "
docker logs market-pie5-bot-api | grep -c "SHUTDOWN COMPLETE" | grep -q "^[1-9]" && echo "yes" || echo "no"

# Check for error messages
ERROR_COUNT=$(docker logs market-pie5-bot-api | grep -i "error\|exception" | wc -l)
echo "  Error messages during shutdown: $ERROR_COUNT"

# Check database can be restarted
echo -n "✓ Database ready for restart: "
docker compose up -d postgres
sleep 3
docker exec market-pie5-bot-postgres pg_isready -U marketbot_user && echo "yes" || echo "no"
```

## Troubleshooting

### Shutdown Hangs (Exceeds 30s)

```bash
# 1. Check what's blocking
docker logs market-pie5-bot-api | tail -20

# 2. Kill hung container
docker kill market-pie5-bot-api

# 3. Check database connections
docker exec market-pie5-bot-postgres \
  psql -U marketbot_user -d marketbot \
  -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"

# 4. Force disconnect stale queries
docker exec market-pie5-bot-postgres \
  psql -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'marketbot';"
```

### Data Loss After Shutdown

```bash
# Check if bot_state.json was saved
ls -la bot_state.json

# If missing, restore from backup
docker exec market-pie5-bot-postgres \
  pg_dump -U marketbot_user -d marketbot \
  | gunzip > backup_emergency.sql
```

### Trades Left in "Pending" State

```bash
# Query for pending trades
docker exec market-pie5-bot-postgres \
  psql -U marketbot_user -d marketbot \
  -c "SELECT * FROM trades WHERE status = 'pending';"

# Manually update if needed
docker exec market-pie5-bot-postgres \
  psql -U marketbot_user -d marketbot \
  -c "UPDATE trades SET status = 'completed' WHERE status = 'pending' AND updated_at < NOW() - INTERVAL '1 hour';"
```

## References

- [Docker Stop Signals Documentation](https://docs.docker.com/compose/compose-file/compose-file-v3/#stop_signal)
- [Docker Grace Period](https://docs.docker.com/compose/compose-file/compose-file-v3/#stop_grace_period)
- [PostgreSQL Server Shutdown](https://www.postgresql.org/
- [FastAPI Shutdown Events](https://fastapi.tiangolo.com/advanced/events/#shutdown-event)
