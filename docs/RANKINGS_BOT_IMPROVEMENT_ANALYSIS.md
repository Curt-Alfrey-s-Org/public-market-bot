# Rankings-Bot → Market-Bot Improvement Analysis

**Purpose:** Identify non-mission-related improvements from rankings-bot that can be applied to market-pie5-bot. Both repos share the same core architecture (FastAPI + React + Vite) but have different missions (trading vs. billiards rankings).

**Last Updated:** March 17, 2026

---

## Executive Summary

| Category | Rankings-Bot Has | Market-Bot Has | Recommendation |
|----------|------------------|----------------|----------------|
| **Coding standards** | `.github/CODING_STANDARDS.md` (comprehensive) | None | Add adapted version |
| **Start/stop scripts** | `scripts/start.sh`, `scripts/stop.sh` (unified) | `start_api.sh` only | Add unified scripts |
| **Deployment docs** | `START_STOP_RESTART.md`, `WHAT_CONTROLS_THE_WEBSITE.md` | Scattered | Add operational docs |
| **Docs index** | Rich `docs/INDEX.md` with troubleshooting table | Minimal `docs/INDEX.md` | Expand index |
| **Process ownership** | `PRODUCTION_API_OWNERSHIP.md` (Twelve-Factor) | Referenced in rules only | Add doc |
| **Port assignments** | `.github/PORT_ASSIGNMENTS.md` | In README only | Add canonical doc |
| **Test DB safety** | Refuses non-test Postgres by default | N/A (no Postgres) | Skip |
| **Docker production** | Full Docker Compose flow | Optional | Consider for production |
| **Desktop launcher** | `install_desktop_launcher.sh`, `install_desktop_all_users.sh` | `install_desktop_icons.sh` | Align patterns |

---

## 1. Coding Standards (High Impact)

**Rankings-bot:** `.github/CODING_STANDARDS.md` — 450+ lines covering:
- Python (PEP 8, type hints, FastAPI patterns)
- TypeScript/React (ESLint, hooks, error boundaries)
- Docker (BuildKit, multi-stage, health checks)
- Database (PostgreSQL, migrations, indexes)
- Security (JWT, subprocess safety, secrets)
- Testing (unit, integration, AAA pattern)
- Git (conventional commits, branch strategy)
- Configuration (single source, no fallbacks)
- Monitoring (structured logging, health checks)

**Market-bot:** No central coding standards doc. Rules exist in `.cursor/rules/` but not in repo.

**Recommendation:** Add `.github/CODING_STANDARDS.md` adapted from rankings-bot. Remove rankings-specific sections (tournament management, web scraping, AI Coach). Keep: Python, FastAPI, TypeScript, Docker, security, testing, Git, config, monitoring. Add market-bot-specific: trading safety, Schwab API patterns, PDT compliance.

---

## 2. Unified Start/Stop Scripts (High Impact)

**Rankings-bot:** Single entry points with clear modes:
```bash
./scripts/start.sh              # Full stack
./scripts/start.sh --dev        # Development
./scripts/start.sh --deps-only  # Postgres + Redis only
./scripts/start.sh --app-only   # API + frontend (deps must run first)
./scripts/start.sh --production # No prompt
./scripts/stop.sh
./scripts/stop.sh --app-only
```

**Market-bot:** `start_api.sh` only. No unified stop. No dev vs. production distinction. Frontend started separately (`cd frontend && npm run dev`).

**Recommendation:** Create `scripts/start.sh` and `scripts/stop.sh`:
- `--dev`: Start API + frontend (like current `start_api.sh` + `cd frontend && npm run dev`), optionally in background
- `--api-only`: API only (current `start_api.sh` behavior)
- `--full`: API + frontend, with optional Docker path if/when Docker is adopted
- `stop.sh`: Kill API and frontend processes by port (8002, 5173)

---

## 3. Operational Documentation (Medium Impact)

**Rankings-bot:**
- `docs/START_STOP_RESTART.md` — Quick reference table, production vs. dev
- `docs/WHAT_CONTROLS_THE_WEBSITE.md` — Request flow (browser → Nginx → API), key files

**Market-bot:** Instructions scattered in README, `docs/INSTRUCTIONS_FOR_USERS.md`. No single "start/stop/restart" reference. No "what controls the app" doc.

**Recommendation:**
- Add `docs/START_STOP_RESTART.md`: Table of commands (start API, start frontend, stop, run tests)
- Add `docs/WHAT_CONTROLS_THE_APP.md`: Request flow (browser → Vite dev server → API on 8002), key files (`api/main.py`, `frontend/`)

---

## 4. Docs Index with Troubleshooting (Medium Impact)

**Rankings-bot:** `docs/INDEX.md` includes:
- Testing, Dependencies, Deployment, Auth, Tournaments, etc.
- **Troubleshooting table:** Symptom → Doc (e.g., "502 Bad Gateway" → BAD_GATEWAY_TROUBLESHOOTING.md)
- "Skip when scanning" section

**Market-bot:** `docs/INDEX.md` is minimal (Mission, Trading, Development, Archive). `DOCUMENTATION_INDEX.md` at root is comprehensive but separate.

**Recommendation:** Merge/expand `docs/INDEX.md` to include:
- Troubleshooting table (symptom → doc)
- Link to `DOCUMENTATION_INDEX.md` or consolidate
- "Skip when scanning" for archive, screenshots

---

## 5. Process Ownership & Deployment Standards (Medium Impact)

**Rankings-bot:** `PRODUCTION_API_OWNERSHIP.md` (referenced in rules) — Production uses process manager (systemd/Docker). Scripts delegate to systemd when service exists. Single owner per port.

