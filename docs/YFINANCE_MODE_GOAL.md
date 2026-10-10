# Yfinance Mode — Goal (From the Code Only)

This describes **what yfinance mode does** in the bot and **what it helps improve**, based only on what the code actually does.

---

## 1. What “yfinance mode” is in the code

**How it’s set**

- **Dashboard:** User selects **Training** (or “yfinance”); `POST /api/bot/mode` with `mode: 'yfinance'` runs.
- **Env:** `SCHWAB_API_ENABLED=off` with paper trading also behaves as yfinance (no Schwab API, paper + yfinance data).
- **Bot state:** `bot.mode = 'yfinance'` and/or `bot.using_yfinance_sim = True` (set when Schwab API is disabled or unavailable and the bot falls back to yfinance).

**What the mode API sets for `mode === 'yfinance'`** (`api/routes/bot.py`)

- `PAPER_TRADING_MODE=true`
- `SCHWAB_SANDBOX_MODE=false`
- `SCHWAB_API_ENABLED=off`
- `WEB_GUI_CONTINUOUS_TRADING=true`
- `WEB_GUI_DEBUG=true`
- `ENABLE_PDT_RULES=true` (PDT is still not enforced because paper mode is true; see `check_pdt_compliance`).

So in code terms, yfinance mode = **paper trading + no Schwab API + continuous trading + debug on**.

---

## 2. What the code does when in yfinance mode

### Data source

- **Prices / volume:** `get_stock_price()` uses **yfinance** (`fetch_real_stock_price`) when Schwab API is disabled. No broker; data comes from the yfinance library (delayed/free).
- **OHLCV for strategies:** `_get_ohlcv_for_symbol()` uses the data fetcher’s yfinance path or `yf.Ticker(symbol).history(...)`.
- **Fallback:** If yfinance fails, the code can use a random price (when `ALLOW_RANDOM_FALLBACK` is true) so the loop doesn’t stop.

So: **yfinance mode = real(ish) market data via yfinance, no broker, no real money.**

### Trading loop timing (`api/bot_manager.py`)

- When `bot.mode == 'yfinance'` or `(PAPER_TRADING_MODE and not SCHWAB_SANDBOX_MODE and SCHWAB_API_ENABLED off)`:
  - `trade_delay = 0` (no delay between symbols in a cycle).
  - `cycle_delay = max(0.5, WEB_GUI_CYCLE_DELAY)` (default 1 s between cycles).
- So the code runs **back-to-back symbol processing and short cycle delays** — i.e. “continuous” trading in the sense of minimal waiting.

### Execution and limits (main.py)

- **Execution:** All orders are **simulated** in `execute_trade_paper_mode()` (no broker orders).
- When `using_yfinance_sim` is True the code **does not enforce**:
  - **Capital floor** — `check_capital_floor()` returns “ok” immediately.
  - **T+1 settlement** — `check_settled_capital_available()` returns “ok” immediately.
  - **Risk threshold** — the check that would skip the trade for “potential_loss > risk_limit” is skipped.
  - **Max open positions** — `can_open_new_position()` is not called; position limit is not applied.
- **PDT:** Already not enforced whenever `PAPER_TRADING_MODE` is true, so in yfinance mode there is no PDT limit in practice.

So: **yfinance mode = no internal “safety” limits (floor, T+1, risk, position count); the loop can keep opening/closing simulated positions as fast as the cycle allows.**

### Auto-configuration when `using_yfinance_sim` is True (`_auto_configure_yfinance_mode`)

- Forces paper trading, sandbox off, Schwab API off.
- Sets `WEB_GUI_CONTINUOUS_TRADING=true` and `WEB_GUI_DEBUG=true`.
- So the rest of the app (GUI, logging) is aligned with “continuous, debug, no broker”.

### Trade recording

- Trades are recorded with `mode: 'api_disabled'` or `'yfinance_sim'` so they can be filtered later (e.g. `get_trades_by_mode('yfinance_sim')`).
- That allows the app to **treat yfinance runs as a distinct dataset** (e.g. for stats, AI analysis, backtests).

---

## 3. What this will help improve and how (from the code only)

