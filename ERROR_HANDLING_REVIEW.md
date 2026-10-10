# Error Handling & Logging Review

## Current State Analysis

### ✅ **What's Working Well**

1. **Backend Error Handling**
   - Most API endpoints have try/except blocks
   - Errors are logged with `logger.error()`
   - HTTPException is used for API errors
   - Some endpoints return empty data instead of 503 (good UX)

2. **Logging Infrastructure**
   - Logging is configured in `api/main.py`
   - Logger instances created in each module
   - Log levels: INFO, WARNING, ERROR

3. **Frontend Error Handling**
   - React Query handles errors in mutations/queries
   - Toast notifications for user feedback
   - Some error boundaries exist

### ⚠️ **Issues Found**

1. **Missing Traceback in Error Logs**
   - Many `logger.error()` calls don't include `exc_info=True`
   - Makes debugging harder

2. **Generic Exception Handling**
   - Many `except Exception as e:` blocks are too broad
   - Should catch specific exceptions

3. **Missing Error Handling**
   - Some operations don't have try/except
   - File operations (reading .env) could fail silently
   - Network operations in frontend need better handling

4. **Insufficient Debug Logging**
   - No DEBUG level logging in dev mode
   - Missing logs for:
     - API request/response details
     - State transitions
     - Mode changes
     - Bot lifecycle events

5. **Frontend Error Boundaries**
   - No React Error Boundaries
   - Unhandled errors crash the entire app

6. **Missing Validation**
   - Some endpoints don't validate input
   - Type checking could be better

## Recommendations

### 1. Enhanced Logging Configuration

Add environment-based log levels:

```python
# api/main.py
import os
import logging

# Set log level based on environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
if os.getenv('DEBUG', 'false').lower() == 'true':
    LOG_LEVEL = 'DEBUG'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

### 2. Add Traceback to All Error Logs

```python
# Instead of:
logger.error(f"Error: {e}")

# Use:
logger.error(f"Error: {e}", exc_info=True)
```

### 3. More Specific Exception Handling

```python
# Instead of:
try:
    # code
except Exception as e:
    logger.error(f"Error: {e}")

# Use:
try:
    # code
except FileNotFoundError as e:
    logger.error(f"File not found: {e}", exc_info=True)
except ValueError as e:
    logger.error(f"Invalid value: {e}", exc_info=True)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

### 4. Add Debug Logging for Dev Mode

```python
# Add debug logs for:
- API request/response (method, path, status, duration)
- Bot state transitions (stopped → starting → running)
- Mode changes
- Trade execution attempts
- Data fetching operations
```

### 5. Frontend Error Boundaries

```typescript
// Add ErrorBoundary component
// Wrap main app sections
// Show user-friendly error messages
```

### 6. Better Frontend Error Handling

```typescript
// Add:
- Network error retry logic
- Timeout handling
- Connection status monitoring
- Error recovery mechanisms
```

## Priority Fixes

### High Priority
1. Add `exc_info=True` to all error logs
2. Add DEBUG logging in dev mode
3. Add React Error Boundaries
4. Better error messages for users

### Medium Priority
5. More specific exception handling
6. Add request/response logging middleware
7. Add validation to API endpoints
8. Better frontend error recovery

### Low Priority
9. Structured logging (JSON format)
10. Log aggregation setup
11. Performance logging
12. Audit logging
