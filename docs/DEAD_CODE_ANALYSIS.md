# Market Pie5 Bot - Dead/Unnecessary Code Analysis

**Generated:** 2026-02-03  
**Scope:** Root-level scripts, redundant tests, obsolete utilities

---

## 1. Redundant Test Files (Root vs tests/)

The project has **~120+ test_*.py** files in the **root** and a structured **tests/** directory. Many root tests duplicate or overlap with `tests/backend/` and `tests/frontend/`.

| Category | Root Files | Canonical Location | Recommendation |
|----------|------------|-------------------|----------------|
| Imports | (none) | tests/backend/test_imports.py | Keep tests/ only |
| Yfinance | test_yfinance_*.py | tests/backend/test_yfinance_mode.py, test_yfinance_regression.py | Consolidate into tests/ |
| API | test_api_*.py | tests/backend/test_api_endpoints.py | Consolidate |
| Bot integration | test_bot_*.py, test_trading_bot.py | tests/backend/test_bot_integration.py | Consolidate |
| GUI | test_gui_*.py | tests/frontend/test_gui_*.py | Consolidate |
| Short selling | test_short_selling.py | tests/backend (referenced in run_2) | Move to tests/ or keep if run_2 depends on root |
| Strategy/signals | test_strategy_signals.py, test_strategies_comprehensive.py | (in root) | Move to tests/backend/ |
| Order types | test_order_type_configuration.py, test_order_payload_builder.py | (in root) | Move to tests/backend/ |

**run_comprehensive_tests.py** references both root and tests/ — this creates duplication.

---

## 2. Demo Scripts (demo_*.py)

**~30 demo_*.py** files in root. These appear to be one-off demos or validation scripts, not part of the main test suite.

| File | Purpose | Status |
|------|---------|--------|
| demo_async_startup.py | Async startup demo | Likely obsolete if async is in main |
| demo_backtest_*.py | Backtest demos | Consider moving to examples/ |
| demo_stock_screener_*.py | Screener demos | Likely obsolete |
| demo_sentiment_*.py | Sentiment demos | Likely obsolete |
| demo_email_alert.py | Email alert demo | One-off |
| demo_*.py (others) | Various feature demos | Review individually |

**Recommendation:** Move to `examples/` or `scripts/demos/`; archive or delete if no longer needed.

---

## 3. Verify Scripts (verify_*.py)

**~15 verify_*.py** files. One-off verification scripts, often created to validate a specific fix.

| File | Purpose | Status |
|------|---------|--------|
| verify_async_startup.py | Verify async startup fix | One-off |
| verify_yfinance_fix.py | Verify yfinance fix | One-off |
| verify_selftest_system.py | Verify selftest | Use tests/runner.py instead |
| verify_* (others) | Various verifications | Consolidate into single `scripts/verify_all.py` or remove |

**Recommendation:** Keep only if actively used; else archive or remove.

---

## 4. Duplicate/Obsolete Utilities

| File | Issue | Recommendation |
|------|-------|----------------|
| run_all_tests.py | Overlaps run_comprehensive_tests.py, tests/runner.py | Prefer run_comprehensive_tests.py or tests/runner.py |
| run_unittest.py | Ad-hoc unittest runner | Use pytest or run_comprehensive_tests |
| run_integration_test.py | Single integration test | Merge into tests/ |
| run_screener_test.py | Screener test | Move to tests/ |
| restart_api.py, restart_api_simple.py | API restart | Keep one (e.g., scripts/restart_api.sh) |
| start_bot_*.py (multiple) | Bot startup variants | Consolidate to start_web_gui.sh or one script |
| check_bot_*.py (multiple) | Bot status checks | Consolidate to diagnose_bot_status.py |
| deploy_*.py (deploy_and_test, deploy_and_verify, deploy_bot_fix, etc.) | Various deploys | Consolidate to scripts/deploy.sh |

---

## 5. Diagnostic/Debug Scripts

| File | Purpose | Status |
|------|---------|--------|
| diagnostic.py | General diagnostics | Keep |
| diagnose_api_connection.sh | API connection check | Keep |
| diagnose_bot_status.py | Bot status | Keep |
| debug_api_connection.py | API debug | Merge with diagnose_* or keep |
| debug_bot.py, debug_positions.py | Bot/position debug | Keep if used |
| env_conflict_checker.py | Env conflicts | Keep |
| collect_errorlogs.py | Error log collection | Keep |

---

## 6. One-Off Fix/Validation Scripts

Files created to validate a specific bugfix. Once the fix is merged, these are often obsolete:

- validate_*.py (validate_trade_fix, validate_short_selling, validate_gui_*, etc.)
- test_*_fix.py (test_max_stock_price_fix, test_shutdown_fix, etc.) — some may be obsolete if the fix is permanent

**Recommendation:** After confirming the fix is in main code, archive or delete.

---

## 7. ML Optimization JSON Files

**~30 ml_optimization_*.json** files in root. These are ML run outputs.

**Recommendation:** Move to `runs/ml_optimization/` or `data/ml_runs/`; add to .gitignore if large/transient.

---

## 8. Summary: Files to Consider Removing or Relocating

| Action | Count | Examples |
|--------|-------|----------|
| **Archive/remove** (one-off verify/validate) | ~20 | verify_async_startup.py, validate_trade_fix.py |
| **Move to tests/** | ~40 | test_strategies_comprehensive.py, test_short_selling.py |
| **Move to examples/** | ~25 | demo_*.py |
| **Consolidate** | ~10 | restart_api*.py, start_bot_*.py, check_bot_*.py |
| **Relocate ml_optimization_*.json** | ~30 | Move to runs/ or data/ |

---

## 9. Canonical Test Entry Points

After cleanup, the recommended ways to run tests:

1. **Self-test (API required):** `python tests/runner.py` or `python run_comprehensive_tests.py`
2. **Unit tests only:** `pytest tests/backend/ -v` (no API)
3. **Core unittests:** `python -m unittest test_order_type_configuration test_strategy_signals test_short_selling test_order_payload_builder -v`
4. **CI:** `pytest tests/ -v --ignore=tests/frontend/` (or run frontend tests in GUI env)

---

## 10. Cleanup Completed (2026-02-03)

- **archive/demos/** — 34 demo_*.py moved
- **archive/verify/** — 12 verify_*.py moved
- **archive/scripts/** — restart_api_simple.py, run_integration_test.py moved
- **runs/ml_optimization/** — ml_optimization_*.json moved from root

Root-level test_*.py kept (referenced by run_2, run_comprehensive_tests, etc.).

---

*Last Updated: 2026-02-03*