- **Collecting trade history without a broker**  
  The bot runs the full pipeline (screener → signals → execute_trade_paper_mode) and records each trade with a yfinance-related mode. So you get a **history of simulated decisions and PnL** driven by yfinance data. That history is what the AI analysis and other features consume (e.g. “at least 10 trades” for AI; see `api/routes/ai.py` and the frontend). So yfinance mode **helps improve** anything that depends on having a **large, no-broker-required sample of trades** (e.g. strategy tuning, AI suggestions).

- **Running the strategy and risk pipeline without limits**  
  Because capital floor, T+1, risk threshold, and position limit are not enforced in yfinance mode, the bot can **run many cycles and many positions** without being stopped by those guards. So you can **stress the strategy and the code path** (screener → signals → allocation → execute_trade_paper_mode) and see more wins/losses and edge cases. That **helps improve** confidence in the **strategy logic and the execution path** before turning on Sandbox or Live.

- **Faster iteration (continuous mode)**  
  With `trade_delay = 0` and short `cycle_delay`, the same strategy and same symbols are evaluated **more often** per unit time. So you get **more trades per hour** than in modes that use larger delays. That **helps improve** how quickly you can **accumulate trade data and test changes** (e.g. after changing strategy or .env).

- **Debug visibility**  
  With `WEB_GUI_DEBUG=true` and the rest of the logging, you can **see why the bot did or didn’t trade** (e.g. HOLD vs BUY/SELL, prices, allocations). So yfinance mode **helps improve** **troubleshooting and tuning** (e.g. fixing “bot not trading” or adjusting filters/strategy).

- **Clear separation from live/sandbox**  
  Trades are tagged by mode (`api_disabled` / `yfinance_sim`). So you can **analyze or export only yfinance runs** and keep them separate from broker-based runs. That **helps improve** **clean datasets for training, reporting, or AI** without mixing real and simulated execution.

---

## 4. Where yfinance mode is in time (timeline)

**Does it trade “last week” or “20 years ago”?**  
**No.** Yfinance mode uses **current (latest) data** from Yahoo Finance, not a fixed past date.

**How the code does it**

- **Execution price / volume:** `get_stock_price()` → `fetch_real_stock_price()` uses `yf.Ticker(symbol)` and then `ticker.fast_info.get('lastPrice')` (or `ticker.info`). That is the **latest available** price (typically last close or current session). No `start_date`/`end_date` or `period` is passed for this call — it’s the **live** last price.
- **Strategy OHLCV:** For signals, the bot uses `_fetch_ohlcv_for_strategy(symbol, period='3mo')`, i.e. the **last 3 months** of daily bars **up to “now”**. So indicators are computed on recent history ending at the current moment.
- **Caching:** Prices are cached per symbol for 60 seconds, so within a short window every symbol is still using “current” data from that window.

So in time: **yfinance mode is “now”** — it trades on **today’s (or latest) numbers**, not last week and not 20 years ago.

**Same timeline for all stocks?**  
**Yes.** Every symbol is queried at the **same real-world time** (or within the same 60s cache window). Each cycle, the bot gets the latest price for each symbol and decides; the next cycle runs seconds later (e.g. `cycle_delay` ~1 s) and again uses the latest data. So all picks are evaluated on the **same real-world timeline**, mimicking **real-world “right now” picking of trades** — the only difference is no real broker and no real money.

**Contrast with backtest mode**

- **Backtest** uses `enable_historical_mode(start_date, end_date)` and `current_sim_date`: it **replays** history day-by-day, with one shared simulation date for all symbols. That’s a different code path (e.g. `backtest_loop()`), not the normal “start bot” / Training (yfinance) mode.
- **Yfinance (Training) mode** never sets `historical_mode`; it always uses the live/latest path above.

---

## 5. Short summary

- **Goal of yfinance mode in code terms:**  
  Run the **same strategy and execution pipeline** as in other modes, but with **yfinance as the only data source**, **no broker**, **no capital/T+1/risk/position limits**, and **minimal delays**, so the bot can **trade continuously** and **record many simulated trades** for learning, testing, and AI/analytics.

- **What it helps improve:**  
  1) **Trade data** for AI and analysis (no broker needed).  
  2) **Strategy and execution testing** under no internal limits.  
  3) **Faster iteration** via continuous, low-delay runs.  
  4) **Debugging and tuning** via debug mode and logging.  
  5) **Clean separation** of yfinance-only trades for reporting or training.
