# Live Production Mode: Flow When Live + Start Are Pressed

Descriptive summary of what happens from **Live** button → **Start** until the bot runs and places (or skips) real trades.

---

## 1. Mode selection (Live button)

- User clicks **Live** on the homepage. `select_mode` sets `selected_mode = 'live'`.
- UI highlights Live; other modes (Sandbox, yfinance Training, Dry-run Live) are unselected.
- No env or bot state changes yet. Start must be pressed to apply.

---

## 2. Start button → control_bot

When **Start** is clicked (and a mode is selected):

1. **Mode check**  
   - If no mode selected → error "Please select a trading mode before starting the bot"; Start does nothing.

2. **Live-specific env overrides**  
   - `PAPER_TRADING_MODE` = `'false'`  
   - `SCHWAB_SANDBOX_MODE` = `'false'`  
   - `SCHWAB_API_ENABLED` = `'on'`  
   - No `DRY_RUN_MODE` (so real orders).

3. **UI → env**  
   - Capital, min/max allocation, risk threshold, position size, capital floor %, max positions, max consecutive losses, trailing/stop/take-profit, dynamic stop, min/max price, min volume, max volatility, partial exit, trading frequency, max symbols, continuous trading, etc. are written to `os.environ`.

4. **Module reload**  
   - `importlib.reload(main_module)` so the bot reads the updated env (including Live settings).

5. **Bot creation**  
   - `TradingBot(total_capital=...)` is instantiated with UI capital (or default).
   - **In live mode**, if `USE_SCHWAB_CAPITAL_IN_LIVE=true` (default), the bot **fetches actual account cash/buying power from Schwab API** and **overrides** `total_capital` with the real account funds. This determines how much trading the bot can do based on actual available capital.

6. **Thread start**  
   - `run_bot_loop` runs in a daemon thread. Logs show "Bot started ... in live mode" and "● Running."

These are **runtime overrides only**; they are not persisted to `.env` unless the user uses "Apply Settings."

---

## 3. Bot loop (run_bot_loop)

The loop runs in a separate thread and keeps running until **Stop** or one cycle in single-cycle mode.

1. **Symbol loading**  
   - If watchlist enabled and non‑empty: use watchlist symbols (by win probability).  
   - Else: if `ENABLE_STOCK_SCREENER` → `load_scan_symbols(use_screener=True)`; otherwise load from file.  
   - Symbols are capped by `MAX_SYMBOLS_TO_TRADE` (from Settings / env).

2. **Trading cycle**  
   - For each symbol (in order):
     - **Price**  
       `get_stock_price(symbol)` → price and volume (or fallback).  
     - **Trade**  
       `execute_trade(symbol, 'BUY', price, volume=volume)`.  
       The **Web GUI always passes `BUY`**; it does not use strategy signals or signal→action mapping.  
     - **Logging**  
       Results are logged; trade log updates only when status is `'simulated'` (not in Live).  
     - **Delay**  
       `time.sleep(2)` between symbols.

3. **Cycle mode**  
   - **Single-cycle** (`WEB_GUI_CONTINUOUS_TRADING` false): one pass over all symbols, then loop exits.  
   - **Continuous**: repeat cycles with `WEB_GUI_CYCLE_DELAY` seconds between them.  
   - **Stop**: at any time, **Stop** sets `stop_event`; the loop exits when it checks it.

---

## 4. execute_trade → Live path

With Live, `PAPER_TRADING_MODE=false` and `SCHWAB_SANDBOX_MODE=false`, so:

- `execute_trade` routes to **`execute_trade_live_mode`** (production Schwab API).
- No sandbox, no local simulation. `DRY_RUN_MODE` is unset, so orders are real.

---

## 5. execute_trade_live_mode (production)

Each `execute_trade(symbol, 'BUY', ...)` in Live goes through this pipeline. Steps are skipped when a check fails (with appropriate status returned).

1. **Action**  
   - Validate action is one of `BUY`, `SELL`, `SHORT`, `COVER`.

