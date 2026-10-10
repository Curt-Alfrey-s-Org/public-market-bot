# Production API Ownership — Market Bot

**Principle:** Production MUST use a process manager (systemd, Docker, or similar). Only one mechanism starts/restarts each service. Scripts delegate to the process manager when it exists.

---

## Core Principles

### 1. Single Process Manager (Production)

- **Production** uses a process manager: systemd, supervisord, or container orchestration
- **No duplicate starters** — Only one mechanism starts/restarts each service/port
- **Standards:** [Twelve-Factor App (Processes)](https://12factor.net/processes), [FastAPI deployment](https://fastapi.tiangolo.com/deployment/)

### 2. Development vs Production

| Mode | Who starts API | Who starts frontend |
|------|----------------|---------------------|
| **Development** | `./scripts/start.sh` or `./start_api.sh` | `./scripts/start.sh` or `cd frontend && npm run dev` |
| **Production** | systemd service or Docker | Nginx serves built `frontend/dist/` |

### 3. Script Delegation

When a systemd service exists, scripts should use `systemctl` instead of starting uvicorn directly:

```bash
# Good pattern for scripts
if command -v systemctl &>/dev/null && systemctl cat market-bot-api.service &>/dev/null; then
  # Production: delegate to systemd (single owner)
  sudo systemctl restart market-bot-api
  exit 0
fi
# Dev: start directly (no systemd)
./scripts/start.sh --api-only
```

---

## Current State (Development)

- **API:** Started by `./start_api.sh` or `./scripts/start.sh --api-only`
- **Frontend:** Started by `cd frontend && npm run dev` or `./scripts/start.sh`
- **Ports:** API 8002, Frontend 5173
- **No systemd/Docker** in default dev flow

---

## Future Production Deployment

When deploying to production:

1. **Create systemd service** (e.g. `market-bot-api.service`) for the API
2. **Build frontend** (`npm run build`) and serve via Nginx or the API
3. **Scripts check for systemd** and delegate with `systemctl restart` when service exists
4. **Single owner per port** — no script and systemd both starting uvicorn

---

## Anti-Patterns to Avoid

- ❌ "systemd or start_api.sh" as equal production options
- ❌ Scripts that start uvicorn when systemd service exists (causes "address in use")
- ❌ Two processes on the same port

---

## See Also

- [START_STOP_RESTART.md](START_STOP_RESTART.md) — Start/stop commands
- [WHAT_CONTROLS_THE_APP.md](WHAT_CONTROLS_THE_APP.md) — Request flow
- [.github/CODING_STANDARDS.md](../.github/CODING_STANDARDS.md) — Coding standards
