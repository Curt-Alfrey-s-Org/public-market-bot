# Startup Self-Test Integration

## Overview

The bot now runs self-tests at startup and displays pass/fail status lights in the GUI menu.

## Features

### 1. Startup Self-Test Runner
**File:** `tests/startup_test.py`

Lightweight test suite that runs quickly at startup:
- Tests 5 critical endpoints (Health, Bot Status, Stats, Trades, Messages)
- Fast execution (< 2 seconds)
- Returns pass/fail status
- Can be run standalone or via API

### 2. API Integration
**File:** `api/main.py`

- **Startup Event**: Runs self-tests when API starts
- Logs results to console
- Doesn't block API startup if tests fail

**File:** `api/routes/system.py`

- **`/api/system/health`** endpoint runs self-tests on demand
- Returns detailed test results
- Used by frontend to display status

### 3. GUI Status Indicators
**File:** `frontend/src/components/Sidebar.tsx`

Status lights in sidebar footer:
- 🟢 **Green (PASS)**: All tests passed
- 🔴 **Red (FAIL)**: Some tests failed
- 🟡 **Yellow (...)**: Testing or unknown

**Features:**
- Auto-refreshes every 30 seconds
- Shows test count (e.g., "4/5 tests passed")
- Animated pulse for active status
- Tooltips on hover

## Usage

### Standalone Test
```bash
# Run startup tests manually
python3 tests/startup_test.py

# JSON output
python3 tests/startup_test.py --json
```

### Via API
```bash
# Get system health (includes self-test results)
curl http://localhost:8000/api/system/health
```

### In GUI
- Status indicator appears automatically in sidebar footer
- Updates every 30 seconds
- Click to view details (if System page shows details)

## Test Coverage

Startup tests verify:
1. ✅ API Health endpoint
2. ✅ Bot Status endpoint
3. ✅ Stats endpoint
4. ✅ Trades endpoint
5. ✅ Messages endpoint

## Benefits

1. **Early Detection**: Issues found immediately at startup
2. **Visual Feedback**: Quick status check in GUI
3. **Non-Blocking**: API starts even if tests fail
4. **Lightweight**: Fast execution (< 2 seconds)
5. **Always Visible**: Status shown in sidebar on all pages

## Status Indicators

### Green (PASS) 🟢
- All 5 tests passed
- System is healthy
- All endpoints accessible

### Red (FAIL) 🔴
- One or more tests failed
- Check logs for details
- May indicate API or bot issues

### Yellow (...) 🟡
- Tests are running
- Or API health endpoint unavailable
- Check API is running

## Integration Points

1. **API Startup**: Tests run automatically when API starts
2. **System Health Endpoint**: Tests run on-demand via `/api/system/health`
3. **Frontend Sidebar**: Displays status with auto-refresh
4. **Logs**: Test results logged to console

## Future Enhancements

- [ ] Click status light to show detailed test results
- [ ] Add individual test status indicators
- [ ] Show last test run time
- [ ] Add manual "Run Tests" button
- [ ] Export test results to file
- [ ] Add test history/trends
