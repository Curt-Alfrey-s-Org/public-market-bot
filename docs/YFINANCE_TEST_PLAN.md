# Yfinance mode — test plan (until solid)

How to run and extend yfinance tests so the mode stays solid.

**Prerequisites:** `pip install -r requirements.txt` (pandas and other deps required for `main.py`). Use the project venv if you have one.

---

## 1. Run yfinance-only tests (no API)

From project root:

```bash
./run_yfinance_tests.sh
```

Or:

```bash
python3 tests/runner.py --yfinance-only
```

This runs:

1. **test_yfinance_sim.py** — auto-fallback (Schwab fail → yfinance), trade tagging (`yfinance_sim`), trade filtering by mode, API validation with fallback, both APIs unavailable → random.
2. **test_yfinance_fallback_alert.py** — alert when yfinance unavailable (random fallback), no alert when yfinance works.
3. **YfinanceModeTest** (tests/backend/test_yfinance_mode.py) — unit tests:
   - `get_stock_price` uses yfinance and sets `using_yfinance_sim`
   - `execute_trade` paper mode records trade with mode `yfinance_sim`
   - `get_strategy_signal` returns `(signal, price, volume)` with signal in BUY/SELL/HOLD
   - `get_strategy_signal` returns HOLD when OHLCV has insufficient bars
   - `get_trades_by_mode('yfinance_sim')` returns only yfinance_sim trades
   - `validate_api_connectivity` succeeds with yfinance fallback

All of the above **do not require the API** to be running.

---

## 2. Run full suite (includes yfinance + API)

With API running (`./start_api.sh`):

```bash
python3 tests/runner.py
```

This includes:

- Import validation
- **YfinanceModeTest** (same as above)
- API endpoints (health, bot status, **mode change to yfinance**, **reports/decisions**)
- Bot integration, error patterns, E2E critical path
- Frontend data/visual/interactions (optional; frontend URL)

Use this to confirm mode switch to yfinance and Decision Report work against a live API.

---

## 3. Manual checklist (GUI)

After unit/API tests pass, validate in the GUI:

1. **Start API + frontend** — `./start_api.sh`, then `cd frontend && npm run dev` → open http://localhost:5173.
2. **Select mode** — Choose **yfinance** (Training).
3. **Start bot** — Click **Start**.
4. **Decision Report** — Open **Reports → Decision Report**. Within 1–2 minutes you should see:
   - Cycle number ≥ 1
   - Rows per symbol with signal (HOLD/BUY/SELL), reason (Hold, No trade, Order submitted, etc.)
5. **Logs** — Open **Logs**; expect lines like “Evaluating N symbols”, “Cycle #N complete”, “Culled … No-trade symbol(s)” (if culling enabled).
6. **Trades** — If strategy produces BUY/SELL and execution runs, **Trades** should show simulated fills.
7. **Performance** — Optional: set `BOT_TIMING=true` in .env, restart bot, then check Decision Report “Last cycle timings” block. See [PERFORMANCE_CHECK.md](PERFORMANCE_CHECK.md).

---

## 4. When tests fail

- **Import/main errors** — Ensure `requirements.txt` is installed and you’re in the project root (and venv if used).
- **get_strategy_signal / STRATEGY_MIN_BARS** — Unit test mocks OHLCV with 50+ rows; if `STRATEGY_MIN_BARS` is higher, the test uses `max(50, STRATEGY_MIN_BARS)`. If your env sets a very high value, the mock may need adjusting.
- **record_trade / execute_trade** — If paper mode path fails (e.g. capital floor), ensure `using_yfinance_sim=True` in the test so capital/PDT checks are skipped in code.
- **API tests skipped** — Run with API: `./start_api.sh` then `python3 tests/runner.py` (no `--yfinance-only`).

---

## 5. Adding more tests

- **tests/backend/test_yfinance_mode.py** — Add new `test_*` methods and append them to the `tests` list in `run()`.
- **test_yfinance_sim.py** / **test_yfinance_fallback_alert.py** — Add new `unittest.TestCase` methods.
- **API behavior** — Use **tests/backend/test_api_endpoints.py** (e.g. mode change, reports/decisions) or **tests/backend/test_bot_integration.py** for bot + API integration.

Keeping **run_yfinance_tests.sh** and the manual checklist up to date will keep yfinance mode solid as you change code.
