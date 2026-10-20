# GUI Crash/Refresh Fixes

## Issues Fixed

### 1. **Infinite Retry Loops** ✅
**Problem**: React Query was retrying failed network requests infinitely, causing the GUI to crash/refresh

**Fix**: 
- Added smart retry logic that stops retrying on network errors
- Network errors (ECONNABORTED, timeout, Network errors) don't retry
- Other errors retry up to 1-2 times with exponential backoff

### 2. **Mode Selection Crashes** ✅
**Problem**: Selecting yfinance mode caused crashes when API was unreachable

**Fix**:
- Added timeout to mode mutation (5 seconds)
- Better error messages for network errors
- Prevents multiple simultaneous mutations
- Closes dialog before mutation to prevent double-clicks

### 3. **Error Boundary Infinite Loops** ✅
**Problem**: ErrorBoundary could trigger infinite error loops

**Fix**:
- Added check to prevent re-triggering errors when already in error state
- Better error logging in dev mode

### 4. **Network Error Handling** ✅
**Problem**: Network errors weren't handled gracefully, causing crashes

**Fix**:
- Added `NetworkErrorHandler` component that shows banner when API is unreachable
- Prevents error spam in console
- Stops polling when network errors occur
- Circuit breaker pattern - stops retrying after network errors

## Changes Made

### 1. **React Query Configuration** (`App.tsx`)
```typescript
retry: (failureCount, error: any) => {
  // Don't retry on network errors
  if (!error.response && (error.code === 'ECONNABORTED' || error.message?.includes('Network'))) {
    return false
  }
  return failureCount < 1
}
```

### 2. **ModeSelector** (`ModeSelector.tsx`)
- Added timeout to API calls
- Better error handling for network errors
- Prevents multiple mutations
- Closes dialog before mutation

### 3. **useBotStatus Hook** (`useBotStatus.ts`)
- Stops polling on network errors
- Smart retry logic
- Prevents error propagation

### 4. **API Client** (`client.ts`)
- Better network error detection
- Prevents error spam
- Adds error metadata for handling

### 5. **NetworkErrorHandler Component** (NEW)
- Shows banner when API is unreachable
- Prevents showing error multiple times
- Auto-dismisses after 30 seconds

### 6. **ErrorBoundary** (`ErrorBoundary.tsx`)
- Prevents infinite error loops
- Better error logging

## How It Works Now

### When API is Running ✅
- Normal operation
- Polling works correctly
- Mode changes work
- No crashes

### When API is Down ⚠️
- Network error banner appears at top
- Polling stops automatically
- Mode selection shows clear error message
- No infinite retries
- No crashes/refreshes
- GUI remains stable

### When API Recovers ✅
- Error banner disappears
- Polling resumes automatically
- All features work normally

## Testing

To test the fixes:

1. **Start API**: `./start_api.sh`
   - GUI should work normally
   - No errors

2. **Stop API**: `pkill -f uvicorn`
   - Network error banner should appear
   - GUI should NOT crash/refresh
   - Mode selection should show error (not crash)

3. **Restart API**: `./start_api.sh`
   - Error banner should disappear
   - GUI should resume normal operation

## Expected Behavior

### Before Fixes ❌
- GUI crashes/refreshes on network errors
- Infinite retry loops
- Mode selection causes crashes
- Console spam with errors

### After Fixes ✅
- GUI remains stable on network errors
- Smart retry logic (no infinite loops)
- Mode selection shows error (no crash)
- Clean error handling
- Network error banner for visibility
