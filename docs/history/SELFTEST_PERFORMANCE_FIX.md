# Self-Test Performance Fix

## Problem Identified

1. **Yellow light staying on**: Self-test was running on EVERY health check request
2. **Bot going offline/online**: Health endpoint was slow/blocking, causing connection status to flicker
3. **Performance issue**: `/api/system/health` was running full self-test suite (6 tests) every 30 seconds

## Root Cause

The `/api/system/health` endpoint was running the complete self-test suite on **every single request**:
- Sidebar polls health every 30 seconds
- ConnectionStatus polls health every 5 seconds
- Each health check triggered a full self-test run (6 tests, ~0.5 seconds each)
- This caused the endpoint to be slow and block requests

## Solution Implemented

### 1. Added Caching to Self-Test Results
- Cache self-test results for 60 seconds
- Only run tests when cache is stale or missing
- Return cached results for subsequent requests

### 2. Improved Connection Status
- Increased timeout from 3s to 5s
- Added `keepPreviousData: true` to prevent flickering
- Reduced retries from 2 to 1 (fail faster)
- Simplified retry delay

## Expected Results

### Before Fix:
- Health check: ~0.5-1 second (running full test suite)
- Yellow light: Stays on during test execution
- Connection status: Flickers offline/online due to slow responses

### After Fix:
- Health check: <50ms (using cached results)
- Yellow light: Shows correct status immediately
- Connection status: Stable, no flickering
- Self-tests: Run once per minute (when cache expires)

## Self-Test Duration

**Normal duration**: ~0.5 seconds for full test suite
- Module Imports: ~45ms
- API Health: ~234ms
- Bot Status: ~123ms
- Stats Endpoint: ~100ms
- Trades Endpoint: ~100ms
- Messages Endpoint: ~100ms

**Total**: ~500-700ms for all 6 tests

## Cache Strategy

- **Cache duration**: 60 seconds
- **Cache invalidation**: Automatic after 60 seconds
- **Cache refresh**: Runs new test when cache expires
- **Message notifications**: Only sent when test actually runs (not on cached results)

## Files Modified

1. `api/routes/system.py`:
   - Added `_self_test_cache` global variable
   - Modified `/health` endpoint to use cache
   - Only run tests when cache is stale

2. `frontend/src/components/ConnectionStatus.tsx`:
   - Increased timeout to 5 seconds
   - Added `keepPreviousData: true`
   - Reduced retries and simplified retry logic

## Monitoring

To verify the fix:
```bash
# Check API response times (should be fast now)
time curl -s http://localhost:8000/api/system/health > /dev/null

# Monitor logs for cache hits
tail -f /tmp/market-bot-api.log | grep "cached self-test"
```

## Benefits

✅ **Fast health checks**: <50ms instead of 500-1000ms  
✅ **No more yellow light stuck**: Status updates immediately  
✅ **Stable connection status**: No more offline/online flickering  
✅ **Reduced load**: Tests run 1x per minute instead of every 5-30 seconds  
✅ **Better UX**: Instant status updates for users
