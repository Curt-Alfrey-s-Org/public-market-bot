# Database and restart recovery design

Design for better DB processes (saved items, settings, filters/sort, trade history) and bot restart recovery so the bot can pick up where it left off after a lost connection.

---

## 1. Current state

| Item | Where it lives | Persisted? | On restart |
|------|----------------|------------|------------|
| **Trade history** | `bot.trade_history` (in-memory) | Optional JSON via `save_trade_history()` | Empty; no load from DB |
| **Positions** | `bot.positions` (in-memory) | No | Empty |
| **Settings** | `.env` file | Yes (API writes .env) | Reloaded from .env |
| **Bot state** | In-memory (current_symbols, no_trade_streak, cycle_number) | No | Fresh load of symbols; cycle 1 |
| **Logs filters/sort** | Frontend state | No | Reset |
| **Decision Report filters/sort** | Frontend state | No | Reset |
| **LogManager** | `log_manager.py` (SQLite `trading_logs.db`) | Yes | Not wired to bot runtime; bot does not write trades to it |

**Gap:** Trades and positions are lost on restart. Bot always starts from a fresh symbol list and cycle 1. No “resume” behavior.

---

## 2. Research summary: recovery window

- **Real-time connections (e.g. WebSocket):** Recovery windows are usually **15 seconds to 2 minutes**. After that, reconnection does not restore prior state; you start a new session.
- **Trading bots:** Best practice is to **persist positions and trade history** so that after any restart (crash, disconnect, deploy) the bot can:
  1. Load last known positions and trade history from DB.
  2. Optionally reconcile with broker (or in sim, trust persisted state).
  3. Decide whether to **resume** (use saved symbol list and cycle state) or **start fresh** (reload symbols, reset cycle) based on **how long ago** the last activity was.

**30-minute rule:** If the bot was last active more than **30 minutes** ago, treating the session as stale and “starting from beginning” (reload symbols from feed/screener, reset cycle count) is reasonable because:
- Market data and “today’s best” lists may have changed.
- Cached no_trade_streak / prospects may be outdated.
- Avoiding stale state is safer than resuming old symbol list and cycle.

**Shorter outages:** If last activity was **within 30 minutes**, resuming (restore `current_symbols`, `no_trade_streak`, cycle_number) lets the bot continue without re-scanning and avoids duplicate work.

---

## 3. Proposed architecture

### 3.1 Trade history

- **Persist:** Every `record_trade()` in `main.py` also writes to a **single source of truth** for trades:
  - Option A: Use existing **LogManager** (SQLite `trading_logs.db`, table `trades`). Bot calls `log_manager.log_trade(...)` from `record_trade()`.
  - Option B: New **trades** table in a dedicated `bot_state.db` (or same DB) with same schema; keep LogManager for backward compat elsewhere.
- **On bot init:** Load `trade_history` from DB (e.g. last N trades or by session/mode) into `bot.trade_history` so the API and stats see history after restart.
- **Settings:** Keep `.env` as source of truth for bot/config; API already persists there. Optional: cache in DB for fast read (lower priority).

### 3.2 Positions

- **Option A (derive):** Don’t store positions in DB; on startup **reconstruct** open positions from trade history (e.g. BUY/SELL and SHORT/COVER pairs per symbol). Simple but requires consistent trade history.
- **Option B (store):** Persist `positions` in a **bot_state** table (e.g. JSON blob or one row per symbol) and update on every trade; on init load into `bot.positions`.

Recommendation: Start with **derive from trade history**; add stored positions later if needed (e.g. for multi-day restarts).

### 3.3 Bot state (resume vs start fresh)

- **Persist:** At end of each cycle (in `bot_manager._run_bot_loop`), save:
  - `last_cycle_at` (timestamp)
  - `current_symbols` (list)
  - `no_trade_streak` (dict)
  - Optionally `cycle_number`
- **Storage:** SQLite table `bot_state` (one row per “session” or latest row) or a JSON file (e.g. `bot_state.json`) in project root.
- **On loop start:**
  - If no saved state: load symbols from feed/screener as today; start cycle 1.
  - If saved state exists:
    - If `now - last_cycle_at <= 30 minutes`: **Resume** — restore `scan_symbols` and `no_trade_streak` (and optionally cycle_number); continue.
    - If `now - last_cycle_at > 30 minutes`: **Start fresh** — reload symbols from feed/screener; reset no_trade_streak; start cycle 1.

Config: `BOT_RECOVERY_WINDOW_MINUTES` (default 30) so the threshold is tunable.

### 3.4 Settings

- **Current:** `.env` + API `get_settings` / `update_settings` that read/write .env. Keep this.
- **Optional later:** DB cache of settings for fast read; .env remains source of truth on disk.

### 3.5 Filters/sort (UI)

- **Logs page:** Persist “View” (preset), Level, Logger, Search, Sort By, Order, Lines, Auto-refresh in **localStorage** (e.g. key `logs_preferences`). On load, restore from localStorage.
- **Decision Report:** Persist filter/sort (filterSymbol, filterSignal, filterAction, filterReason, sortBy, sortOrder) in **localStorage** (e.g. `decision_report_preferences`). On load, restore.
- **Other “saved items”:** If you have watchlists or saved scan lists, store in DB or JSON and load on startup (separate from this doc).

---

## 4. Implementation phases

| Phase | What | Notes |
|-------|------|--------|
| **1** | Bot state persistence + 30-min rule | Save/load current_symbols, no_trade_streak, last_cycle_at; resume or start fresh in bot_manager. |
| **2** | Trade history to DB + load on init | Wire record_trade to LogManager (or shared DB); load trade_history from DB in bot init. |
| **3** | Positions | Derive from trade history on startup (or add positions table). |
| **4** | UI preferences | localStorage for Logs and Decision Report filters/sort. |

---

## 5. File/DB layout (proposed)

- **Existing:** `log_manager.py` → `logs/trading_logs.db` (trades, system_logs, backtest_results, performance_metrics).
- **New (optional):** `bot_state.db` or reuse `trading_logs.db` with new table `bot_state` (last_cycle_at, current_symbols JSON, no_trade_streak JSON, cycle_number). Alternatively `bot_state.json` for minimal dependency.
- **Trade history:** Use LogManager’s `trades` table as canonical store; bot writes on each `record_trade` and loads from it on init.

---

## 6. Config (env)

- `BOT_RECOVERY_WINDOW_MINUTES` — if last cycle was longer than this ago, start fresh (default 30).
- `BOT_STATE_DB_PATH` or `BOT_STATE_FILE` — path to state DB or JSON (optional; default under project root).

---

## 7. References

- Recovery windows: Socket.IO, Ably (≈2 min for connection state); Freqtrade custom trade data in DB; state persistence patterns (e.g. Burr).
- This design uses a **30-minute** recovery window for “resume vs start fresh” as a configurable, safe default for a trading loop.
