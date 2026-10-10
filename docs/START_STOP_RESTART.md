# Start, Stop, and Restart — Market Bot

**Single entry points:** `./scripts/start.sh` and `./scripts/stop.sh`

---

## Quick Reference

| Action | Command |
|--------|---------|
| **Start (full dev)** | `./scripts/start.sh` or `./scripts/start.sh --dev` |
| **Start (API only)** | `./scripts/start.sh --api-only` |
| **Stop (all)** | `./scripts/stop.sh` |
| **Legacy: API only** | `./start_api.sh` |
| **Self-test + analyze** | `./run_selftest_and_analyze.sh` |

---

## Development (Default)

### Full stack (API + frontend)

```bash
./scripts/start.sh
```

- Starts API in background (port 8002)
- Starts frontend in foreground (port 5173)
- Open http://localhost:5173 in your browser
- Press Ctrl+C to stop frontend; API keeps running
- Run `./scripts/stop.sh` to stop API

### API only

```bash
./scripts/start.sh --api-only
```

- Starts API in foreground (port 8002)
- For frontend, open another terminal: `cd frontend && npm run dev`

### Stop everything

```bash
./scripts/stop.sh
```

- Stops API (uvicorn)
- Stops frontend (Vite on port 5173)

---

## Ports

| Service | Default Port | Env Override |
|---------|--------------|--------------|
| API | 8002 | `API_PORT` |
| Frontend | 5173 | `FRONTEND_PORT` |

---

## Legacy Scripts

| Script | Purpose |
|--------|---------|
| `./start_api.sh` | Start API only (foreground, with venv) |
| `./fix_api_connection.sh` | Kill existing API and restart |

---

## Disk / Docker cleanup

See **[DOCKER_DISK_CLEANUP.md](DOCKER_DISK_CLEANUP.md)** for **`./scripts/cleanup_docker_disk.sh`** (build cache and optional image prune) vs **`./scripts/docker_cleanup.sh`** (project containers).

---

## See Also

- [WHAT_CONTROLS_THE_APP.md](WHAT_CONTROLS_THE_APP.md) — Request flow and key files
- [INSTRUCTIONS_FOR_USERS.md](INSTRUCTIONS_FOR_USERS.md) — User instructions
