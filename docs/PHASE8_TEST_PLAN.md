# Phase 8.2 Test Plan (Web GUI Polish & Migration)

**Purpose:** Ensure React + FastAPI GUI is production-ready: E2E coverage, responsive behavior, error handling, and performance.  
**Reference:** [ROADMAP.md](../ROADMAP.md) — Phase 8: Polish & Migration.

---

## 1. Automated Tests (run regularly)

### Backend + frontend self-test

```bash
# From project root. API must be running on http://localhost:8000
python3 tests/runner.py
```

**Covers:**
- **API Endpoints:** Health, root, bot status/start/stop/shutdown, stats, trades, messages, logs, **reports/decisions**, settings, system, CORS
- **Bot Integration:** Bot lifecycle, mode change
- **Error Patterns:** API error handling
- **E2E Critical Path (API):** Single test that runs in sequence: health → stats → reports/decisions → logs → messages → bot status (see `tests/backend/test_e2e_critical_path.py`)
- **Imports:** Module load and route registration
- **GUI Data Points:** Frontend fetches correct API data
- **GUI Visual / Interactions:** Basic UI behavior

**Decision Report:** The test `Reports Decisions Endpoint` asserts `GET /api/reports/decisions` returns `candidates`, `decisions`, `cycle_number`, `total_candidates`, `evaluated_count`, `cycle_in_progress_no_data` with correct types.

**Before running:** Start API (`./start_api.sh` or `uvicorn api.main:app --reload`) and optionally frontend (`cd frontend && npm run dev`) so GUI tests can hit `http://localhost:5173`.

---

## 2. E2E Critical Path

**Automated (API):** `python3 tests/runner.py` runs **E2E Critical Path (API)** — health → stats → reports/decisions → logs → messages → bot status in one sequence. No frontend required.

**Manual (frontend):** Run with **API + frontend** up. Verify in order:

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `http://localhost:5173` | App loads; no blank screen |
| 2 | Dashboard | Stats (capital, trades, win rate, etc.) load; Recent Activity shows messages |
| 3 | Start bot (yfinance mode) | Start succeeds; status shows "Running" |
| 4 | Reports → Decision Report | Table loads; candidates/decisions or "not yet evaluated" banner; polling updates |
| 5 | Logs page | Log lines from `trading_bot.log`; filters (level, search) work |
| 6 | Stop bot | Stop succeeds; status shows "Stopped" |
| 7 | Settings | Settings load; categories visible; no console errors on load |
| 8 | Trades / Pending / System / AI / Tax | Each page loads without crash |

---

## 3. Responsive & Layout

- [ ] **Desktop (e.g. 1920×1080):** Sidebar, dashboard, Decision Report table, Logs — all usable; no horizontal scroll for main content.
- [ ] **Tablet (e.g. 768px width):** Layout adapts; sidebar or nav still usable; tables readable or scrollable.
- [ ] **Narrow (e.g. 375px):** No overlap; primary actions (start/stop, nav) still accessible.

Test on at least one real device or browser resize; document any known layout limits.

---

## 4. Error Handling

- [ ] **API down:** Frontend shows clear error (e.g. "Cannot connect") instead of infinite loading or blank page.
- [ ] **404 / invalid route:** App shows error boundary / "Try again" or redirect, no white screen.
- [ ] **Bot start/stop failure:** User sees feedback (toast or message), not silent failure.
- [ ] **Logs endpoint (missing file):** Logs page shows empty or "No logs" instead of crashing.

---

## 5. Performance (guidelines)

- [ ] **Initial load:** First meaningful paint &lt; 5s on typical broadband.
- [ ] **Navigation:** Lazy-loaded routes (Dashboard, Decision Report, Logs, Settings, etc.) load in &lt; 2s after click.
- [ ] **Decision Report polling:** When bot is running, 2.5s polling does not cause visible jank or memory growth over 5+ minutes.
- [ ] **API health:** `GET /api/health` responds in &lt; 500ms under normal load.

Use browser DevTools (Network, Performance) and/or `tests/runner.py` timings; document baseline if needed.

---

## 6. WebSocket Reconnection (when implemented)

- [ ] **WebSocket down:** App falls back to polling or shows "Reconnecting" and recovers when server is back.
- [ ] **Reconnect after sleep:** After machine/sleep, client reconnects or refreshes data on next interaction.

*Note: Current real-time updates use polling; WebSocket items can be added when `/ws` is implemented.*

---

## 7. Sign-off

| Area | Owner | Done |
|------|--------|------|
| Automated tests (runner.py) | Dev | ☑ |
| E2E critical path (API) | Dev | ☑ |
| E2E critical path (frontend manual) | Dev/QA | ☐ |
| Responsive & layout | Dev/QA | ☐ |
| Error handling | Dev | ☐ |
| Performance | Dev | ☐ |
| WebSocket reconnection | Dev | ☐ (N/A until WS added) |

**Phase 8.2 status:** Automated testing and E2E critical path (API) are implemented and run via `python3 tests/runner.py`. Manual checklist (frontend E2E, responsive, error handling, performance) remains for QA sign-off when needed.

**Last updated:** January 2026.  
**Next:** Phase 8.3 (migration guide) is complete; proceed to other roadmap items.
