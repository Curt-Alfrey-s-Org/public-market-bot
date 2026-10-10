# Market Pie5 Bot - Log Analysis for Debugging

**Generated:** 2026-02-03  
**Scope:** All logs in market-pie5-bot, api.log, trading_bot.log, selftest_debug.log, alerts.log, test_failures.txt, debug_logs/

---

## Executive Summary

| Log Source | Status | Critical Issues |
|------------|--------|-----------------|
| api.log | ⚠️ | `No module named uvicorn` (when run via system python) |
| trading_bot.log | ✅ | Normal Dash/werkzeug activity, fallback stock universe |
| selftest_debug.log | ⚠️ | API timeout at localhost:8000 during selftest; Import/Yfinance modules pass |
| alerts.log | ⚠️ | SMTP failures, capital floor breaches, live trading credential errors |
| test_failures.txt | ❌ | Many FAIL/ERROR entries; decryption, API priority, date parsing, risk_management |
| debug_logs/run_* | ✅ | Short-selling/order-type tests pass (run_2); run_4/5/6 verification outputs |

---

## 1. api.log

**Location:** `/home/operator/market-pie5-bot/api.log`

**Content:**
```
/usr/bin/python3: No module named uvicorn
```

**Diagnosis:** API was started with system Python (`/usr/bin/python3`) instead of venv. Uvicorn is installed in `venv/`.

**Fix:** Always use `source venv/bin/activate` or `./venv/bin/python -m uvicorn ...` when starting the API.

---

## 2. trading_bot.log

**Location:** `/home/operator/market-pie5-bot/trading_bot.log`

**Findings:**
- Dash web GUI runs on 0.0.0.0:8050
- Rate limiters configured (Alpha Vantage, yfinance)
- Top Performers Watchlist uses **fallback stock universe** (158 stocks) — `Using fallback stock universe`
- Stock screener initialized, swing trade candidate selection runs
- No critical errors in sampled portion

---

## 3. selftest_debug.log

**Location:** `/home/operator/market-pie5-bot/selftest_debug.log`

**Findings:**
- **API not accessible:** `HTTPConnectionPool(host='localhost', port=8000): Read timed out`
- Import Validation: 6/6 passed
- Yfinance Mode: 6/6 passed
- Yfinance Regression: passed
- Bot integration (yfinance mode): passed
- API/Frontend tests depend on API being up — start API before running selftest

**Recommendation:** Ensure API is running (`uvicorn api.main:app --host 0.0.0.0 --port 8000`) before selftest, or increase timeout.

---

## 4. alerts.log

**Location:** `/home/operator/market-pie5-bot/alerts.log`

**Critical Issues:**
1. **SMTP authentication failed** (multiple):
   - `535, b'5.7.8 Username and Password not accepted'`
   - `535, 'Authentication failed'`
   - Cause: Invalid or missing Gmail SMTP credentials in .env

2. **Capital Floor Breach** (expected in testing):
   - Trading paused when capital drops below 10% of starting
   - Trading resumed when capital recovers

3. **Live Trading Error**:
   - `Failed to execute BUY for AAPL: Live mode credentials not configured or invalid`
   - Expected when running in paper/sandbox without live credentials

**Fix:** For email alerts, use App Password for Gmail or fix SMTP_* env vars. For live trading, configure Schwab credentials or ensure paper mode.

---

## 5. test_failures.txt

**Location:** `/home/operator/market-pie5-bot/test_failures.txt`

**Error Categories:**

| Category | Examples |
|----------|----------|
| **Decryption** | `ERROR:web_gui:Failed to decrypt value:` |
| **SMTP** | `ERROR:main:SMTP authentication failed` |
| **API Priority** | `ERROR:api_priority_manager:Failed MEDIUM request failing-request: Test error` |
| **Date parsing** | `ERROR:main:Invalid date format: Unknown datetime string format, unable to parse: invalid-date` |
| **Schwab** | `ERROR:main:[SANDBOX] Authentication failed - invalid or expired API key` |
| **Risk Management** | `ERROR:risk_management:Invalid entry_price: -150.0 (must be positive)` |
| **Config validation** | `ERROR:main:Configuration validation failed with 1 issue(s)` |
| **yfinance** | `ERROR:main:Connection error fetching price for AAPL from Yahoo Finance: Failed to connect` |

**Test Failures:**
- `update_watchlist_data` concurrent/loading flag tests: FAIL
- `web_gui decryption functions`: FAIL
- `SWING_HOLD_MIN_DAYS` default/WARNING tests: FAIL
- Formatting tests (dollar .2f, percentage .1f): FAIL
- Many GUI tests: `skipped 'tkinter not available'` or `skipped 'GUI not available'`

**Recommendations:**
1. Fix web_gui decryption for empty/invalid values — add graceful fallback
2. Add `pytest.ini` coverage as optional (pytest-cov causes CLI errors when missing)
3. Install `requests` in venv (`pip install -r requirements.txt`)
4. Run tests in environment with tkinter for GUI tests, or mark as skip on headless

---

## 6. debug_logs/ (run_2, run_4, run_5, run_6)

**Purpose:** Numbered run outputs for short-selling, screener, live capital, cleanup, Top Performers Feed.

**run_2_results.txt:**
- test_order_type_configuration, test_strategy_signals, test_short_selling, test_order_payload_builder — all `ok`
- Short-selling validation passes

**run_4/5/6:** Verification scripts for live capital, .env2 cleanup, Top Performers Feed refactor.

---

## 7. Comprehensive Test Runner

**Current State (run_comprehensive_tests.py):**
- **17/17 failed** due to:
  1. `pytest.ini` addopts include `--cov=...` — pytest fails with "unrecognized arguments" (pytest-cov not installed or incompatible)
  2. `ModuleNotFoundError: No module named 'requests'` in test_api_integration, test_gui_features
  3. `main.py` imports `requests` — venv may be missing requests

**Fix:**
1. `pip install -r requirements.txt` in venv
2. Make coverage optional in pytest.ini (remove or conditionalize --cov)
3. Ensure venv is activated when running tests

---

## 8. Passing Tests (verified 2026-02-03)

Core unittest-based tests pass with venv:

```bash
cd /home/operator/market-pie5-bot && source venv/bin/activate
python -m unittest test_order_type_configuration test_strategy_signals test_short_selling test_order_payload_builder -v
# Ran 54 tests in ~4s - OK
```

These cover: order types, strategy signals, short selling, order payload builder.

---

## 9. Action Items

| Priority | Action |
|----------|--------|
| High | Install full `pip install -r requirements.txt` in venv (yfinance, pandas, etc.) |
| High | pytest.ini: coverage made optional (done) |
| Medium | Fix web_gui decryption for empty/invalid encrypted values |
| Medium | Document SMTP setup or disable email alerts in dev |
| Low | Add tkinter skip reason for GUI tests on headless servers |
| Low | Consolidate/archive redundant test_*.py files (see DEAD_CODE_ANALYSIS.md) |

---

*Last Updated: 2026-02-03*
