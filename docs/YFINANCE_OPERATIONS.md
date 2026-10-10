# Yfinance Mode — Operations

How to run, test, and operate the bot in yfinance mode (training / no broker).

---

## Quick start

1. **Start API** (project root, with venv if you use it):
   ```bash
   ./start_api.sh
   ```
2. **Start frontend** (optional, for GUI):
   ```bash
   cd frontend && npm run dev
   ```
   Open http://localhost:5173 → select **yfinance** (Training) → **Start**.
3. **Validate:** Logs page and **Reports → Decision Report** (cycle number, symbols, signals).

---

## Run yfinance tests (no API)

From project root with venv activated:

```bash
./run_yfinance_tests.sh
```

Or:

```bash
python3 tests/runner.py --yfinance-only
```

Runs: test_yfinance_sim.py, test_yfinance_fallback_alert.py, Import + YfinanceModeTest (12 tests). Use to confirm fallback, trade tagging, and signal/execute logic.

---

## See trades in yfinance mode

If the Decision Report shows symbols but no or few trades, loosen params **one at a time** (see [YFINANCE_LOOSEN_PARAMS.md](YFINANCE_LOOSEN_PARAMS.md)):

1. **Settings → Strategy:** Turn **ML signal filter** OFF (or lower min confidence / min win prob).
2. **Settings → Strategy:** Set **Min OHLCV bars for signal** to **20** (or 30).
3. **Settings → Trading:** Ensure **Manual Trade Approval** is OFF.
4. **Settings → Discovery:** Check **Min/Max stock price** and **Max discovered stocks** so symbols load.

Restart the bot after changing settings. Check Logs for "decision=BUY → action BUY" and Trades for simulated fills.

---

## Full test suite (with API)

With API running (`./start_api.sh`):

```bash
python3 tests/runner.py
```

Includes mode change to yfinance, reports/decisions, E2E critical path, and frontend checks.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [YFINANCE_MODE_GOAL.md](YFINANCE_MODE_GOAL.md) | What yfinance mode does in code |
| [YFINANCE_TEST_PLAN.md](YFINANCE_TEST_PLAN.md) | Test plan and manual GUI checklist |
| [YFINANCE_LOOSEN_PARAMS.md](YFINANCE_LOOSEN_PARAMS.md) | Params to loosen to see trades |
| [PERFORMANCE_CHECK.md](PERFORMANCE_CHECK.md) | Optional BOT_TIMING and cycle timings |

**Last updated:** January 2026.
