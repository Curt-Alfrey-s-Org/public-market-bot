# GUI Polling Fix - Resolved Glitching Issue

## Problem Identified

**The GUI was glitching, not the API.** The API was working perfectly (all 200 OK responses), but the frontend was making excessive polling requests.

## Root Cause Analysis

From monitoring `/tmp/market-bot-api.log`:
- API was receiving **excessive requests** from the same client (127.0.0.1:52666)
- Multiple rapid-fire requests to `/api/messages?limit=50` 
- All requests were successful (200 OK), but the volume was causing UI glitching

### Polling Intervals Found:
- ❌ **MessageBox**: 1000ms (1 second) - **TOO FREQUENT**
- ❌ **System page**: 2000ms (2 seconds) - **TOO FREQUENT**
- ✅ StatsOverview: 5000ms (5 seconds) - OK
- ✅ ConnectionStatus: 5000ms (5 seconds) - OK
- ✅ Other components: 5000ms (5 seconds) - OK

## Fix Applied

### 1. MessageBox Component (`frontend/src/components/MessageBox.tsx`)
**Before:**
```typescript
refetchInterval: 1000, // Update every second
staleTime: 500,
```

**After:**
```typescript
refetchInterval: 5000, // Update every 5 seconds (reduced from 1s to prevent excessive polling)
staleTime: 3000, // Increased from 500ms to 3s to reduce unnecessary refetches
refetchOnWindowFocus: false, // Don't refetch when window regains focus
```

### 2. System Page (`frontend/src/pages/System.tsx`)
**Before:**
```typescript
refetchInterval: 2000, // Update every 2 seconds
```

**After:**
```typescript
refetchInterval: 10000, // Update every 10 seconds (reduced from 2s to prevent excessive polling)
```

## Expected Results

- ✅ **Reduced API load by ~80%** (from 1-2 requests/second to 1 request every 5-10 seconds)
- ✅ **Smoother GUI experience** - no more flickering/glitching
- ✅ **Less network overhead** - fewer unnecessary requests
- ✅ **API still responsive** - 5-10 second intervals are sufficient for real-time updates
- ✅ **Better performance** - less CPU/memory usage from constant polling

## Monitoring

To verify the fix is working:

```bash
# Monitor API request frequency
tail -f /tmp/market-bot-api.log | grep "messages" | awk '{print $1, $2}' | uniq -c

# Should see much fewer requests now (1 every 5 seconds instead of 1 per second)
```

## Current Polling Intervals (Post-Fix)

| Component | Interval | Status |
|-----------|----------|--------|
| MessageBox | 5000ms (5s) | ✅ Fixed |
| System page | 10000ms (10s) | ✅ Fixed |
| StatsOverview | 5000ms (5s) | ✅ OK |
| ConnectionStatus | 5000ms (5s) | ✅ OK |
| PerformanceChart | 5000ms (5s) | ✅ OK |
| MonthlyReturnsChart | 5000ms (5s) | ✅ OK |
| Trades | 5000ms (5s) | ✅ OK |
| Logs | 5000ms (5s) | ✅ OK |
| Sidebar | 30000ms (30s) | ✅ OK |
| AI page | 30000ms (30s) | ✅ OK |

## Notes

- Messages don't need to update every second - 5 seconds is sufficient for real-time feel
- System metrics don't need to update every 2 seconds - 10 seconds is adequate
- All other components were already at reasonable intervals (5 seconds)
- The fix maintains responsiveness while dramatically reducing load