**Market-bot:** `deployment-process-ownership.mdc` rule exists but no repo doc. `start_api.sh` starts uvicorn directly; no systemd delegation.

**Recommendation:** Add `docs/PRODUCTION_API_OWNERSHIP.md` (or `PROCESS_OWNERSHIP.md`):
- Production: systemd or Docker owns API; scripts use `systemctl` when service exists
- Development: `start_api.sh` or `scripts/start.sh --dev` starts directly
- Document the pattern for future production deployment

---

## 6. Port Assignments (Low Impact)

**Rankings-bot:** `.github/PORT_ASSIGNMENTS.md` — Canonical list of ports (API 8003, frontend 5174, etc.).

**Market-bot:** Ports in README (8002, 5173) and `PORT_ASSIGNMENTS.md` referenced at `/home/operator/.github/` (workspace-level).

**Recommendation:** Add `.github/PORT_ASSIGNMENTS.md` in market-pie5-bot repo with: API 8002, frontend 5173, reserved 8000 (Yacht). Ensures single source of truth within repo.

---

## 7. Dependencies Documentation (Low Impact)

**Rankings-bot:** `docs/DEPENDENCIES.md` — requirements-api.txt, requirements-deps.txt, package.json, live-update defaults.

**Market-bot:** `requirements.txt` exists; no central dependencies doc.

**Recommendation:** Add `docs/DEPENDENCIES.md` listing:
- `requirements.txt` (Python)
- `frontend/package.json` (Node)
- Optional: `requirements-api.txt` if split later

---

## 8. Test Database Safety (N/A for Market-Bot)

**Rankings-bot:** `run_comprehensive_tests.py` has `_enforce_safe_test_database()` — refuses to run tests on non-test Postgres unless `ALLOW_TESTS_ON_NON_TEST_DB=1`.

**Market-bot:** No Postgres; uses SQLite/file-based storage. Not applicable unless Postgres is adopted.

---

## 9. Docker Production Flow (Future Consideration)

**Rankings-bot:** Full Docker Compose (Postgres, Redis, API, Celery, Nginx, Cloudflare tunnel). `full_deploy.sh` with intelligent caching, `--production`/`--maintenance`.

**Market-bot:** Docker exists (`docker-compose.yml`, `Dockerfile`) but primary flow is host-based (`start_api.sh` + frontend dev).

**Recommendation:** Document current host-based flow as primary. When moving to production deployment, adopt rankings-bot patterns (Docker Compose, health checks, single owner per service).

---

## 10. Desktop Launcher (Low Impact)

**Rankings-bot:** `scripts/install_desktop_launcher.sh`, `scripts/install_desktop_all_users.sh` — installs to application menu, optional Desktop shortcut.

**Market-bot:** `install_desktop_icons.sh` — similar purpose. Different script location (root vs. scripts/).

**Recommendation:** Move `install_desktop_icons.sh` to `scripts/install_desktop_launcher.sh` for consistency. Add `install_desktop_all_users.sh` if system-wide install is desired.

---

## 11. Config Policy (Low Impact)

**Rankings-bot:** `docs/SPLASH_CONFIG.md` — Config is single source of truth; no fallbacks when missing. API returns 503 with clear message.

**Market-bot:** `.env` with fallbacks in code. No explicit config policy.

**Recommendation:** Document in CODING_STANDARDS or separate doc: required env vars should fail fast with clear errors, not silently fall back to defaults for critical settings (e.g., `PAPER_TRADING_MODE`, `SCHWAB_API_KEY`).

---

## Implementation Priority

| Priority | Item | Effort | Impact | Status |
|----------|------|--------|--------|--------|
| 1 | Add `.github/CODING_STANDARDS.md` | Medium | High | ✅ Done |
| 2 | Add `docs/START_STOP_RESTART.md` | Low | Medium | ✅ Done |
| 3 | Add `docs/WHAT_CONTROLS_THE_APP.md` | Low | Medium | ✅ Done |
| 4 | Create `scripts/start.sh`, `scripts/stop.sh` | Medium | High | ✅ Done |
| 5 | Expand `docs/INDEX.md` with troubleshooting | Low | Medium | ✅ Done |
| 6 | Add `docs/PRODUCTION_API_OWNERSHIP.md` | Low | Medium | ✅ Done |
| 7 | Add `.github/PORT_ASSIGNMENTS.md` | Low | Low | ✅ Done |
| 8 | Add `docs/DEPENDENCIES.md` | Low | Low | ✅ Done |
| 9 | Move/align desktop launcher scripts | Low | Low | Pending |

---

## Files to Create/Modify

### Create
- `.github/CODING_STANDARDS.md`
- `docs/START_STOP_RESTART.md`
- `docs/WHAT_CONTROLS_THE_APP.md`
- `scripts/start.sh`
- `scripts/stop.sh`
- `docs/PRODUCTION_API_OWNERSHIP.md`
- `.github/PORT_ASSIGNMENTS.md`
- `docs/DEPENDENCIES.md`

### Modify
- `docs/INDEX.md` — Add troubleshooting table, expand sections
- `README.md` — Link to new docs
- `DOCUMENTATION_INDEX.md` — Link to `docs/INDEX.md`

---

## References

- Rankings-bot: `/home/operator/rankings-bot/`
- Rankings-bot CODING_STANDARDS: `rankings-bot/.github/CODING_STANDARDS.md`
- Rankings-bot start/stop: `rankings-bot/scripts/start.sh`, `rankings-bot/scripts/stop.sh`
- Rankings-bot docs index: `rankings-bot/docs/INDEX.md`
- Market-bot rules: `market-pie5-bot/.cursor/rules/` (deployment-process-ownership, etc.)
