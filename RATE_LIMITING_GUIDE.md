# Rate Limiting Guide for market-pie5-bot

## Overview

The bot includes comprehensive built-in rate limiting for external API calls to prevent exceeding API quotas and avoid 429 (Rate Limited) errors. This feature automatically tracks and enforces rate limits for all major APIs:

- **NewsAPI** (Sentiment analysis)
- **Finnhub** (Financial news)
- **Alpha Vantage** (Fundamental data)
- **yfinance** (Market data)
- **HuggingFace** (ML optimization)

## Problem Addressed

**Before rate limiting:**
```
[12:03:44] sentiment_analyzer - ERROR - NewsAPI error 429: {"status":"error","code":"rateLimited","message":"You have made too many requests recently. Developer accounts are limited to 100 requests over a 24 hour period (50 requests available every 12 hours). Please upgrade to a paid plan if you need more requests."}
[12:05:12] data_fetcher - ERROR - Alpha Vantage error: API rate limit reached
```

**After rate limiting:**
- API calls are tracked automatically
- Calls are blocked when limits are reached
- Clear warnings are logged with wait times
- No more 429 errors from APIs
- Proactive enforcement prevents quota exhaustion

## How It Works

### RateLimiter Class

The `RateLimiter` class tracks API calls using a sliding time window:

```python
from sentiment_analyzer import RateLimiter

# Create a rate limiter: 100 calls per 24 hours
limiter = RateLimiter(
    max_calls=100,
    time_window=86400,  # 24 hours in seconds
    name="NewsAPI"
)

# Check if call can be made
if limiter.can_make_call():
    # Make API call
    response = api.fetch_data()
    
    # Record the call
    limiter.record_call()
else:
    # Rate limit reached
    wait_time = limiter.get_wait_time()
    print(f"Wait {wait_time} seconds before next call")
```

### Automatic Integration

Rate limiting is automatically applied to all API calls:

1. **NewsAPI** - Limits enforced in both sync and async methods (sentiment_analyzer.py)
2. **Finnhub** - Limits enforced in both sync and async methods (sentiment_analyzer.py)
3. **Alpha Vantage** - Limits enforced in both sync and async methods (data_fetcher.py, async_data_fetcher.py)
4. **yfinance** - Limits enforced in both sync and async methods (data_fetcher.py, async_data_fetcher.py)
5. **HuggingFace** - Limits enforced for ML optimization requests (ml_param_optimizer.py)

When a rate limit is reached:
- The API call is **skipped** (not made)
- A warning is logged with details
- The remaining calls are shown
- Wait time until next available call is calculated

## Configuration

### Environment Variables

Add these to your `.env` file to configure rate limits:

```bash
# NewsAPI Rate Limiting (Default: 100 calls per 24 hours)
NEWS_API_MAX_CALLS_PER_DAY=100
NEWS_API_TIME_WINDOW_HOURS=24

# Finnhub Rate Limiting (Default: 60 calls per 60 seconds)
FINNHUB_MAX_CALLS_PER_MINUTE=60
FINNHUB_TIME_WINDOW_SECONDS=60

# Alpha Vantage Rate Limiting (Default: 5 calls per 60 seconds)
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE=5
ALPHA_VANTAGE_TIME_WINDOW_SECONDS=60

# yfinance Rate Limiting (Default: 30 calls per 60 seconds)
YFINANCE_MAX_CALLS_PER_MINUTE=30
YFINANCE_TIME_WINDOW_SECONDS=60

# HuggingFace Rate Limiting (Default: 10 calls per 60 seconds)
HUGGINGFACE_MAX_CALLS_PER_MINUTE=10
HUGGINGFACE_TIME_WINDOW_SECONDS=60
```

### Default Limits

| API | Free Tier Limit | Bot Default | Module |
|-----|----------------|-------------|--------|
| NewsAPI | 100 requests/day | 100 calls/24 hours | sentiment_analyzer.py |
| Finnhub | 60 requests/minute | 60 calls/60 seconds | sentiment_analyzer.py |
| Alpha Vantage | 5 requests/minute, 500/day | 5 calls/60 seconds | data_fetcher.py, async_data_fetcher.py |
| yfinance | No official limit | 30 calls/60 seconds | data_fetcher.py, async_data_fetcher.py |
| HuggingFace | Varies by tier | 10 calls/60 seconds | ml_param_optimizer.py |

