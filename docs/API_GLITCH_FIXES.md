# Market Bot API — Glitch Fixes

**Date:** 2026-02-04

---

## Issues Found and Fixed

### 1. **get_logs blocking on huge log file**

- **Problem:** `trading_bot.log` had 1.18M+ lines. Reading with `f.readlines()` loaded the entire file into memory and blocked the event loop for many seconds.
- **Fix:** Read only the last ~2MB of the file (`_read_tail_lines`) and run the read in `asyncio.to_thread()` so it doesn't block other requests.

### 2. **get_trades blocking SQLite I/O**

- **Problem:** `LogManager().get_trades()` does synchronous SQLite queries. With thousands of trades, this blocked the event loop.
- **Fix:** Run `LogManager().get_trades()` in `asyncio.to_thread()`.

### 3. **get_stats blocking on heavy iteration**

- **Problem:** Stats computation iterates over `trade_history` (5000+ items), sorts, and computes monthly returns. All synchronous and blocking.
- **Fix:** Moved computation into `_compute_stats_sync()` and run it via `asyncio.to_thread()`.

---

## Files Changed

- `api/routes/logs.py` — tail-based read + thread pool
- `api/routes/trades.py` — thread pool for LogManager.get_trades
- `api/routes/stats.py` — `_compute_stats_sync` + thread pool

---

## Restart Required

Restart the API for changes to take effect:

```bash
# If running via start_api.sh or manually, restart:
pkill -f "uvicorn api.main:app.*8002"  # or your port
cd /home/operator/market-pie5-bot && source venv/bin/activate
API_PORT=8002 python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8002 &
```

---

*Last Updated: 2026-02-04*
