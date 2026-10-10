# Performance check

How to run a performance check on the trading bot (cycle timings, bottlenecks, system health).

## 1. Enable cycle timing (BOT_TIMING)

1. In the project root, edit `.env` and set:
   ```bash
   BOT_TIMING=true
   ```
2. **Restart the bot** (Stop → Start, or use the Restart button in the GUI).
3. Let the bot run **at least one full cycle** (e.g. one pass over all symbols).

## 2. Where to see the results

### Option A: Decision Report (GUI)

1. Open **Reports → Decision Report**.
2. When `BOT_TIMING=true` and at least one cycle has completed, a **“Last cycle timings (performance)”** block appears.
3. It shows:
   - **Total cycle** — total time for the last cycle (seconds).
   - **Signals** — time spent in `get_strategy_signal` for all symbols (parallel batch).
   - **Execute** — time spent executing trades.
   - **OHLCV / Strategy / Price** — breakdown inside signal evaluation (data fetch vs strategy vs price).
   - **Symbols** — number of symbols in the cycle.
   - **Trades** — number of trades executed.

Use this to see where time is spent (e.g. OHLCV vs strategy vs execute).

### Option B: Logs

1. Open **Logs** (or tail `trading_bot.log`).
2. After each cycle you’ll see a line like:
   ```text
   Cycle #N timing: get_strategy_signal=X.XXs (M sym), execute_trade=Y.YYs (K trades), total=Z.ZZs | breakdown: ohlcv=... strategy=... price=...
   ```

### Option C: API

- `GET /api/reports/decisions` returns `last_cycle_timings` when the bot has run at least one cycle with `BOT_TIMING=true`.

## 3. Tuning performance

- **Batch size:** `BOT_SIGNAL_BATCH_SIZE` (default 16, max 64) — more workers = faster signal phase, more CPU/network. Increase if you have spare capacity.
- **Timeouts:** `GET_STRATEGY_SIGNAL_TIMEOUT_SECONDS` — if symbols often time out, consider increasing (e.g. 90) so slow symbols don’t block the cycle.
- **Culling:** `BOT_CULL_NO_TRADE_CYCLES` / `BOT_PROSPECTS_MIN_SIZE` — fewer prospects = shorter cycles after culling.

## 4. System health (self-test)

1. Open **System** in the sidebar.
2. The page shows **health** and **self-test** results (passed/total, timings).
3. Click **“Run full self-test suite”** to run the full test suite (bot must be **stopped**). This checks API, bot status, stats, trades, messages, logs, settings, etc., and reports timings.

Use this to confirm the stack is healthy; cycle timings above focus on **trading loop** performance.

## 5. Turn timing off

When you’re done checking performance, set:

```bash
BOT_TIMING=false
```

and restart the bot to avoid any extra timing overhead (small, but unnecessary in production).
