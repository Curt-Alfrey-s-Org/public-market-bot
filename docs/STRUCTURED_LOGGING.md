# Structured Logging - Market Bot

## Overview

Structured logging converts logs to JSON format for:
- Easy parsing by log aggregators (ELK, Splunk, CloudWatch)
- Filtering and searching by field
- Better debugging with structured context
- Integration with monitoring systems

## Log Format

Each log entry is a valid JSON object:

```json
{
  "timestamp": "2026-02-12T14:30:00.123456Z",
  "level": "INFO",
  "message": "Trade executed",
  "logger": "api.routes.trades",
  "event": "trade_executed",
  "symbol": "AAPL",
  "price": 150.25,
  "quantity": 10,
  "trade_type": "BUY",
  "trade_id": "trade_20260212_143000_001"
}
```

## Log Levels

| Level | Purpose | Example |
|-------|---------|---------|
| `DEBUG` | Detailed diagnostic information | `data_fetcher: Requesting price for AAPL` |
| `INFO` | General informational messages | `bot_started: Paper trading mode enabled` |
| `WARNING` | Warning messages for potential issues | `trade_failed: Order expired for MSFT` |
| `ERROR` | Error messages for serious problems | `api_error: Database connection timeout` |
| `CRITICAL` | Critical errors requiring immediate action | `startup_failed: Missing required secrets` |

## Log Fields

Each log entry includes:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | When the event occurred | `2026-02-12T14:30:00.123Z` |
| `level` | String | Log severity | `INFO`, `ERROR` |
| `message` | String | Human-readable message | `Trade executed successfully` |
| `logger` | String | Component/module name | `api.routes.trades` |
| `event` | String | Event type for filtering | `trade_executed` |
| Additional fields | Various | Context-specific data | `symbol`, `price`, `quantity` |

## Querying Logs

### View Logs as JSON

```bash
# View tail of logs with JSON formatting
tail -f logs/trading_bot.log | jq '.'
```

### Filter by Event Type

```bash
# Find all trade execution logs
cat logs/trading_bot.log | jq 'select(.event == "trade_executed")'

# Output:
# {
#   "timestamp": "2026-02-12T14:30:00.123456Z",
#   "level": "INFO",
#   "event": "trade_executed",
#   "symbol": "AAPL",
#   "price": 150.25,
#   "quantity": 10
# }
```

### Filter by Symbol

```bash
# Get all logs for a specific stock
cat logs/trading_bot.log | jq 'select(.symbol == "AAPL")'
```

### Filter by Level

```bash
# Find all errors
cat logs/trading_bot.log | jq 'select(.level == "ERROR")'

# Find all warnings and errors
cat logs/trading_bot.log | jq 'select(.level == "WARNING" or .level == "ERROR")'
```

### Time Range Filtering

```bash
# Get logs from specific time period
cat logs/trading_bot.log | jq 'select(.timestamp > "2026-02-12T14:00:00Z" and .timestamp < "2026-02-12T15:00:00Z")'
```

### Count Events

```bash
# Count trade executions
cat logs/trading_bot.log | jq 'select(.event == "trade_executed")' | wc -l

# Count errors by type
cat logs/trading_bot.log | jq -r 'select(.level == "ERROR") | .error_type' | sort | uniq -c
```

## Log Examples

### Bot Startup

```json
{
  "timestamp": "2026-02-12T08:00:00.000000Z",
  "level": "INFO",
  "message": "Bot started",
  "event": "bot_started",
  "version": "1.5.0",
  "mode": "paper_trading",
  "sandbox_enabled": true
}
```

### Trade Execution

```json
{
  "timestamp": "2026-02-12T14:30:00.123456Z",
  "level": "INFO",
  "message": "Trade executed",
  "event": "trade_executed",
  "trade_id": "trade_20260212_143000_001",
  "symbol": "AAPL",
  "price": 150.25,
  "quantity": 10,
  "trade_type": "BUY",
  "order_type": "LIMIT",
  "status": "FILLED",
  "execution_time_ms": 245
}
```

