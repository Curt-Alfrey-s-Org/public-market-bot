# Self-Tests, Logs, and Bot Mode — Analysis & Fixes

## Summary

Analysis of self-tests, all logs, and current bot mode led to the following fixes so behavior is consistent and the GUI matches the API.

---

## 1. Self-Tests

### What exists

- **Startup self-tests** (`api/main.py`): Run when the API starts (syntax check, bot manager init, module imports, app structure, routes, CORS, shutdown endpoint, system endpoint). Results are logged to `trading_bot.log`; if the bot is running, a summary is added to `stored_messages`.
- **HTTP self-tests** (`api/routes/system.py`): Run in a background thread a few seconds after startup; call health, stats, etc. Results are cached and shown on the System page.
- **Full suite** (`tests/runner.py`): Import validation, API endpoints, bot integration, error patterns, E2E critical path, GUI data/visual/interactions. Requires the API to be running for most tests; if the API is not available, many tests are skipped (not failed).

### Fixes

- **Startup self-test when bot is None**: The code only calls `bot.stored_messages.add_message(...)` when `bot and hasattr(bot, 'stored_messages')`, so no change was required. At startup the bot is not created yet, so the message is simply not added.
- **Mode in tests**: Bot mode is now normalized (see below) so status and Mode Selector stay in sync.

### How to run

- Start API: `./start_api.sh`
- Run full suite: `python3 tests/runner.py --api-url http://localhost:8000`
- Run tests from GUI: System → Run Tests (requires bot stopped)

---

## 2. Logs

### What exists

- **`trading_bot.log`**: Written by `api/main.py` (root logger `FileHandler`). Contains API and bot logs. Level comes from `LOG_LEVEL` (default INFO).
- **Logs API** (`api/routes/logs.py`): Serves log lines with filters (level, logger, search) and sort (timestamp, level, logger). Used by the Logs page.
- **`selftest_debug.log`**: Written by `api/routes/system.py` when the full test run fails or has stderr; used for analyzing self-test failures.

### Fixes

- **Log file path**: The logs route now uses the same project root as `api/main.py` via `Path(__file__).resolve().parent.parent.parent / "trading_bot.log"`, so the log file path is consistent regardless of process cwd.
- **Path type**: The logs route uses `Path` and `str(log_file)` in the response so the path is unambiguous and consistent.

---

## 3. Bot Mode

### What existed

- **API** returned `mode = 'dry_run'` when `DRY_RUN_MODE=true`.
- **Frontend ModeSelector** uses values: `sandbox`, `live`, `yfinance`, `dryrun-live`.
- So when dry-run was set, the API said `dry_run` and no Mode Selector button was active (value mismatch).

### Fixes

- **API** (`api/routes/bot.py`): When deriving mode from env (no bot, or fallback), use `'dryrun-live'` instead of `'dry_run'` so it matches the frontend.
- **Bot manager** (`api/bot_manager.py`): `get_bot_status()` now also returns `'dryrun-live'` when `DRY_RUN_MODE=true` for consistency.
- **Frontend** (`BotControls.tsx`): Mode label handles both `dryrun-live` and `dry_run` and displays **Dry Run Live**.

Result: Status bar and Mode Selector show the same mode (including Dry Run Live), and the correct button is highlighted.

---

## 4. Quick Reference

| Area        | Location                    | Notes                                                |
|------------|-----------------------------|------------------------------------------------------|
| Startup tests | `api/main.py` startup_event | Logged to `trading_bot.log`; no crash when bot is None |
| HTTP tests | `api/routes/system.py`      | Cached; Run Tests on System page                    |
| Full suite | `tests/runner.py`           | Run with API up for meaningful results              |
| Log file   | `trading_bot.log` (project root) | Same path from main and logs route              |
| Mode       | API + bot_manager + frontend | `dryrun-live` used everywhere for dry-run mode  |
