# Market Bot — yfinance Mode Roadmap

**Focus:** Run bot in yfinance mode, ensure trading, analyze logs, test, debug, repeat.

**Created:** 2026-02-03  
**Status:** In Progress

---

## Cycle 1: Run → Analyze → Test → Debug → Repeat

### 1. Run Bot in yfinance Mode
- [x] API running (port 8002 — 8000 occupied by Yacht)
- [x] Start bot via `POST /api/bot/start` with `{"mode": "yfinance"}`
- [x] Bot trading: 10+ trades (INTC, APA, VZ, HAL, SLB, etc.)
- [x] Frontend: vite proxy defaults to 8002 (VITE_API_PROXY env to override)

### 2. Analyze Logs
- [x] `trading_bot.log` — yfinance mode init OK, stock discovery, screener (158 stocks fallback)
- [x] `api_8002.log` — startup 8/8 self-tests passed
- [x] `alerts.log` — Schwab "Live Mode" alerts during sandbox/dryrun cycle (expected)
- [x] Findings: "Using fallback stock universe", "No notification library", "Desktop notifications not available" (non-blocking)

### 3. Test
- [x] Core unittests: 31/31 pass (fixed `test_can_open_short_when_allowed` — clear positions in setUp)
- [x] yfinance-specific: `tests/runner.py --yfinance-only` — 15/15 pass
- [x] API health, bot status, trades endpoints — all OK

### 4. Debug
- [x] Fix `test_can_open_short_when_allowed` — positions loaded from DB caused exposure check to fail; clear in setUp
- [ ] Optional: expand stock universe if fallback 158 is limiting
- [ ] See [YFINANCE_LOOSEN_PARAMS.md](YFINANCE_LOOSEN_PARAMS.md) if no trades
- [ ] Re-run and verify

### 5. Repeat
- [ ] Restart bot with fixes
- [ ] Re-analyze logs
- [ ] Re-test
- [ ] Iterate until stable

---

## Key Settings for yfinance Mode

| Setting | Purpose |
|---------|---------|
| PAPER_TRADING_MODE | true |
| SCHWAB_API_ENABLED | off |
| ENABLE_ML_SIGNAL_FILTER | Consider OFF if no trades |
| Min OHLCV bars for signal | 20–30 if strict |
| Manual Trade Approval | OFF |

---

## Log Locations

| Log | Path |
|-----|------|
| Bot/API | `/home/operator/market-pie5-bot/trading_bot.log` |
| API startup | `/home/operator/market-pie5-bot/api.log` |
| Alerts | `/home/operator/market-pie5-bot/alerts.log` |
| Debug analysis | `/home/operator/market-pie5-bot/docs/LOG_ANALYSIS_DEBUG.md` |

---

## Timestamped Logs and Image Pulls

- Use timestamped Docker logs for debugging: `docker logs --timestamps -f --tail 80 <service>`
- Avoid pulling on start; prefer local images by setting `pull_policy: if_not_present` (or `never`) in compose, or run `docker-compose up -d --no-build`

## Cycle Log

| Cycle | Date | Actions | Findings | Fixes |
|-------|------|---------|----------|-------|
| 1 | 2026-02-03 | Started API 8002, bot yfinance, analyzed logs, ran tests, fixed failing test | Bot trading; port 8000 in use by Yacht; fallback universe 158 stocks; test_can_open_short failed due to DB-loaded positions | API on 8002; TestCanOpenShort setUp clears positions |
| 2 | 2026-02-03 | Probed all endpoints, tested yfinance/sandbox/dryrun-live modes, ran pytest | GET /api/system/info 404 (use /api/system); test_exit_prices failed (AAPL $150 > MAX $55) | probe path fix; test_exit_prices use entry_price 50 |
| 3 | 2026-02-03 | yfinance-only tests, alerts.log, frontend proxy, run-tests | 15/15 yfinance tests pass; alerts expected for sandbox/dryrun; frontend pointed to 8002; run-tests uses API_URL | vite proxy 8002; run-tests API_URL from env |

---

## Quick Start (Cycle 2+)

```bash
# Start API (use 8002 if 8000 occupied by Yacht)
cd /home/operator/market-pie5-bot && source venv/bin/activate
API_PORT=8002 python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8002 &

# Frontend (proxy to 8002 by default): cd frontend && npm run dev

# Start bot in yfinance mode
curl -X POST http://127.0.0.1:8002/api/bot/start -H "Content-Type: application/json" -d '{"mode": "yfinance"}'

# Check status & trades
curl http://127.0.0.1:8002/api/bot/status
curl "http://127.0.0.1:8002/api/trades?limit=10"

# Logs
tail -f trading_bot.log
```

---

*Last Updated: 2026-02-03*
