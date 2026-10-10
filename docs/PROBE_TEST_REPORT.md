# Market Bot — Probe & Test Report

**Date:** 2026-02-03  
**API:** http://127.0.0.1:8002

---

## 1. API Endpoint Probe

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /api/health | 200 | OK |
| GET /api/bot/status | 200 | OK |
| GET /api/stats | 200 | OK |
| GET /api/trades | 200 | OK |
| GET /api/messages | 200 | OK |
| GET /api/settings | 200 | OK |
| GET /api/logs | 200 | OK |
| GET /api/reports/decisions | 200 | OK |
| GET /api/pending-trades | 200 | OK |
| GET /api/system | 200 | System info (path is /api/system, not /api/system/info) |
| GET /api/system/health | 200 | OK |

---

## 2. Bot Mode Cycle

| Mode | Start | Status After |
|------|-------|--------------|
| yfinance | OK | running=true, mode=yfinance |
| sandbox | OK | running=true, mode=sandbox |
| dryrun-live | OK | running=true, mode=live* |

\* dryrun-live reports mode `live` in status (dryrun is a variant of live with DRY_RUN_MODE=true).

---

## 3. Test Failures Found

| Test | Failure | Fix |
|------|---------|-----|
| tests/backend/test_exit_prices.py::test_buy_records_entry_exit_and_pnl | AAPL $150 exceeded MAX_STOCK_PRICE $55 → trade skipped | Changed entry_price to 50.0 |

---

## 4. Probe Script

Run: `bash scripts/probe_all_modes.sh [API_URL]`

```bash
cd /home/operator/market-pie5-bot
bash scripts/probe_all_modes.sh http://127.0.0.1:8002
```

---

## 5. Run Full Tests

```bash
cd /home/operator/market-pie5-bot && source venv/bin/activate

# Unit tests (no API)
python -m unittest discover -s . -p "test_*.py" -v

# Pytest (tests/ backend; conftest.py adds project root to path)
pytest tests/ -v --tb=short

# Comprehensive runner (requires API on 8000, bot stopped)
API_URL=http://127.0.0.1:8002 python tests/runner.py --api-url http://127.0.0.1:8002
```

---

## 6. Known Issues

- **run-tests endpoint** — now uses `API_URL` env (default 8002)
- **pytest asyncio_mode** config warning (unknown option)
- **TestResult/TestStatus** collection warnings in framework/base_test.py

---

*Last Updated: 2026-02-03*
