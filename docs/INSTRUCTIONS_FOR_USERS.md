# Instructions for users — what to do now

**Use this if you’ve just set up the project and want to run the bot and see it working.**

---

## 1. Install (if you haven’t already)

```bash
cd market-pie5-bot
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env if needed (e.g. BOT_TOTAL_CAPITAL, mode defaults)
```

---

## 2. Start the API and the web UI

**Terminal 1 — API (required):**

```bash
./start_api.sh
```

Leave this running. You should see the API start on port 8000.

**Terminal 2 — Web dashboard:**

```bash
cd frontend
npm install
npm run dev
```

Then open your browser to: **http://localhost:5173**

---

## 3. In the web UI: choose mode and start the bot

1. **Mode** (top of the page): choose one of:
   - **yfinance** — paper trading with simulated data (no broker; good for testing)
   - **Sandbox** — paper trading with Schwab sandbox (needs Schwab API keys)
   - **Live** — real trading (use with caution)
   - **Dry-run** — live data, no orders

2. Click **Start** to begin the trading loop.

3. The bot will load symbols, evaluate them in cycles, and (depending on mode) place simulated or real orders.

---

## 4. Where to look to see what the bot is doing

| Where | What you see |
|-------|-------------------------------|
| **Dashboard** | Stats, capital, positions, recent activity |
| **Reports → Decision Report** | Per-symbol decisions (HOLD, BUY, SELL, reasons), cycle number, optional **Last cycle timings** when `BOT_TIMING=true` |
| **Logs** | Live log lines (e.g. “Cycle #N complete”, “Evaluating N symbols”) |
| **Trades** | Executed trades (filled, pending, history) |
| **Settings** | Capital, strategy, trading and screener options (changes apply on next Start/Restart) |

---

## 5. Run a performance check (optional)

To see how long each cycle and each phase (signals, execute, OHLCV, strategy, price) takes:

1. In the project root, add or set in **.env**: `BOT_TIMING=true`
2. **Restart the bot** (Stop → Start, or Restart).
3. Let at least one full cycle complete.
4. Open **Reports → Decision Report**. A **“Last cycle timings (performance)”** block will appear with Total cycle, Signals, Execute, OHLCV, Strategy, Price (seconds).
5. You can also check the **Logs** page for lines like: `Cycle #N timing: get_strategy_signal=... execute_trade=... total=...`

Full steps and tuning options: **[docs/PERFORMANCE_CHECK.md](PERFORMANCE_CHECK.md)**.

---

## 6. System health and self-test (optional)

- Open **System** in the sidebar to see health and self-test status (passed/total, timings).
- To run the **full self-test suite**: stop the bot, then click **“Run full self-test suite”** on the System page. This checks API, bot status, stats, trades, messages, logs, settings, etc.

---

## 7. Restart, stop, shutdown

- **Restart** — Stops the bot and starts it again with current settings (mode, .env). Use this after changing Settings or .env.
- **Stop** — Pauses the bot; you can **Start** again without restarting the server.
- **Shutdown** — Stops the API server. To use the app again, run `./start_api.sh` (and frontend if needed).

---

## 8. If something’s wrong

- **“No symbols” / “No data” in Decision Report** — First cycle can take 1–2 minutes (fetching data). Check **Logs** for “Evaluating N symbols”. If it stays stuck, see **[docs/DECISION_REPORT_NO_DATA_ANALYSIS.md](DECISION_REPORT_NO_DATA_ANALYSIS.md)**.
- **No trades (all HOLD / No trade)** — Strategy or filters may be strict. See **[docs/YFINANCE_LOOSEN_PARAMS.md](YFINANCE_LOOSEN_PARAMS.md)** and **[docs/WHY_BOT_NOT_TRADING.md](WHY_BOT_NOT_TRADING.md)**.
- **API or frontend won’t start** — Ensure port 8000 (API) and 5173 (frontend) are free; check `./start_api.sh` output and browser console.

More docs: **[README.md](../README.md)**, **[docs/USER_GUIDE.md](USER_GUIDE.md)**, **[docs/README.md](README.md)**.
