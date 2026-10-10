# Migration: React + FastAPI as Default Web GUI

**Status:** Complete. The default web interface is now **React + FastAPI**. The legacy Plotly Dash web GUI has been removed from the repo.

---

## What Changed

| Before | After |
|--------|--------|
| Plotly Dash (`web_gui.py`, `start_web_gui.sh`) on port **8050** | **FastAPI** backend (port **8000**) + **React** frontend (port **5173**) |
| Single process (Dash served app + bot) | Two processes: API server + React dev/build |
| `./start_web_gui.sh` | `./start_api.sh` then `cd frontend && npm run dev` (or serve built frontend via API) |

---

## How to Run the Web UI (Current)

1. **Start the API** (required for dashboard and bot control):
   ```bash
   ./start_api.sh
   ```
   API runs at `http://localhost:8000`. Health: `http://localhost:8000/api/health`.

2. **Start the React frontend** (dashboard UI):
   ```bash
   cd frontend && npm install && npm run dev
   ```
   Frontend runs at `http://localhost:5173`. Open this URL in your browser.

3. **Use the dashboard:** Start/stop bot, change mode, view Stats, Trades, Logs, **Decision Report**, Settings, System, AI, Tax Reports from the React app. All data is fetched from the API.

**Mobile/tablet:** Use your machine’s IP instead of `localhost` (e.g. `http://192.0.2.21:5173` for frontend, `http://192.0.2.21:8000` for API). Ensure the frontend is configured to call the API at that host if needed (e.g. env or proxy).

---

## Feature Parity (React vs Legacy Dash)

The React GUI replicates the main workflows:

- **Dashboard** – Stats, recent activity (stored messages), bot status
- **Bot control** – Start, Stop, Shutdown; mode selection (yfinance, Sandbox, Live, Dry-run Live)
- **Trades** – Trade list with filters
- **Pending Trades** – Approval/rejection when manual approval is enabled
- **Logs** – Log viewer (reads `trading_bot.log`) with level/search
- **Decision Report** – Live candidate symbols and per-symbol decisions (yfinance visibility)
- **Settings** – Trading, risk, and other settings (GET/PUT via API)
- **System** – System info and self-test panel
- **AI** – AI summary and request
- **Tax Reports** – Tax report generation and downloads

If you relied on a specific Dash-only feature not listed above, check the API docs or open an issue; the backend may already expose it under a different route.

---

## Legacy Dash / Old Scripts

- **Old Dash GUI** (`web_gui.py`, `archive/old-dash-gui/`) has been **removed** from the repository. History is still in git if you need to reference it.
- **`start_web_gui.sh`** no longer exists. Use **`start_api.sh`** + **React frontend** as above.
- **Desktop icons** that pointed at the old web GUI should be updated to open `http://localhost:5173` (or your frontend URL). See [DESKTOP_ICONS_GUIDE.md](../DESKTOP_ICONS_GUIDE.md) if you use install scripts.

---

## Testing and Rollout

- **Phase 8.2 test plan:** [docs/PHASE8_TEST_PLAN.md](PHASE8_TEST_PLAN.md) – E2E, responsive, error handling, performance.
- **Self-test:** `python3 tests/runner.py` (with API running) – includes Decision Report and other API tests.

---

## Summary

- **Default web UI:** React + FastAPI. Start with `./start_api.sh` and `cd frontend && npm run dev`.
- **Legacy Dash:** Removed; use React + FastAPI for all web workflows.
- **Docs:** This file is the migration guide; [ROADMAP.md](../ROADMAP.md) Phase 8.3 tracks migration completion.

**Last updated:** January 2026.
