# Integration Test Suite Documentation

## Overview

This document describes the integration test suite for the Market Pie5 Bot GUI and Backend connection.

## Test Files

### 1. `test_api_integration.py`
**Purpose:** Comprehensive API endpoint testing

**Tests:**
- Health check endpoint
- Root endpoint
- Bot status endpoint
- Bot mode endpoint (POST)
- Stats endpoint
- Messages endpoint
- Trades endpoint
- System endpoint
- CORS configuration
- WebSocket connection

**Usage:**
```bash
python3 test_api_integration.py
```

**Expected Output:**
- ✓ for passing tests
- ✗ for failing tests
- ⚠ for warnings (expected failures)

### 2. `test_frontend_integration.sh`
**Purpose:** Frontend server and proxy testing

**Tests:**
- Frontend server accessibility
- API reachability
- CORS headers
- Vite proxy configuration
- WebSocket endpoint (if websocat installed)

**Usage:**
```bash
./test_frontend_integration.sh
```

### 3. `debug_api_connection.py`
**Purpose:** Detailed API connection diagnostics

**Tests:**
- Port availability
- HTTP connection
- Health endpoint
- CORS configuration
- Bot status endpoint

**Usage:**
```bash
python3 debug_api_connection.py
```

### 4. `restart_and_test_gui.sh`
**Purpose:** Complete restart and test workflow

**Actions:**
1. Stops existing services
2. Verifies ports are free
3. Starts API server
4. Starts Frontend server
5. Runs integration tests
6. Provides summary

**Usage:**
```bash
./restart_and_test_gui.sh
```

## Common Issues and Solutions

### Issue 1: API Not Accessible
**Symptoms:**
- `curl: (7) Failed to connect`
- Port 8000 not in use

**Solutions:**
1. Check if API process is running: `ps aux | grep uvicorn`
2. Check API logs: `tail -f /tmp/market-bot-api.log`
3. Restart API: `./restart_and_test_gui.sh`

### Issue 2: Frontend Not Accessible
**Symptoms:**
- `curl: (7) Failed to connect`
- Port 5173 not in use

**Solutions:**
1. Check if frontend process is running: `ps aux | grep vite`
2. Check frontend logs: `tail -f /tmp/market-bot-frontend.log`
3. Restart frontend: `cd frontend && npm run dev`

### Issue 3: 503 Service Unavailable
**Symptoms:**
- API returns 503 for `/api/stats`, `/api/messages`

**Explanation:**
- This is **EXPECTED** when bot instance is not available
- Frontend should handle 503 gracefully
- Bot instance becomes available when bot is started

**Solutions:**
- Start bot via API: `POST /api/bot/start`
- Or wait for bot to initialize automatically

### Issue 4: CORS Errors
**Symptoms:**
- Browser console shows CORS errors
- API requests blocked

**Solutions:**
1. Verify CORS configuration in `api/main.py`:
   ```python
   allow_origins=[
       "http://localhost:5173",
       "http://localhost:3000",
   ]
   ```
2. Check that frontend URL matches allowed origins
3. Restart API after CORS changes

### Issue 5: Import Errors
**Symptoms:**
- `ImportError: cannot import name 'get_bot_instance'`
- API fails to start

**Solutions:**
- Ensure all routes import from `api.utils`, not `api.main`
- Check files: `api/routes/*.py`
- All should have: `from api.utils import get_bot_instance`

## Test Results Interpretation

### All Tests Pass ✓
- API and Frontend are working correctly
- Connection between them is established
- Ready for use

### Some Tests Fail ✗
- Check specific test output
- Review error messages
- Check logs for details
- Fix issues and re-run tests

### 503 Errors (Expected)
- Bot instance not available
- This is normal if bot hasn't started
- Not a critical issue
- Frontend should handle gracefully

## Continuous Testing

### Manual Testing
Run tests after:
- Code changes to API routes
- Frontend API client changes
- CORS configuration changes
- Service restarts

### Automated Testing
Consider adding to CI/CD:
```bash
# In CI/CD pipeline
./restart_and_test_gui.sh
```

## Troubleshooting Checklist

- [ ] API process is running (`ps aux | grep uvicorn`)
- [ ] Frontend process is running (`ps aux | grep vite`)
- [ ] Port 8000 is listening (`lsof -i :8000`)
- [ ] Port 5173 is listening (`lsof -i :5173`)
- [ ] API health check works (`curl http://localhost:8000/api/health`)
- [ ] Frontend is accessible (`curl http://localhost:5173`)
- [ ] No import errors in API logs
- [ ] CORS headers are present
- [ ] WebSocket can connect (if needed)

## Next Steps

1. Run `./restart_and_test_gui.sh` to restart and test
2. Review test output for any failures
3. Fix any identified issues
4. Re-run tests to verify fixes
5. Check browser console for frontend errors

---

**Status:** ✅ Test suite ready for use
