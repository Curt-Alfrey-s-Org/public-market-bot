# Analysis: Self-Tests, Logs, Timers, Debug Logs

Analysis of self-tests, logs, timers, and debug logging for errors and improvements. Applied fixes and recommendations are listed below.

---

## 1. Self-Tests

### Errors fixed

- **Health / startup self-test messages never appeared on Dashboard**  
  The health endpoint and API startup event used `bot.add_message(...)` and `hasattr(bot, 'add_message')`. The bot exposes `stored_messages.add_message`, not `add_message`.  
  **Fix:** Use `bot.stored_messages.add_message(...)` and `hasattr(bot, 'stored_messages')` in both `api/routes/system.py` (health) and `api/main.py` (startup event).

- **Reports route not covered by self-tests**  
  Startup and health “Module Imports” self-tests imported routes but did not include `reports`.  
  **Fix:** Added `reports` to the import list in `api/main.py` startup and `api/routes/system.py` `_run_internal_self_tests()`.

- **selftest_debug.log written without UTF-8**  
  `_log_selftest_run` opened the file with `open(..., "w")`, which can cause encoding issues on some systems.  
  **Fix:** Use `open(debug_path, "w", encoding="utf-8")`.

### Improvements (no code change)

- **Run Tests success logic:** `success` is `returncode == 0 or failed == 0`. If the runner exits non-zero (e.g. warnings) but parsed `failed == 0`, the API still returns success. Consider treating `returncode != 0` as failure unless you explicitly want “warnings only” to be success.
- **Startup vs health tests:** Startup runs a subset of checks; health runs internal + optional HTTP tests. Keeping them in sync (same module list, same structure) avoids confusion.

---

## 2. Logs

### Current behavior

- **trading_bot.log:** API adds a `FileHandler` in `api/main.py` so all API and bot-thread logs go to `trading_bot.log`. The Logs page reads this file.
- **Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s` with `datefmt='%Y-%m-%d %H:%M:%S'` (no milliseconds).
- **Logs route** (`api/routes/logs.py`): Reads the file, parses lines with `split(' - ', 3)` (timestamp - logger - level - message), supports filter/sort/tail.

### Improvements (optional)

- **Large files:** Reading the whole file can be slow for very large `trading_bot.log`. For a future improvement, consider reading the last N bytes or using a tail-friendly read when `tail=True`.
- **Parsing robustness:** If a log line contains ` - ` in the message, the parser can mis-split. Acceptable for current format; if you add more structured logging, consider a regex or a format that escapes delimiters.

---

## 3. Timers (BOT_TIMING)

### Current behavior

- **BOT_TIMING=true:** Bot loop and `get_strategy_signal` record timings; one line per cycle is logged and `bot.last_cycle_timings` is set (and exposed by `/api/reports/decisions`).
- **Scope:** `_time` is only imported and used when `timing_enabled` is True, so no overhead when disabled.
- **Breakdown:** Per-symbol `ohlcv_s`, `strategy_s`, `price_s` are appended to `bot._cycle_signal_breakdown` and summed for the log line.

### Improvements (optional)

- **Expose last_cycle_timings in status:** If the Dashboard or System page should show “Last cycle: Xs (ohlcv Ys, strategy Zs, price Ws)”, add `last_cycle_timings` to `/api/bot/status` or document that it is available under `/api/reports/decisions`.
- **Doc:** Mention in SELFTEST_LOGS.md or USER_GUIDE that setting `BOT_TIMING=true` and checking logs (and optionally the decision report) is the way to find bottlenecks.

---

## 4. Debug Logs

### Current behavior

- **LOG_LEVEL=DEBUG:** More verbose logging; full-run self-test output (last 50 lines) is logged at DEBUG when `_log_selftest_run` runs.
- **Copilot debug logger** (`copilot_debug_logger.py`): Controlled by `COPILOT_DEBUG_MODE`, writes JSONL to `logs/copilot_debug_<session>.jsonl`. Separate from `trading_bot.log`.
- **selftest_debug.log:** Written on Run Tests failure or when stderr is present; UTF-8 now.

### Improvements (optional)

- **Document separation:** In USER_GUIDE or a short “Debugging” section, state: (1) `trading_bot.log` = main app + API + bot; (2) `selftest_debug.log` = full-run stdout/stderr on failure; (3) `logs/copilot_debug_*.jsonl` = Copilot debug traces when enabled.
- **Copilot logger errors:** If the log directory is not writable, the logger disables itself and logs once; no further handling required.

---

## 5. Summary of code changes

| Area        | File                      | Change |
|------------|---------------------------|--------|
| Self-tests | `api/routes/system.py`    | Health: use `bot.stored_messages.add_message` and `hasattr(bot, 'stored_messages')`. |
| Self-tests | `api/routes/system.py`    | Internal self-tests: add `reports` to module imports. |
| Self-tests | `api/routes/system.py`    | `_log_selftest_run`: write `selftest_debug.log` with `encoding="utf-8"`. |
| Self-tests | `api/main.py`             | Startup: use `bot.stored_messages.add_message` and `hasattr(bot, 'stored_messages')`. |
| Self-tests | `api/main.py`             | Startup Module Imports: add `reports` to route imports. |

---

## 6. Decision Report: “not yet evaluated” for several minutes

### Cause

The report shows 16 candidates, cycle 1, and reason “not yet evaluated” when the bot is running but **no symbol has finished evaluation yet**. The first symbol’s `get_strategy_signal(symbol)` does:

1. **OHLCV fetch** – `_fetch_ohlcv_for_strategy(symbol)` → yfinance `Ticker(symbol).history(period='3mo')` (network call).
2. **Strategy** – `generate_combined_signal(df)`.
3. **Price/volume** – `get_stock_price(symbol)` → another yfinance call.

If the first call hangs (no timeout), the loop never updates `candidate_decisions`, so the report stays “not yet evaluated” for as long as the hang.

### Fixes applied

- **yfinance timeout:** At main.py load, yfinance is patched to use a `requests.Session` with **timeout** (default **60s**, env `YFINANCE_TIMEOUT_SECONDS`). After 60s the request fails, the symbol gets reason “error” or “insufficient data”, and the loop moves on so the report fills in.
- **Progress logging:** Before each symbol we log:  
  `Evaluating symbol 1/16: SYMBOL (fetching OHLCV and price — may take 1–2 min)`  
  so the **Logs** page shows that the bot is working.
- **Report API:** Added `evaluated_count` and `cycle_in_progress_no_data` (true when cycle ≥ 1 and no symbols evaluated yet).
- **Decision Report UI:** When `cycle_in_progress_no_data` is true, a banner explains that the first evaluation can take 1–2 minutes and suggests checking Logs. Header shows “X evaluated” when available.

### Optional tuning

- **`YFINANCE_TIMEOUT_SECONDS`** (default 60): Increase if 60s is too short for your network; decrease if you want to fail faster and move on.

---

## 7. How to use this

- **Self-test messages on Dashboard:** After these fixes, when health or startup self-tests run, a summary line is added to the bot’s stored messages (Dashboard activity) when the bot instance exists.
- **Analyzing failures:** Use `[SELFTEST]` in `trading_bot.log` and `selftest_debug.log` as described in `docs/SELFTEST_LOGS.md`.
- **Bottlenecks:** Set `BOT_TIMING=true`, restart the bot, run a few cycles, then check logs (and optionally `/api/reports/decisions` → `last_cycle_timings`) for the next bottlenecks.
