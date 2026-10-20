# Frontend Error Handling Guide

## Overview

This document describes how the frontend handles API errors, particularly 503 Service Unavailable responses.

## Error Handling Strategy

### 1. API Client Interceptor

The `apiClient` in `frontend/src/api/client.ts` has a response interceptor that handles:

- **401 Unauthorized**: Removes auth token from localStorage
- **503 Service Unavailable**: Logs as debug (expected when bot not started)
- **Network Errors**: Logs as error (API not reachable)

### 2. React Query Error Handling

Components using `useQuery` and `useMutation` should handle errors:

```typescript
const { data, error, isLoading } = useQuery({
  queryKey: ['stats'],
  queryFn: async () => {
    const response = await apiClient.get('/api/stats')
    return response.data
  },
  retry: (failureCount, error) => {
    // Don't retry on 503 (expected)
    if (error.response?.status === 503) {
      return false
    }
    // Retry other errors up to 3 times
    return failureCount < 3
  },
  retryDelay: 1000,
})
```

### 3. Component-Level Error Handling

Components should display user-friendly messages:

```typescript
if (error) {
  if (error.response?.status === 503) {
    return <div>Bot is not running. Please start the bot to view stats.</div>
  }
  return <div>Error loading data: {error.message}</div>
}
```

## Common Error Scenarios

### Scenario 1: Bot Instance Not Available (503)

**When it happens:**
- Bot hasn't been started
- Bot is initializing
- Bot crashed

**Frontend behavior:**
- API returns 503
- Interceptor logs as debug (not error)
- Components should show friendly message
- Not treated as critical error

**Example handling:**
```typescript
if (error?.response?.status === 503) {
  return <InfoMessage>Bot is not running. Start the bot to view statistics.</InfoMessage>
}
```

### Scenario 2: API Not Reachable

**When it happens:**
- API server not running
- Network issues
- Firewall blocking

**Frontend behavior:**
- Network error (no response)
- Interceptor logs as error
- Components should show connection error
- Treated as critical error

**Example handling:**
```typescript
if (!error.response) {
  return <ErrorMessage>Cannot connect to API. Please ensure the API server is running.</ErrorMessage>
}
```

### Scenario 3: Invalid Response

**When it happens:**
- API returns unexpected format
- Data parsing fails

**Frontend behavior:**
- Parsing error
- Components should show data error
- May retry automatically

## Best Practices

### 1. Graceful Degradation

Always provide fallback UI when data is unavailable:

```typescript
const { data: stats, error, isLoading } = useQuery(...)

if (isLoading) return <LoadingSpinner />
if (error?.response?.status === 503) return <BotNotRunningMessage />
if (error) return <ErrorMessage error={error} />
if (!stats) return <NoDataMessage />

return <StatsDisplay stats={stats} />
```

### 2. User-Friendly Messages

Don't show technical error messages to users:

```typescript
// ❌ Bad
<div>Error: 503 Service Unavailable</div>

// ✅ Good
<div>Bot is not running. Please start the bot to view statistics.</div>
```

### 3. Retry Logic

Don't retry 503 errors (they won't resolve until bot starts):

```typescript
retry: (failureCount, error) => {
  // Don't retry 503
  if (error.response?.status === 503) return false
  return failureCount < 3
}
```

### 4. Status Indicators

Show connection status to users:

```typescript
const { isConnected } = useWebSocket({ url: 'ws://localhost:8000/ws' })

return (
  <div>
    <ConnectionStatus connected={isConnected} />
    {/* ... rest of UI */}
  </div>
)
```

## Testing Error Handling

### Test 503 Responses

1. Stop bot (or ensure it's not started)
2. Open frontend
3. Navigate to pages that require bot instance
4. Verify friendly error messages appear
5. Verify no console errors (only debug logs)

### Test Network Errors

1. Stop API server
2. Open frontend
3. Verify connection error messages appear
4. Verify console shows connection errors

### Test Recovery

1. Start with bot stopped (503 errors)
2. Start bot via API
3. Verify UI updates automatically
4. Verify errors clear

## Current Implementation Status

### ✅ Implemented

- API client interceptor handles 503 gracefully
- Debug logging for 503 (not error logging)
- Network error logging

### ⚠️ Needs Improvement

- Some components may not handle 503 gracefully
- Need to add user-friendly messages in all components
- Need to add connection status indicators

### 📝 TODO

- [ ] Add error boundaries for React components
- [ ] Add global error handler
- [ ] Add connection status indicator
- [ ] Update all components to handle 503 gracefully
- [ ] Add retry logic with exponential backoff
- [ ] Add offline detection

---

**Status:** ✅ Basic error handling implemented, improvements needed
