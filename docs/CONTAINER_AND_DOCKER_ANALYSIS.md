# Container Monitoring & Docker Build Analysis

**Last updated:** February 2026

---

## 1. Which module ensures containers are running / flags errors?

### Primary: `scripts/healthcheck.sh` (Market Bot only)

- **Role:** Checks that **Market Bot** API and frontend containers exist, are running, report healthy (Docker health), and that API/frontend HTTP endpoints respond.
- **Exits:** `0` if all pass, `1` if any check fails (container missing, not running, unhealthy, or HTTP fail).
- **Scope:** Only `market-pie5-bot-api` and `market-bot-frontend`. Does **not** check other bots (rankings, contracts, credit-check) or the Cloudflare Tunnel container (`cf-alfa`).
- **Limitation:** Uses fixed container names. Does not account for `ansible_market-bot-api_1` (docker-compose project prefix).

### Secondary: `scripts/verify_ports_and_health.sh`

- **Role:** HTTP checks (API health, frontend, auth) and optional `docker ps` listing for market-bot–related containers. Logs to `logs/selftest-ports-*.log`.
- **Exits:** Does not strictly enforce “containers must be running”; focuses on ports and HTTP. Some commands use `|| true`, so failures do not always propagate.

### Process-only: `scripts/bot_monitor.sh`

- **Role:** Monitors the **bot process** (`pgrep -f "python3.*main.py"`), not Docker. Useful when running API/bot directly on the host.
- **Does not:** Check Docker containers.

### Conclusion

- **No single module** ensures **all** deployment containers (market, rankings, contracts, credit-check, cf-alfa) are running.
- The only script that **flags errors** (exit 1) when containers are missing or not running is **`scripts/healthcheck.sh`**, and only for Market Bot’s two containers.

---

## 2. Error handling improvements needed

| Area | Current | Improvement |
|------|---------|-------------|
| **healthcheck.sh** | Assumes `sudo docker` works; no check for Docker installed or permission denied | Test `docker`/`sudo docker` once; exit with clear message if unavailable |
| **healthcheck.sh** | Fixed names `market-pie5-bot-api`, `market-bot-frontend` | Support env vars (e.g. `CONTAINER_API`, `CONTAINER_FRONTEND`) and alternate name `ansible_market-bot-api_1` |
| **healthcheck.sh** | Fails entirely if frontend container missing (e.g. API-only deploy) | Make frontend check optional (e.g. skip if container not expected) |
| **verify_ports_and_health.sh** | Some `|| true` masks failures | Use `set -e` and fail on HTTP/auth failures where appropriate, or document “best-effort” |
| **run_selftest_subdomain_trail.sh** | Uses `CONTAINER` env; falls back to `docker` if `sudo docker` fails | Good; ensure all callers can pass container name for different compose projects |
| **Orchestration** | No “all containers” check for 4-bot + tunnel | Add optional script (e.g. `scripts/check_all_containers.sh`) that checks expected list and exits 1 if any missing/not running |

---

## 3. Docker build size and standards

### API Dockerfile (project root)

| Issue | Severity | Current | Best practice |
|-------|----------|---------|----------------|
| **No .dockerignore** | High | Entire repo (1.1G+) sent as build context; `COPY *.py` pulls 240+ root `.py` (tests, one-off scripts) | Add `.dockerignore` to exclude `docs/`, `tests/`, `frontend/`, `*.md`, `.git`, etc. |
| **Single stage** | Medium | `gcc`/`g++` and build tools stay in final image | Multi-stage: build wheels in builder stage, copy only runtime + artifacts to final stage |
| **COPY *.py** | High | Copies every root `.py` (including test/debug scripts) | Copy only needed modules (e.g. `api/`, `main.py`, `database/`, etc.) or use .dockerignore so only needed files are in context |
| **Base image** | OK | `python:3.10-slim` | Good; consider `python:3.10-slim-bookworm` for reproducibility |
| **Layer order** | OK | requirements then code | Good for cache |
| **HEALTHCHECK** | OK | curl `/api/health` | Good |

### Frontend Dockerfile (`frontend/Dockerfile`)

| Issue | Severity | Current | Best practice |
|-------|----------|---------|----------------|
| **Build failure ignored** | High | `RUN npm run build \|\| true` | Fail build on failure: `RUN npm run build` |
| **COPY . .** in builder | Medium | Copies entire frontend (including node_modules if present) | Add `.dockerignore` in frontend: `node_modules`, `dist`, `.git` so `npm ci` is the source of truth |
| **Multi-stage** | OK | builder + nginx runtime | Good |
| **Runtime image** | OK | `nginx:alpine` + curl for healthcheck | Good |
| **HEALTHCHECK** | OK | curl `/` | Good |

### Image size drivers

- **API:** Large dependency set (pandas, numpy, scipy, sklearn, selenium, backtrader, etc.). Optional: split `requirements.txt` into base vs optional and use a slimmer base image for production.
- **Context size:** Without `.dockerignore`, build context is large and builds are slower; image layers may include unnecessary files if COPY patterns are broad.

---

## 4. Recommendations (short)

1. **Containers:** Keep using `scripts/healthcheck.sh` for Market Bot; add env-based container names and optional frontend check; add optional “all containers” checker for full deployment.
2. **Error handling:** In healthcheck, check for Docker availability and permission; exit with clear message. In verify_ports_and_health, avoid masking failures where a hard fail is desired.
3. **Docker:** Add `.dockerignore` (root and frontend). In API Dockerfile, copy only required app code (or narrow with .dockerignore). In frontend Dockerfile, remove `|| true` from `npm run build`. Consider multi-stage API build to keep final image smaller.
