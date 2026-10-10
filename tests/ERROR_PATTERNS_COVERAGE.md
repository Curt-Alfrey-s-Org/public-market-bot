# Error Patterns Test Coverage

## Overview

This document tracks errors that have been encountered and the tests that now catch them to prevent regression.

## Error Patterns Covered

### 1. ✅ Circular Import Errors
**Error**: `ImportError: cannot import name 'get_bot_instance' from partially initialized module 'api.main'`

**Test**: `tests/backend/test_imports.py::test_circular_import_patterns`
- Scans route files for `from api.main import get_bot_instance` pattern
- Catches before runtime

**Test**: `tests/backend/test_imports.py::test_api_main_import`
- Actually tries to import `api.main` to catch circular imports at runtime

### 2. ✅ Mode Showing "Unknown"
**Error**: Mode displayed as "unknown" when bot is stopped

**Test**: `tests/backend/test_error_patterns.py::test_mode_not_unknown_when_stopped`
- Verifies mode is never "unknown"
- Ensures mode is determined from environment variables

**Test**: `tests/backend/test_api_endpoints.py::test_bot_status`
- Verifies mode field exists and is valid

### 3. ✅ Mode Change While Bot Running
**Error**: User could change mode while bot was running

**Test**: `tests/backend/test_error_patterns.py::test_mode_change_blocked_while_running`
- Verifies mode change returns 400 error when bot is running
- Checks error message indicates mode change is blocked

### 4. ✅ System Endpoint Structure Mismatch
**Error**: System page showed "Something went wrong" - backend returned nested structure, frontend expected flat

**Test**: `tests/backend/test_error_patterns.py::test_system_endpoint_structure`
- Verifies all required fields exist at top level
- Checks field types match frontend expectations

**Test**: `tests/backend/test_api_endpoints.py::test_system_endpoint`
- Verifies system endpoint returns correct structure

### 5. ✅ Settings Endpoint Missing Fields
**Error**: Settings page showing nothing - likely missing fields

**Test**: `tests/backend/test_error_patterns.py::test_settings_endpoint_returns_all_fields`
- Verifies all required settings fields are returned
- Checks field types are correct

**Test**: `tests/backend/test_api_endpoints.py::test_settings_endpoint`
- Verifies settings endpoint returns all required fields

### 6. ✅ User-Facing Error Messages
**Error**: Error messages were showing to users in GUI

**Test**: `tests/backend/test_error_patterns.py::test_api_response_has_no_error_messages`
- Scans API responses for user-facing error messages
- Ensures errors use status codes instead of messages

### 7. ✅ Import Validation
**Error**: Various import errors preventing API startup

**Tests**: `tests/backend/test_imports.py`
- `test_circular_import_patterns` - Pattern detection
- `test_api_main_import` - Runtime import test
- `test_route_imports` - Individual route imports
- `test_utils_import` - Utils module validation
- `test_bot_manager_import` - Bot manager import
- `test_critical_modules_initialization` - Full integration

### 8. ✅ GUI Interaction Failures
**Error**: Self-test only checked for button presence, not actual functionality

**Tests**: `tests/frontend/test_gui_interactions.py`
- `test_bot_start_button` - Actually clicks start and verifies bot runs
- `test_bot_stop_button` - Actually clicks stop and verifies bot stops
- `test_mode_change_button` - Actually changes mode and verifies persistence
- `test_stats_display_updates` - Verifies stats are displayed
- `test_trades_table_displays` - Verifies trades table is visible

### 9. ✅ Yfinance regression (recently found)
**Errors**: (1) When `SCHWAB_API_ENABLED=off`, `record_trade` uses mode `api_disabled` not `yfinance_sim` — tests that need `yfinance_sim` must patch env. (2) `save_trade_history` metadata `mode` is env-derived (api_disabled/sandbox/simulation/live), not per-trade. (3) Bot loads trades from DB on init; tests that assert exact trade count or filter by mode must set `bot.trade_history = []` first or counts are wrong.

