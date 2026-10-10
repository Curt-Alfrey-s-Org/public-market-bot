# API Connection & GUI Flickering Fixes

## Issues Identified

### 1. **API Not Responding**
- API process is running but not listening on port 8000
- Health endpoint not responding
- This causes "Cannot connect to API" errors in GUI

### 2. **Button Flickering (Grey/White)**
- **Root Cause**: Multiple components polling the same endpoint every 2 seconds
  - `BotControls` polls `/api/bot/status` every 2s
  - `Dashboard` also polls `/api/bot/status` every 2s
  - This causes duplicate requests and rapid state changes
- When API is slow/unresponsive, button state flickers between loading/not-loading

### 3. **Stats Not Displaying**
- Connection errors not handled gracefully
- Aggressive polling causes errors to accumulate
- No retry logic with exponential backoff

## Fixes Applied

### 1. **Shared Bot Status Hook** ✅
- **File**: `frontend/src/hooks/useBotStatus.ts` (new)
- **Purpose**: Single source of truth for bot status
- **Benefits**:
  - Prevents duplicate polling
  - Shared cache across components
  - Reduced API load
  - Smoother UI updates

### 2. **Reduced Polling Frequency** ✅
- Changed from 2 seconds to 3 seconds
- Added exponential backoff for retries
- Better stale time management

### 3. **Better Error Handling** ✅
- **ConnectionStatus**: Better detection of connection errors
- **StatsOverview**: Improved timeout and network error detection
- **BotControls**: Shows connection error message when API unreachable
- **API Client**: Reduced noise from timeout errors

### 4. **Exponential Backoff** ✅
- Retry delays: 1s, 2s, 4s (max 5s)
- Prevents overwhelming API during connection issues
- Better user experience during temporary outages

## Files Changed

1. `frontend/src/hooks/useBotStatus.ts` - **NEW** - Shared hook
2. `frontend/src/components/BotControls.tsx` - Uses shared hook, shows connection errors
3. `frontend/src/pages/Dashboard.tsx` - Uses shared hook instead of duplicate query
4. `frontend/src/components/ConnectionStatus.tsx` - Better error detection
5. `frontend/src/components/StatsOverview.tsx` - Better timeout/network error handling
6. `frontend/src/api/client.ts` - Reduced timeout error logging

## API Connection Issue

The API process is running but not responding. To diagnose:

```bash
./diagnose_api_connection.sh
```

This will check:
- API process status
- Port binding
- Health endpoint response
- Recent errors
- Process details

## Recommendations

### Immediate Actions

1. **Restart API**:
   ```bash
   pkill -f uvicorn
   ./start_api.sh
   ```

2. **Check API Logs**:
   ```bash
   tail -f trading_bot.log
   ```

3. **Verify Port Binding**:
   ```bash
   sudo lsof -i :8000
   # or
   sudo ss -tlnp | grep 8000
   ```

### Long-term Improvements

1. **Add API Health Monitoring**
   - Periodic health checks
   - Auto-restart on failure
   - Alert on connection loss

2. **Connection State Management**
   - Global connection state
   - Retry with exponential backoff
   - Graceful degradation

3. **Reduce Polling Further**
   - Use WebSocket for real-time updates
   - Only poll when needed
   - Smart polling based on state

## Testing

After fixes, test:

1. **Button Stability**:
   - Start button should not flicker
   - Status should update smoothly
   - No rapid grey/white changes

2. **Connection Errors**:
   - Clear error messages when API down
   - Graceful retry when API recovers
   - No error spam in console

3. **Performance**:
   - Reduced API requests
   - Faster UI updates
   - Better caching

## Expected Behavior

### When API is Running ✅
- Button shows correct state (Start/Stop)
- Stats display correctly
- Connection status shows "Connected"
- Smooth updates every 3 seconds

### When API is Down ⚠️
- Button shows "Cannot connect to API" message
- Stats show connection error
- Connection status shows "Disconnected"
- Retries with exponential backoff
- No flickering or rapid state changes
