# Log Analysis Report - Bot Running Analysis

**Date:** January 26, 2026  
**Analysis Period:** Real-time monitoring  
**Status:** ⚠️ **CRITICAL ISSUES DETECTED**

---

## 🔴 Critical Issues Found

### 1. Thread Exhaustion Error (CRITICAL)

**Error:**
```
RuntimeError: can't start new thread
File "/home/operator/market-pie5-bot/web_gui.py", line 2944, in fetch_feed_data
  candidates = get_top_performers_watchlist(max_stocks=FEED_SIZE * 2)
```

**Root Cause:**
- `yfinance` library uses `multitasking` with `threads=True` for parallel downloads
- Feed refreshes are happening too frequently (every few seconds)
- Each refresh downloads 100 stocks (FEED_SIZE * 2 = 50 * 2 = 100)
- System thread limit is being exhausted (1823 threads active, max ~127k)
- No error handling or backoff when thread exhaustion occurs

**Impact:**
- Feed updates failing repeatedly
- Stock screener unable to fetch data
- Potential memory/resource leaks
- Bot functionality degraded

**Frequency:** Every 1-2 seconds (repeated failures)

---

### 2. Schwab API Sandbox Mode Warnings

**Warning:**
```
[INFO ALERT] Subject: Sandbox Mode: Schwab API Required
Schwab sandbox API failed for COF/SLB/APA.
Sandbox mode requires Schwab API connectivity - NO fallback allowed.
```

**Impact:**
- Expected behavior if Schwab API not configured
- Not critical if using yfinance simulation mode
- Can be resolved by configuring Schwab API or disabling sandbox mode

**Frequency:** Multiple occurrences for different symbols

---

## 📊 System Status

### Bot Process
- **Status:** ✅ Running
- **PID:** 304480
- **CPU:** 241% (multi-threaded)
- **Memory:** 984MB
- **Uptime:** ~23 minutes

### Thread Statistics
- **Active Threads:** 1823
- **System Thread Limit:** 127,249
- **User Thread Limit:** 63,624
- **Status:** ⚠️ High thread count (potential leak)

### Log Files
- **trading_bot.log:** 6.6MB (growing)
- **alerts.log:** 2.4KB

---

## 🔍 Detailed Error Pattern

### Thread Exhaustion Pattern
```
2026-01-26 14:39:35,000 - ERROR - Error fetching feed data: can't start new thread
2026-01-26 14:39:35,006 - WARNING - Feed update error: Error fetching feed data: can't start new thread
2026-01-26 14:39:35,939 - ERROR - Error fetching feed data: can't start new thread
2026-01-26 14:39:35,952 - WARNING - Feed update error: Error fetching feed data: can't start new thread
```

**Pattern:** Error occurs every 1-2 seconds, indicating:
1. Feed refresh interval too aggressive
2. No backoff/retry logic
3. Thread pool not being released properly

---

## 🛠️ Recommended Fixes

### Priority 1: Fix Thread Exhaustion (CRITICAL)

1. **Disable threading in yfinance downloads**
   - Change `threads=True` to `threads=False` in `stock_screener.py`
   - Use sequential downloads instead of parallel

2. **Add error handling for thread exhaustion**
   - Catch `RuntimeError: can't start new thread`
   - Implement exponential backoff
   - Add circuit breaker pattern

3. **Reduce feed refresh frequency**
   - Increase `FEED_UPDATE_INTERVAL` from 300s to 600s (10 minutes)
   - Add minimum time between refresh attempts
   - Implement feed refresh throttling

4. **Add thread pool management**
   - Limit concurrent yfinance downloads
   - Use thread pool executor with max workers
   - Properly cleanup threads after use

### Priority 2: Improve Error Handling

1. **Add retry logic with backoff**
2. **Implement circuit breaker for feed updates**
3. **Add thread count monitoring**
4. **Log thread exhaustion as critical alert**

### Priority 3: Optimize Feed Updates

1. **Cache feed data more aggressively**
2. **Reduce number of stocks fetched** (FEED_SIZE * 2 = 100 is high)
3. **Batch downloads more efficiently**
4. **Add feed update debouncing**

---

## 📈 Integration Status

### ML/AI Integrations
- **ML Signal Filter:** ✅ No errors in logs
- **Portfolio Optimizer:** ✅ No errors in logs
- **Adaptive Learning:** ✅ No errors in logs
- **Real-time ML Optimization:** ✅ No errors in logs

**Note:** Integrations appear to be working, but feed errors may prevent proper testing.

---

## 🎯 Immediate Actions Required

1. **URGENT:** Fix thread exhaustion in yfinance downloads
2. **URGENT:** Add error handling and backoff for feed updates
3. **HIGH:** Reduce feed refresh frequency
4. **MEDIUM:** Monitor thread count and add alerts
5. **LOW:** Configure Schwab API or disable sandbox mode warnings

---

## 📝 Next Steps

1. Implement fixes for thread exhaustion
2. Test feed updates with reduced frequency
3. Monitor thread count after fixes
4. Verify all integrations still working
5. Update documentation with thread limits

---

**Report Generated:** 2026-01-26 14:39  
**Next Review:** After fixes implemented