**Tests**: `tests/backend/test_yfinance_regression.py`
- `test_record_trade_mode_api_disabled_when_schwab_off` - Documents contract: when API off, mode is `api_disabled`
- `test_save_trade_history_metadata_mode_in_allowed_set` - metadata `mode` must be in allowed set
- `test_trade_filter_count_requires_isolated_history` - When testing filter counts, isolate `trade_history` first

**Also**: `test_yfinance_sim.py` (trade_mode_tagging, separate_trade_filtering, save_trade_history) — isolate `trade_history` and patch `SCHWAB_API_ENABLED=on` when asserting `yfinance_sim` tagging.

## Error Patterns Not Yet Covered

### 1. ⚠️ API Connection/Port Binding Errors
**Error**: `PermissionError: [Errno 1] Operation not permitted` during port binding

**Status**: System-level issue, difficult to test programmatically
**Recommendation**: Document in diagnostic scripts

### 2. ⚠️ GUI Flickering/Refreshing
**Error**: GUI flickering due to aggressive polling

**Status**: Fixed by reducing polling intervals
**Recommendation**: Add test for polling intervals in frontend tests

### 3. ⚠️ Native Browser Popups
**Error**: Native `window.confirm()` and `alert()` dialogs appearing

**Status**: Fixed by replacing with custom `ConfirmDialog` component
**Recommendation**: Add test to verify no native popups in frontend code

### 4. ⚠️ Duplicate Browser Tabs
**Error**: Bot opening 2 tabs in browser

**Status**: Fixed by disabling Vite auto-open and checking for existing tabs
**Recommendation**: Add test to verify only one browser tab opens

### 5. ⚠️ Shutdown Server Not Working
**Error**: Shutdown server button not actually shutting down server

**Status**: Fixed by using background thread with SIGTERM
**Recommendation**: Add test for shutdown server functionality (difficult - would kill test process)

## Test Coverage Summary

| Error Category | Tests | Coverage |
|---------------|-------|----------|
| Import Errors | 6 tests | ✅ Complete |
| API Structure | 2 tests | ✅ Complete |
| Mode Detection | 2 tests | ✅ Complete |
| Mode Changes | 1 test | ✅ Complete |
| Settings | 2 tests | ✅ Complete |
| Error Messages | 1 test | ✅ Complete |
| GUI Interactions | 5 tests | ✅ Complete |
| Connection Issues | 0 tests | ⚠️ System-level |
| GUI Flickering | 0 tests | ⚠️ Fixed in code |
| Browser Popups | 0 tests | ⚠️ Fixed in code |
| Duplicate Tabs | 0 tests | ⚠️ Fixed in code |

## Adding New Tests

When a new error is found:

1. **Fix the error**
2. **Add a test** in `tests/backend/test_error_patterns.py` or appropriate module
3. **Document the error** in this file
4. **Verify test fails before fix** (if possible)
5. **Verify test passes after fix**

## Test Module Structure

```
tests/
├── backend/
│   ├── test_imports.py          # Import validation
│   ├── test_api_endpoints.py     # API endpoint tests
│   ├── test_bot_integration.py   # Bot integration tests
│   ├── test_error_patterns.py    # Previously found errors
│   ├── test_yfinance_mode.py    # Yfinance unit tests (no API)
│   └── test_yfinance_regression.py  # Yfinance regression (no API) ⭐ NEW
├── frontend/
│   ├── test_gui_interactions.py  # GUI interaction tests
│   ├── test_gui_data_points.py   # Data point tests
│   └── test_gui_visual.py        # Visual/accessibility tests
└── runner.py                     # Test runner (includes all modules)
```

## Related Files

- `.cursor/rules/integrate-findings-into-selftest.mdc` - Rule for integrating findings
- `tests/backend/test_error_patterns.py` - Error pattern tests
- `CIRCULAR_IMPORT_FIX.md` - Example error documentation
- `LOG_ANALYSIS_AND_FIXES.md` - Error analysis documentation
