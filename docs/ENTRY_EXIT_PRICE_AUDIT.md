# Entry/Exit Price and Order-Type Audit

**Last Updated:** January 2026  
**Status:** Audit complete; order-types wired; price sources and exit-price logic in place.

---

## Summary

The bot uses a **single price** for both “should we trade?” (strategy) and “at what price?” (execution). That price comes from **current/last market data** (or fallbacks), configurable via **`PRICE_SOURCE`** (`realtime` vs `last_close`). **Exit-price refresh** (`EXIT_REFRESH_PRICE`): optionally re-fetch price immediately before SELL/COVER and use for execution. **Order types** are configurable via env: **`order_payload_builder`** wires LIMIT, MARKET, STOP, STOP_LIMIT, TRAILING_STOP into Schwab live/sandbox orders; **`order_types.py`** concepts (stop, limit, trailing) are used by the builder.

---

## 1. Price source and data flow

### Where the price comes from

| Step | What happens |
|------|----------------|
| **1. Loop** | CLI/GUI calls `get_strategy_signal(symbol)` → returns `(signal, price, volume)`. |
| **2. Strategy** | Signal = BUY/SELL/HOLD from SMA 20/50 (or combined strategies). Price is **not** derived from strategy. |
| **3. Price** | From `get_stock_price(symbol)` **or** last `close` from OHLCV when that fails. |
| **4. Execution** | `execute_trade(symbol, action, price, volume)`. Same `price` is used for sizing, limit (if LIMIT), and P&L. |

### `get_stock_price` priority

1. **Live:** Schwab API (production or sandbox).  
2. **Paper / API disabled:** yfinance.  
3. **Fallback (if allowed):** `generate_random_price()` when yfinance fails.

### `get_strategy_signal` price and **`PRICE_SOURCE`**

- **`PRICE_SOURCE=realtime`** (default): Prefer `get_stock_price(symbol)`; if that raises, use **last `close`** from OHLCV and last `volume`.  
- **`PRICE_SOURCE=last_close`**: Use **last `close`** and last `volume` from OHLCV only; skip `get_stock_price`.

So we use **current/last available price** only. **Strategy-derived** entry/exit levels (e.g. support/resistance, target) remain **deferred**.

---

## 2. How the price is used

### Paper mode (`execute_trade_paper_mode`)

- **Opens (BUY/SHORT):** Allocate `current_allocation`, `quantity = allocation / price`. Simulate fill at `price`.  
- **Closes (SELL/COVER):** `close_position(symbol, price, …)`. P&L uses that exit `price`.  
- **Order type:** Not applied; we always “fill” at the passed-in `price`.

### Live/sandbox (`execute_trade_live_mode`)

- **Opens:** `BOT_DEFAULT_BUY_ORDER_TYPE` (default **LIMIT**). Limit price = `price`.  
- **Closes:** `BOT_DEFAULT_SELL_ORDER_TYPE` (default **MARKET**). No limit price.  
- **Limit orders:** `order_payload['price'] = price` (optionally adjusted by `LIMIT_ORDER_OFFSET_PCT`; see below).

So:

- **Entry:** same `price` used for signal logic and execution (limit or simulated fill).  
- **Exit:** **`EXIT_REFRESH_PRICE`** (env, default `true`): when action is SELL or COVER, CLI/GUI re-fetch price via `get_stock_price` immediately before `execute_trade` and use that for execution; on failure, keep signal-time price. If `false`, exit uses the same price as the signal.

---

## 3. Order types

### Config (env)

- `BOT_DEFAULT_BUY_ORDER_TYPE` → default **LIMIT**.  
- `BOT_DEFAULT_SELL_ORDER_TYPE` → default **MARKET**.  
- Valid: **`LIMIT`**, **`MARKET`**, **`STOP`**, **`STOP_LIMIT`**, **`TRAILING_STOP`**.  
- **`LIMIT_ORDER_OFFSET_PCT`**, **`STOP_OFFSET_PCT`**, **`STOP_LIMIT_OFFSET_PCT`**, **`TRAILING_STOP_ORDER_PCT`** for order-type–specific params.

### `order_payload_builder` and `order_types.py`

- **`order_payload_builder.py`**: Builds Schwab API payloads for MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP. Wired into **`execute_trade_live_mode`**; used when available (fallback: LIMIT/MARKET only).  
- **`order_types.py`**: Domain models (Limit, Stop, Stop-Limit, Trailing Stop, OCO, Bracket). Concepts (e.g. stop vs limit) inform the builder; **OrderManager** / **process_orders** are **not** used for live order placement.

---

## 4. Gaps and next steps

| Gap | Status |
|-----|--------|
| **Single price** | Still one primary price; **PRICE_SOURCE** and **EXIT_REFRESH_PRICE** clarify and improve. |
| **Limit offset** | Addressed by **`LIMIT_ORDER_OFFSET_PCT`**. |
| **`order_types`** | **`order_payload_builder`** wires STOP, STOP_LIMIT, TRAILING_STOP into live flow. |
| **Exit price** | **EXIT_REFRESH_PRICE** refresh-at-exit in place; strategy-derived target/stop **deferred**. |
| **Paper vs live** | Paper fills at `price`; live uses builder-driven order types. |

### Future (deferred)

- **Strategy-derived levels** (e.g. targets, stops) as first-class outputs from strategies.  
- **OrderManager / process_orders** for live flow (optional).

---

## 5. Implemented improvements

- **`LIMIT_ORDER_OFFSET_PCT`** (env, default `0`): Optional offset for **LIMIT** orders. Opens: `price * (1 - offset)`; closes: `price * (1 + offset)`. Cap 0–5%. **Live** only; **paper** uses `price` as-is.  
- **`PRICE_SOURCE`** (`realtime` | `last_close`): Drives **`get_strategy_signal`** price source.  
- **`EXIT_REFRESH_PRICE`** (default `true`): Re-fetch price before SELL/COVER and use for execution.  
- **`order_payload_builder`**: STOP, STOP_LIMIT, TRAILING_STOP with **`STOP_OFFSET_PCT`**, **`STOP_LIMIT_OFFSET_PCT`**, **`TRAILING_STOP_ORDER_PCT`**.

---

## 6. References

- **Price flow:** `get_strategy_signal` (PRICE_SOURCE) → loop (EXIT_REFRESH_PRICE for exits) → `execute_trade` → paper / live.  
- **Order payloads:** `order_payload_builder.build_schwab_order_payload`; **`execute_trade_live_mode`** in `main.py`.  
- **Order type models:** `order_types.py`.
