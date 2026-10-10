# Decision Report: 16 Tickers but No Data — Analysis & Fix

## What “no data” means

The Decision Report shows **candidates** (symbols to trade) and **decisions** (last evaluation per symbol). “16 tickers but no data” means:

- **candidates** = 16 (from `bot.current_symbols`)
- **decisions** = all rows show signal/action “—”, reason “Pending” (i.e. `bot.candidate_decisions` is empty or not the bot that’s running)

So either the report is reading a **different bot instance** than the one running, or the running bot hasn’t finished evaluating **any** symbol yet.

---

## Root cause: wrong bot instance after Restart (fixed)

### Bug

In `api/utils.py`, `set_bot_instance` used:

```python
bot_instance = bot_instance or bot
```

So:

1. **`set_bot_instance(None)`** (on shutdown) did **not** clear: `bot_instance` stayed the old bot.
2. **`set_bot_instance(new_bot)`** (after Restart) did **not** replace: the old bot was kept.

After **Restart**:

- The **loop** ran the **new** bot (passed to `_run_bot_loop(bot)`).
- The **API** (and thus Decision Report) used **`get_bot_instance()`** → still the **old** bot.
- Old bot had `current_symbols` from the previous run (e.g. 16) but **no new updates** in `candidate_decisions` (new updates went to the new bot).
- Result: report shows 16 candidates and “no data” (no decision rows from the running cycle).

### Fix

In `api/utils.py`, `set_bot_instance` was changed to **always assign**:

```python
def set_bot_instance(bot):
    """Set the global bot instance. Pass None to clear (e.g. on shutdown). Always replace so Restart uses the new bot and Decision Report shows live data."""
    global bot_instance
    bot_instance = bot
    return bot_instance
```

Now:

- **Shutdown** → `set_bot_instance(None)` clears the global.
- **Restart** → new bot is stored and returned by `get_bot_instance()`, so the report and the loop use the **same** bot and decision data.

---

## If you still see “no data” after the fix

Then the **running** bot has not yet written any `candidate_decisions`. That happens only when **no symbol has finished** `get_strategy_signal(symbol)`.

### 1. First symbol still evaluating (normal at start)

- The first call does **OHLCV fetch** (yfinance) and then **price/volume**; that can take **1–2 minutes** per symbol.
- The UI shows: *“Cycle in progress. First evaluation can take 1–2 minutes per symbol…”* when `cycle_in_progress_no_data` is true.
- **Action:** Wait a few minutes and refresh; check **Logs** for “Evaluating symbol 1/N: …” to confirm progress.

### 2. yfinance slow or blocking

- OHLCV is fetched in `_fetch_ohlcv_for_strategy()` via `yf.Ticker(symbol).history()`; price in `get_stock_price()`.
- A **session timeout** is set (e.g. `YFINANCE_TIMEOUT_SECONDS`, default 60s) in `main.py` so the first symbol doesn’t hang forever.
- **Optional:** Set `GET_STRATEGY_SIGNAL_TIMEOUT_SECONDS=90` (or 120) in `.env`. The bot loop will run each symbol’s `get_strategy_signal` with that timeout; if a symbol exceeds it, the report shows reason **timeout** and the loop continues. So the Decision Report keeps filling in even when one symbol is slow.
- **Action:** Ensure network is OK; if needed increase `YFINANCE_TIMEOUT_SECONDS` or check firewall/proxy.

### 3. Settings that affect “enough data” for a decision

These are read at runtime (and after Restart, `.env` is reloaded in `start_bot()`), so GUI changes apply after **Restart**:

| Setting | Role | Effect on “no data” |
|--------|------|----------------------|
| **STRATEGY_MIN_BARS** | Min OHLCV bars for strategy | If yfinance returns fewer bars, `get_strategy_signal` returns HOLD and the loop still writes a decision. So this doesn’t leave the report empty; it only affects signal quality. |
| **PRICE_SOURCE** | `realtime` vs `last_close` | `last_close` uses OHLCV last close/volume (no extra price fetch). `realtime` uses `get_stock_price()` (yfinance) — can be slow. |
| **ENABLE_ML_SIGNAL_FILTER** | ML filter on BUY/SELL | Can change signal to HOLD; the loop still records a decision. |
| **ML_SIGNAL_FILTER_MIN_CONFIDENCE** / **MIN_WIN_PROB** | ML thresholds | Same as above; don’t prevent decision rows. |

So “no data” is **not** caused by these strategy/ML settings; they only change **what** signal/action/reason appear. Empty report is either wrong bot instance (fixed above) or no symbol has completed evaluation yet.

---

## Code flow (for reference)

1. **Bot start** (`api/bot_manager.py`): `start_bot()` → `shutdown_bot()` → `set_bot_instance(None)` → `initialize_bot_from_main()` → `set_bot_instance(bot)` → `_run_bot_loop(bot)` in a thread.
2. **Loop** (`_run_bot_loop`): loads symbols → `bot.current_symbols = scan_symbols` → each symbol: `get_strategy_signal(symbol)` then `bot.candidate_decisions[symbol] = { … }`.
3. **Report** (`api/routes/reports.py`): `get_bot_instance()` → `current_symbols`, `candidate_decisions`, `current_cycle_number` → one row per candidate, filling from `candidate_decisions.get(symbol)` or “Pending”.

With the fix, step 1 and 3 use the **same** `bot_instance`, so the report shows live data after Restart once at least one symbol has been evaluated.
