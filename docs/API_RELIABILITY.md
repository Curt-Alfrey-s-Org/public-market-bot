# API Reliability & Retry Strategy

**Phase 1.1 (Startup Recovery) & Phase 1.2 (API Retry Logic)**

## Overview

This document explains how market-pie5-bot handles network failures, API timeouts, and rate limiting using intelligent retry logic and cache fallback mechanisms.

## Phase 1.1: Startup Recovery

### Goal
Auto-load market data on bot restart if database is empty, reducing startup time and ensuring the bot has data to work with immediately.

### How It Works

When the bot starts:

1. **Check for Existing Data**
   - Check if `bot_state.json` exists and contains data
   - Check if database has existing market snapshots or trades
   - If found: skip yfinance fetch and mark as initialized

2. **Fetch Initial Data**
   - If no data found: fetch initial data from yfinance
   - Default symbols: AAPL, SPY, QQQ
   - Single attempt per symbol with 60-second timeout
   - Continue if some symbols fail

3. **Graceful Degradation**
   - If all yfinance fetches fail: log warning but continue
   - Bot will operate with limited data until yfinance recovers
   - Return 503 Service Unavailable in health check if degraded

### Health Check Response

The `/api/health` endpoint includes startup status:

```json
{
  "running": "ready",
  "startup_status": {
    "initialized": true,
    "timestamp": "2026-02-12T10:30:45.123456",
    "symbol_count": 3,
    "error": null
  }
}
```

### Startup Timeline

| Event | Duration | Status |
|-------|----------|--------|
| API startup begins | 0s | Starting |
| Self-tests complete | ~100ms | Tests OK |
| Bot data initialization | 10-30s | Fetching (yfinance) |
| Ready for requests | ~30s | Ready |

**Expected first startup: 10-30 seconds**

## Phase 1.2: API Retry Logic

### Goal
Handle network failures, timeouts, and rate limiting gracefully without crashing the bot.

### Retry Strategy

All API calls (yfinance, Schwab) use exponential backoff retry logic:

```
Attempt 1: Immediate
Attempt 2: Wait 2^0 * 1s = 1s
Attempt 3: Wait 2^1 * 1s = 2s
Attempt 4: Wait 2^2 * 1s = 4s
```

**Default: 3 retries, max ~7 seconds total wait time**

### Error Classification

| Error Type | Retryable | Examples |
|-----------|-----------|----------|
| **Timeout** | ✅ Yes | `asyncio.TimeoutError`, `socket.timeout` |
| **Network** | ✅ Yes | `ConnectionError`, `ConnectionRefused` |
| **Rate Limit** | ✅ Yes | HTTP 429 (Too Many Requests) |
| **Server Error** | ✅ Yes | HTTP 502, 503, 504 |
| **Client Error** | ❌ No | HTTP 400, 401, 403, 404 |

### Log Output

When retries occur, logs show:

```
[RETRY] attempt 1 (TimeoutError, retry after 1.2s) for yfinance fetch: AAPL
[RETRY] attempt 2 (TimeoutError, retry after 2.1s) for yfinance fetch: AAPL
[RETRY] Success on attempt 3/3 for yfinance fetch: AAPL
```

On failure after max retries:

```
[RETRY] Failed after 3 attempts for yfinance fetch: AAPL
Last error: TimeoutError: _ssl.c:123 timed out
Attempts: attempt 1 (TimeoutError, retry after 1.2s); attempt 2 (TimeoutError, retry after 2.1s)
```

### Cache Fallback

When all retries are exhausted:

1. **Check Cache**: Look for recently-fetched data in TTL cache
2. **Use Fallback**: If found and not expired (default 5 minutes): use cached data
3. **Log Fallback**: `[CACHE] Using cached data from 5 minutes ago`
4. **Degrade**: If cache miss: bot operates with degraded functionality

### Cache Configuration

| Parameter | Default | Purpose |
|-----------|---------|---------|
| TTL (Time To Live) | 5 minutes | How long to keep cached data |
| Max Entries | Unlimited | Number of symbols to cache |
| Strategy | LRU-style | Oldest entries expire first |

### Usage Examples

#### yfinance with Retry

```python
from api.utils import with_retry
from api.utils import cache_get, cache_set
import yfinance

async def fetch_stock_data(symbol: str):
    """Fetch with retry and cache fallback."""
    
    # Try with retry
    try:
        result = await with_retry(
            lambda: yfinance.Ticker(symbol).history(period="1d"),
            max_retries=3,
            timeout=60,
            operation_name=f"yfinance:{symbol}"
        )
        
        # Cache successful result
        cache_set(f"yfinance:{symbol}", result, ttl_seconds=300)
        return result
        
    except Exception as e:
        logger.error(f"Fetch failed for {symbol}: {str(e)[:100]}")
        
        # Try cache fallback
        cached = cache_get(f"yfinance:{symbol}")
        if cached:
            logger.info(f"Using cached data for {symbol}")
            return cached
        
        raise  # No fallback available
```