### Adjusting Limits

**Conservative approach (recommended):**
```bash
# Use 90% of quota to leave headroom
NEWS_API_MAX_CALLS_PER_DAY=90
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE=4

# For multiple bot instances, divide the quota
NEWS_API_MAX_CALLS_PER_DAY=50  # 2 bots sharing 100/day quota
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE=2  # 2 bots sharing 5/min quota
```

**Paid plans:**
```bash
# If you have a paid NewsAPI plan (e.g., 1000 requests/day)
NEWS_API_MAX_CALLS_PER_DAY=1000

# If you have Alpha Vantage premium (e.g., 75 requests/min)
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE=75

# If you have HuggingFace Pro (higher rate limits)
HUGGINGFACE_MAX_CALLS_PER_MINUTE=60
```

**Development/Testing:**
```bash
# Lower limits for testing rate limiting behavior
NEWS_API_MAX_CALLS_PER_DAY=10
ALPHA_VANTAGE_MAX_CALLS_PER_MINUTE=2
YFINANCE_MAX_CALLS_PER_MINUTE=5
```

## Logging and Monitoring

### Rate Limit Warnings

When a rate limit is reached, you'll see warnings like:

```
[12:03:44] sentiment_analyzer - WARNING - NewsAPI rate limit reached (0/100 calls available). Next call available in 2.5 hours. Skipping fetch for AAPL.
[12:05:30] data_fetcher - WARNING - Alpha Vantage rate limit reached (0/5 calls available). Next call available in 45.2s. Skipping fetch for MSFT.
[12:06:15] ml_param_optimizer - WARNING - HuggingFace rate limit reached (0/10 calls available). Next call available in 30.5s. Skipping API call.
```

### Debug Information

With debug logging enabled, you'll see:

```
[12:03:44] sentiment_analyzer - DEBUG - NewsAPI call made. Remaining calls: 95/100
[12:03:45] data_fetcher - DEBUG - Alpha Vantage call made. Remaining calls: 4/5
[12:03:46] data_fetcher - DEBUG - yfinance call made. Remaining calls: 28/30
```

### Checking Rate Limit Status

```python
from sentiment_analyzer import SentimentAnalyzer
from data_fetcher import DataFetcher
from ml_param_optimizer import MLParameterOptimizer

# Check sentiment analyzer rate limits
analyzer = SentimentAnalyzer()
print(f"NewsAPI: {analyzer.news_api_limiter.get_remaining_calls()}/{analyzer.news_api_limiter.max_calls}")
print(f"Finnhub: {analyzer.finnhub_limiter.get_remaining_calls()}/{analyzer.finnhub_limiter.max_calls}")

# Check data fetcher rate limits
fetcher = DataFetcher()
print(f"Alpha Vantage: {fetcher.alpha_vantage_limiter.get_remaining_calls()}/{fetcher.alpha_vantage_limiter.max_calls}")
print(f"yfinance: {fetcher.yfinance_limiter.get_remaining_calls()}/{fetcher.yfinance_limiter.max_calls}")

# Check ML optimizer rate limits
optimizer = MLParameterOptimizer()
print(f"HuggingFace: {optimizer.hf_api_limiter.get_remaining_calls()}/{optimizer.hf_api_limiter.max_calls}")
```

## Best Practices

### 1. Use Caching Effectively

The bot already caches sentiment data for 1 hour. This reduces API calls:

```python
# First call: Makes API request
sentiment1 = analyzer.get_sentiment_score('AAPL')

# Within 1 hour: Uses cache (no API call)
sentiment2 = analyzer.get_sentiment_score('AAPL')
```

### 2. Prioritize Stocks

Focus sentiment analysis on your most active positions:

```bash
# Limit stocks analyzed for sentiment
ENABLE_SENTIMENT_FILTER=true
MAX_DISCOVERED_STOCKS=10
```

### 3. Adjust Refresh Intervals

Increase refresh intervals to reduce API calls:

```bash
# Increase watchlist refresh interval
TOP_PERFORMERS_REFRESH_INTERVAL=300  # 5 minutes instead of 60 seconds
```

### 4. Monitor Usage

Run the demo script to understand rate limiting:

```bash
python3 demo_rate_limiting.py
```

### 5. Plan for Multiple Bots