### Price Fetch Failure

```json
{
  "timestamp": "2026-02-12T14:31:00.456789Z",
  "level": "ERROR",
  "message": "Price fetch failed",
  "event": "data_fetch_failed",
  "symbol": "MSFT",
  "error": "TimeoutError",
  "error_message": "Request timed out after 30s",
  "source": "yfinance",
  "attempt": 2,
  "max_retries": 3
}
```

### Database Connection

```json
{
  "timestamp": "2026-02-12T08:00:01.000000Z",
  "level": "INFO",
  "message": "Database connected",
  "event": "database_connected",
  "database": "marketbot",
  "pool_size": 10,
  "connection_string": "postgresql://***REDACTED***"
}
```

## API Endpoints

### GET /api/logs

Get logs with optional filtering:

```bash
# Get last 50 logs
curl -H "X-API-Key: $BOT_API_KEY" \
  "http://localhost:8004/api/logs" | jq '.'

# Get logs for specific symbol
curl -H "X-API-Key: $BOT_API_KEY" \
  "http://localhost:8004/api/logs?symbol=AAPL" | jq '.'

# Get only errors
curl -H "X-API-Key: $BOT_API_KEY" \
  "http://localhost:8004/api/logs?status=error" | jq '.'

# Get last 100 logs
curl -H "X-API-Key: $BOT_API_KEY" \
  "http://localhost:8004/api/logs?limit=100" | jq '.'

# Get logs from specific time range
curl -H "X-API-Key: $BOT_API_KEY" \
  "http://localhost:8004/api/logs?start=2026-02-12T14:00:00Z&end=2026-02-12T15:00:00Z" | jq '.'
```

### Response Format

```json
{
  "logs": [
    {
      "timestamp": "2026-02-12T14:30:00.123456Z",
      "level": "INFO",
      "event": "trade_executed",
      "symbol": "AAPL",
      "price": 150.25,
      "quantity": 10
    }
  ],
  "total": 1245,
  "limit": 50,
  "filtered_count": 12
}
```

## Log Files

### Location

```bash
logs/
├── trading_bot.log         # Current logs (rotated daily)
├── trading_bot.log.1       # Yesterday's logs
├── trading_bot.log.2       # 2 days ago
├── trading_bot.log.3       # 3 days ago
├── trading_bot.log.4       # 4 days ago
├── trading_bot.log.5       # 5 days ago
├── trading_bot.log.6       # 6 days ago
└── trading_bot.log.7       # 7 days ago
```

### Retention

- Files are rotated daily
- Last 7 files kept by default (7-day rolling retention)
- Each file max 10 MB before rotation
- Total storage: ~70 MB for 7 days

## Log Configuration

### Environment Variables

```bash
# Set logging level
LOG_LEVEL=DEBUG               # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO                # Default: INFO

# Enable/disable debug mode
DEBUG=true                     # Verbose logging
DEBUG=false                    # Normal logging
```

### Programmatic Configuration

In `api/config_logging.py`:

```python
# JSON logging format
logging.basicConfig(
    format='%(message)s',  # Just JSON, no prefix
    level=logging.INFO
)

# File rotation
RotatingFileHandler(
    'logs/trading_bot.log',
    maxBytes=10_000_000,    # 10 MB per file
    backupCount=7           # Keep 7 days
)
```

## Log Analysis

### Find Patterns

```bash
# Errors in past hour
cat logs/trading_bot.log | \
  jq 'select(.level == "ERROR" and .timestamp > now - 3600)'

# All trades for specific symbol
cat logs/trading_bot.log | \
  jq 'select(.event == "trade_executed" and .symbol == "AAPL") | {timestamp, price, quantity, trade_type}'

# Failed API calls
cat logs/trading_bot.log | \
  jq 'select(.event | contains("failed")) | {timestamp, event, error}'
```

