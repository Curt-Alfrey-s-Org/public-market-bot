# Enhanced Self-Test System

## Overview

The self-test system has been enhanced to **actually test functionality** rather than just checking if endpoints exist. Tests now:

1. **Click buttons** in the GUI and verify results
2. **Verify actions work** (e.g., bot actually starts when you click Start)
3. **Test complete workflows** (start → verify running → stop → verify stopped)
4. **Verify filters work** (not just that filter endpoints exist)
5. **Test mode changes** and verify they persist

## New Test Module: GUI Interactions

A new `GUIInteractionTest` module uses browser automation (Playwright or Selenium) to:

- **Click Start button** → Verify bot actually starts
- **Click Stop button** → Verify bot actually stops
- **Click mode buttons** → Verify mode actually changes
- **Check stats display** → Verify data is displayed in UI
- **Check trades table** → Verify trades are displayed

### Browser Automation

The test supports:
- **Playwright** (preferred, more modern)
- **Selenium** (fallback)

Install dependencies:
```bash
# Playwright
pip install playwright
playwright install chromium

# Or Selenium
pip install selenium
```

## Enhanced API Tests

API endpoint tests now verify **actual functionality**:

### Bot Control Tests
- `test_bot_start`: Actually starts bot and verifies it's running
- `test_bot_stop`: Actually stops bot and verifies it's stopped
- `test_bot_shutdown`: Actually shuts down bot and verifies cleanup

### Filter Tests
- `test_trades_filters`: Verifies filters actually filter (not just return 200)
- `test_logs_filters`: Verifies search and level filters work correctly

### Mode Change Test
- `test_bot_mode_change`: Actually changes mode and verifies:
  - Mode endpoint returns correct mode
  - Mode is persisted to `.env` file
  - Environment variables are updated

## Running Enhanced Tests

```bash
# Run all tests (including GUI interactions)
python3 tests/runner.py

# Run with browser automation
# (Will skip if browser not available)
python3 tests/runner.py --api-url http://localhost:8000 --frontend-url http://localhost:5173
```

## Test Results

Tests now report:
- ✅ **PASS**: Action worked correctly
- ❌ **FAIL**: Action didn't work (e.g., clicked Start but bot didn't start)
- ⚠️ **WARN**: Partial success or non-critical issue
- ⏭️ **SKIP**: Test skipped (e.g., browser not available)

## Example Test Output

```
Running: GUI Interactions
================================================================================
✓ Bot Start Button: PASS
  Clicked Start button, verified bot is running

✗ Bot Stop Button: FAIL
  Clicked Stop but bot is still running. Status: {'running': True}

✓ Mode Change Button: PASS
  Mode changed to yfinance, verified in .env file

✓ Stats Display Updates: PASS
  Stats are displayed in UI

✓ Trades Table Displays: PASS
  Trades table visible with 5 trades
```

## What Gets Tested

### Backend Tests
- ✅ Endpoints return correct status codes
- ✅ **Actions actually work** (start/stop/shutdown)
- ✅ **Filters actually filter** (not just return 200)
- ✅ **Mode changes persist** to .env file

### Frontend Tests
- ✅ **Buttons are clickable** and work
- ✅ **Actions have results** (bot starts when clicking Start)
- ✅ **Data displays** in UI (stats, trades, etc.)
- ✅ **Mode changes** update UI

## Browser Automation Notes

- Tests will **skip** if browser automation is not available
- Tests run in **headless mode** (no visible browser window)
- Tests **clean up** browser instances after completion
- Tests handle **timeouts** and **element not found** gracefully

## Future Enhancements

- [ ] Test form submissions (settings changes)
- [ ] Test navigation between pages
- [ ] Test real-time updates (WebSocket)
- [ ] Test error handling in UI
- [ ] Test responsive design
- [ ] Screenshot comparison for visual regression