#### Schwab API with Retry

```python
async def schwab_fetch_orders():
    """Fetch orders with retry logic."""
    
    return await with_retry(
        client.get_accounts,  # Schwab API function
        max_retries=3,
        backoff_factor=2.0,
        timeout=30,
        operation_name="schwab:get_accounts"
    )
```

#### Synchronous Function

```python
from api.utils import retry_sync, retry_on_exception

# Using function
result = retry_sync(
    func=some_blocking_function,
    max_retries=3,
    timeout=30
)

# Using decorator
@retry_on_exception(max_retries=3)
def my_api_call():
    return requests.get('https://api.example.com/data')
```

## Integration with Bot

### Startup Initialization

The bot calls `initialize_bot_data()` during startup:

```python
# api/main.py lifespan
async def lifespan(app: FastAPI):
    ...
    # Initialize bot data (Phase 1.1)
    try:
        init_result = await initialize_bot_data()
        logger.info(f"Bot data initialized: {init_result}")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
    
    yield  # Application runs
    ...
```

### Per-Request Retry

All yfinance calls should be wrapped:

```python
# Before
data = yfinance.Ticker(symbol).history(...)

# After
data = await with_retry(
    lambda: ...,
    max_retries=3,
    operation_name=f"yfinance:{symbol}"
)
```

## Testing

Run the test suites:

```bash
# Startup recovery tests
python3 -m pytest tests/backend/test_startup_recovery.py -v

# Retry logic tests
python3 -m pytest tests/backend/test_retry_logic.py -v

# Both
python3 -m pytest tests/backend/test_startup_recovery.py tests/backend/test_retry_logic.py -v
```

### Test Coverage

**Phase 1.1:**
- ✅ Empty DB → yfinance fetch → data loads within 30s
- ✅ Existing bot_state.json → skip fetch, mark ready immediately
- ✅ yfinance timeout (60s limit) → log warning, don't crash
- ✅ yfinance not installed → log error, continue with degraded status
- ✅ Concurrent symbol fetches → all succeed
- ✅ HTTP health check includes startup_status

**Phase 1.2:**
- ✅ API timeout first 2 times → retry on 3rd → success
- ✅ Connection error → exponential backoff → eventual success
- ✅ Rate limit (429) → backoff → eventual success
- ✅ Permanent error (404) → fail immediately, no retries
- ✅ All retries fail → use cached data → fallback used
- ✅ Cache expiry → remove stale entries
- ✅ Concurrent API calls → all retry independently

## Production Considerations

### Under Heavy API Load

When the API is heavily loaded and users see rate limiting (429 errors):

1. **Initial requests**: Timeout after 60s
2. **Retry 1**: Wait 1-2 seconds, try again
3. **Retry 2**: Wait 2-4 seconds, try again
4. **Retry 3**: Wait 4-8 seconds, try again
5. **Final result**: Success or cache fallback

**Users may see 2-3 minute response times under extreme load.**

### Database Optimization

Ensure trading history is indexed for fast checks during startup:

```sql
CREATE INDEX idx_trades_timestamp ON trades(created_at);
SELECT COUNT(*) FROM trades;  -- Should be fast
```

### Monitoring

Track retry metrics:

```python
# Add to monitoring dashboard
retry_count = logger.count("Retry")
retry_success = logger.count("Success on attempt")
cache_hit = logger.count("Using cached data")
```

## Limitations & Known Issues

1. **Synchronous yfinance**: Currently each timeout costs 60s. Consider async wrapper in future.
2. **Global cache**: Simple in-memory cache. Consider Redis for distributed bots.
3. **No request deduplication**: Multiple requests for same symbol will each retry independently.
4. **No adaptive backoff**: Backoff is fixed. Future: use server-provided `Retry-After` headers.

## References

- [Phase 1.1 Startup Recovery Tests](test_startup_recovery.py)
- [Phase 1.2 Retry Logic Tests](test_retry_logic.py)
- [Retry Module](../api/utils/retries.py)
- [Cache Module](../api/utils/cache.py)
- [Startup Module](../api/startup.py)

## Rollout Plan

| Phase | Changes | Risk | Timeline |
|-------|---------|------|----------|
| Phase 1.1 | Startup initialization, health endpoint | Low | 4-6 hours |
| Phase 1.2 | Retry logic, cache fallback | Medium | 6-8 hours |
| Phase 1.3 | Wrap all yfinance calls | Medium | In parallel |
| Phase 1.4 | Wrap Schwab API calls | Medium | In parallel |

**Total estimated time: 10-14 hours for both phases**

---

**Status**: Implementation in progress
**Updated**: 2026-02-12
