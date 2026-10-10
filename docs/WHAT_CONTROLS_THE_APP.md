# What Actually Controls the Web App

**Short answer:** The **Vite dev server** (port 5173) serves the React frontend and proxies API requests to the **FastAPI backend** (port 8002). The API serves `/api/*` routes and provides bot control.

---

## Request Flow

1. **Browser** → `http://localhost:5173`
2. **Vite dev server** (frontend)
   - Serves static assets (HTML, CSS, JS)
   - Proxies `/api/*` to `http://localhost:8002`
3. **FastAPI backend** (port 8002)
   - **File:** `api/main.py`
   - Serves: `/api/health`, `/api/bot/*`, `/api/stats`, etc.
   - Controls bot instance (start, stop, mode)

So: **Vite** decides where requests go; the **API** handles bot logic and data.

---

## Key Files

| What | File / location |
|------|------------------|
| **API app** | `api/main.py` |
| **Frontend** | `frontend/` (React + Vite) |
| **Vite config** | `frontend/vite.config.ts` (port 5173, proxy to API) |
| **Start/stop** | [START_STOP_RESTART.md](START_STOP_RESTART.md) |

---

## Production (Future)

When deployed (e.g. Docker, Nginx):
- Nginx or similar reverse proxy forwards traffic
- Frontend build output (`frontend/dist/`) served as static files
- API runs in container or under systemd
- See [PRODUCTION_API_OWNERSHIP.md](PRODUCTION_API_OWNERSHIP.md)

---

## If the app works on PC but not on phone or tablet

- Use the same URL on all devices (e.g. `http://192.0.2.21:5173`)
- Ensure phone/tablet is on the same network
- Check firewall allows ports 5173 and 8002
- Set `API_HOST=0.0.0.0` when starting API for network access