2. **Resource throttling**  
   - If CPU/memory/disk/network limits are exceeded, log, apply throttle delay, then continue (or skip depending on implementation).

3. **Credentials**  
   - `_validate_live_mode_credentials()`: ensure required Schwab API credentials are set and not placeholders.  
   - If invalid → error, alert, return; no order.

4. **Capital floor**  
   - `check_capital_floor()`: account value must stay above configured floor.  
   - If breached → trade blocked, return `paused` / `capital_floor_breach`.

5. **Quantity**  
   - Quantity = `min(current_allocation, BOT_MAX_ALLOCATION) / price`.

6. **T+1 settlement (BUY / SHORT)**  
   - `check_settled_capital_available(current_allocation)`: enough settled cash/collateral to open the position.  
   - If not → skip with `t1_settlement_pending`.

7. **Risk**  
   - Potential loss ≈ `current_allocation * BOT_STOP_LOSS_PERCENT`.  
   - If &gt; `BOT_RISK_THRESHOLD * total_capital` → skip, `risk_threshold_exceeded`.

8. **Opens (BUY / SHORT)**  
   - **SHORT**: `can_open_short(allocation, for_live=True)` (margin, max short positions, max short exposure). If not allowed → skip, `short_not_allowed`.  
   - **BUY / SHORT**: `filter_stock(symbol, price, volume)` (price, volume, volatility, etc.). If filter fails → skip, `failed_stock_filter`.  
   - Live currently uses mock volume when real-time volume is unavailable; filter still runs.

9. **Closes (SELL / COVER)**  
   - `check_holding_period(symbol, action)`: minimum hold before exit.  
   - If not met → skip, `holding_period_not_met`.

10. **Order build**  
    - Order type from `BOT_DEFAULT_BUY_ORDER_TYPE` / `BOT_DEFAULT_SELL_ORDER_TYPE` (or override).  
    - Use `order_payload_builder` when available (MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP) with `LIMIT_ORDER_OFFSET_PCT`, `STOP_OFFSET_PCT`, etc.; otherwise LIMIT/MARKET fallback.  
    - Map action → Schwab instruction (BUY/SELL/SHORT_ETC).

11. **DRY_RUN_MODE**  
    - In **Live**, `DRY_RUN_MODE` is false.  
    - If it were true (Dry-run Live): log "would execute," validate payload, return `dry_run_success`, **no API call**.

12. **Schwab API**  
    - Ensure OAuth client exists (`get_client`); if auth fails → error, alert, return.  
    - `schwab_client.place_order(SCHWAB_ACCOUNT_ID, order_payload)`.

13. **Response**  
    - **201/200**:  
      - Parse order ID from `Location` or body.  
      - Log success.  
      - `send_alert` (e.g. "PRODUCTION Trade Executed").  
      - `_add_unsettled_funds` for T+1 tracking.  
      - Return `status: 'success'` (no premature win/loss in trade history).  
    - **Other**:  
      - Log error, send alert, return `status: 'error'` with reason/message.

---

## 6. End-to-end summary

| Stage | What happens |
|-------|----------------|
| **Live + Start** | Env overrides (Live, API on), reload main, create `TradingBot`, start `run_bot_loop` thread. |
| **Loop** | Load symbols (watchlist or screener) → for each symbol: `get_stock_price` → `execute_trade(symbol, 'BUY', ...)`. |
| **Live execution** | Throttle → credentials → capital floor → quantity → T+1 → risk → filter/holding/short checks → build order → **place_order** via Schwab → alert and track unsettled funds on success. |
| **Stop** | User clicks Stop → `stop_event` set → loop exits, "● Stopped." |

So: **Live + Start** runs the bot in production mode. The GUI currently sends **BUY** only (no strategy-based BUY/SELL/SHORT/COVER). Each BUY is validated and, if all checks pass, sent as a **real order** to the Schwab production API. Dry-run Live uses the same pipeline but sets `DRY_RUN_MODE=true` and never calls the API.