If running multiple bot instances:

```bash
# Bot 1 .env
NEWS_API_MAX_CALLS_PER_DAY=50

# Bot 2 .env
NEWS_API_MAX_CALLS_PER_DAY=50

# Total: 100 calls shared between 2 bots
```

## Troubleshooting

### Problem: Still Getting 429 Errors

**Causes:**
1. Rate limits set too high in `.env`
2. Multiple bot instances using same API key
3. External tools using the same API key

**Solutions:**
1. Reduce `NEWS_API_MAX_CALLS_PER_DAY` to 90 or lower
2. Divide quota among bot instances
3. Use separate API keys for each application

### Problem: Too Few API Calls

**Symptoms:**
- Sentiment data rarely updated
- Warnings about rate limits when calls available

**Solutions:**
1. Check `.env` configuration
2. Verify `NEWS_API_MAX_CALLS_PER_DAY` is not too low
3. Restart bot to reset rate limiter state

### Problem: Want More API Calls

**Options:**
1. **Upgrade to paid plan** (NewsAPI Pro: 250/day, Business: unlimited)
2. **Use multiple API keys** (rotate between keys)
3. **Alternative APIs** (Finnhub, Alpha Vantage, etc.)
4. **Reduce frequency** (increase cache duration, reduce refresh intervals)

## Testing

### Run Rate Limiting Tests

```bash
# Run all rate limiting tests
python3 -m unittest test_sentiment_analyzer.TestRateLimiting -v

# Run all sentiment analyzer tests
python3 -m unittest test_sentiment_analyzer -v
```

### Expected Test Output

```
test_can_make_call_when_under_limit ... ok
test_cannot_make_call_when_at_limit ... ok
test_finnhub_respects_rate_limit ... ok
test_get_remaining_calls ... ok
test_newsapi_respects_rate_limit ... ok
test_old_calls_cleaned_up ... ok
test_rate_limiter_initialization ... ok
test_wait_time_calculation ... ok

Ran 8 tests in 1.102s
OK
```

## API Documentation

### RateLimiter Class

```python
class RateLimiter:
    def __init__(self, max_calls: int, time_window: int, name: str = "API"):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
            name: Name of the API for logging purposes
        """
    
    def can_make_call(self) -> bool:
        """Check if a call can be made without exceeding rate limits"""
    
    def record_call(self):
        """Record that a call was made"""
    
    def get_wait_time(self) -> float:
        """Get seconds to wait before next call is allowed"""
    
    def get_remaining_calls(self) -> int:
        """Get number of calls that can still be made"""
```

## Benefits

✅ **Prevents 429 errors** - No more rate limit violations from any API  
✅ **Automatic tracking** - No manual counting needed  
✅ **Configurable** - Adjust limits via environment variables  
✅ **Multi-API support** - Separate limits for each service (NewsAPI, Finnhub, Alpha Vantage, yfinance, HuggingFace)  
✅ **Graceful degradation** - Skips calls when limit reached instead of failing  
✅ **Detailed logging** - Know your usage status for all APIs  
✅ **Thread-safe** - Uses threading.Lock for concurrent operations  
✅ **Comprehensive coverage** - All external API calls are protected  
✅ **Cost optimization** - Prevents unexpected overage charges on paid plans  
✅ **Async support** - Rate limiting works in both sync and async contexts

## Related Documentation

- [Environment Configuration](.env.example)
- [Sentiment Analysis Guide](SENTIMENT_PORTFOLIO_GUIDE.md)
- [Web GUI Guide](WEB_GUI_GUIDE.md)
- [Data Fetching](data_fetcher.py)
- [Async Data Fetching](async_data_fetcher.py)
- [ML Parameter Optimization](ml_param_optimizer.py)
- [Testing Guide](CONTRIBUTING.md)

## Support

If you encounter issues with rate limiting:

1. Check your `.env` configuration
2. Run `python3 demo_rate_limiting.py` to verify behavior
3. Review logs for rate limit warnings
4. Check [GitHub Issues](https://github.com/operator/market-pie5-bot/issues)
5. See [troubleshooting](#troubleshooting) section above

---

**Last Updated:** 2026-01-22  
**Feature:** Comprehensive API Rate Limiting  
**Affected APIs:** NewsAPI, Finnhub, Alpha Vantage, yfinance, HuggingFace