### Performance Analysis

```bash
# Average trade execution time
cat logs/trading_bot.log | \
  jq 'select(.event == "trade_executed") | .execution_time_ms' | \
  awk '{sum+=$1; count++} END {print "Average: " sum/count "ms"}'

# Slowest trades
cat logs/trading_bot.log | \
  jq 'select(.event == "trade_executed") | {symbol, execution_time_ms}' | \
  jq -s 'sort_by(.execution_time_ms) | reverse | .[0:10]'
```

### Error Statistics

```bash
# Count errors by type
cat logs/trading_bot.log | \
  jq 'select(.level == "ERROR") | .error' | \
  sort | uniq -c | sort -rn
```

## Integration Examples

### ELK Stack (Elasticsearch, Logstash, Kibana)

Configuration in Logstash:

```logstash
input {
  file {
    path => "/path/to/market-pie5-bot/logs/trading_bot.log"
    codec => json
  }
}

filter {
  if [timestamp] {
    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "market-bot-%{+YYYY.MM.dd}"
  }
}
```

### CloudWatch (AWS)

```bash
# Install CloudWatch agent
pip install awslogs

# Configure credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Stream logs to CloudWatch
awslogs create-group /market-bot/logs
awslogs create-stream /market-bot/logs trading_bot
awslogs tail /market-bot/logs trading_bot --follow
```

### Datadog

```python
# In api/config_logging.py
from datadog import initialize, api
from datadog_logging import DataDogHandler

handler = DataDogHandler(
    api_key="change-me",
    app_key="your_datadog_app_key"
)
logging.getLogger().addHandler(handler)
```

## Dashboard Integration

### Grafana Panels

Query logs by event type:

```
{
  "targets": [
    {
      "expr": 'logs_per_event[5m]',
      "refId": "A",
      "legendFormat": "{{event}}"
    }
  ]
}
```

Example dashboard panels:

1. **Trade Execution Rate** - Trades per minute
2. **Error Rate** - Errors per minute
3. **Average Execution Time** - Trade latency
4. **API Response Times** - Request/response times
5. **System Health** - Memory, CPU usage

## Best Practices

### ✓ DO

- Include relevant context in every log
- Use consistent event names for filtering
- Redact sensitive values (done automatically)
- Log at appropriate levels (avoid everything as INFO)
- Include request IDs for tracing
- Log before and after critical operations

### ✗ DON'T

- Log secrets or API keys (filtered automatically)
- Log excessive details at INFO level
- Use unstructured string messages only
- Mix multiple events in one log entry
- Log personally identifiable information

## Troubleshooting

### Logs Not Appearing

```bash
# Check log file permissions
ls -la logs/trading_bot.log

# Check if logs directory exists
mkdir -p logs

# Check application startup
docker logs market-pie5-bot-api | grep -i "logging\|log_level"

# Verify environment variable
docker compose exec market-pie5-bot-api \
  python -c "import os; print(f'LOG_LEVEL={os.getenv(\"LOG_LEVEL\")}')"
```

### Invalid JSON in Logs

```bash
# Validate JSON format
cat logs/trading_bot.log | jq '.' >/dev/null && echo "Valid JSON"

# Fix formatting issues
cat logs/trading_bot.log | jq -s '.' > logs/trading_bot_formatted.log
```

### File Rotation Not Working

```bash
# Check log file size
du -h logs/trading_bot.log*

# Manual rotation if needed
gzip logs/trading_bot.log
mv logs/trading_bot.log.gz logs/trading_bot.log.7.gz
touch logs/trading_bot.log

# Restart application
docker compose restart market-pie5-bot-api
```

## References

- [Python JSON Logger](https://github.com/madzak/python-json-logger)
- [Structured Logging Best Practices](http://kartar.net/2015/12/structured-logging/)
- [JSON Logging Standard](https://github.com/sirupsen/logrus/blob/master/docs/examples_test.go)
- [ELK Stack Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
