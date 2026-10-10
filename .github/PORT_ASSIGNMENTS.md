# Port Assignments — Market-Pie5-Bot

Canonical port list for this repository.

---

## Development (Default)

| Service | Port | Env Override |
|---------|------|--------------|
| API | 8002 | `API_PORT` |
| Frontend (Vite) | 5173 | `FRONTEND_PORT` |

---

## Reserved Ports

| Port | Reserved For |
|------|--------------|
| 8000 | Yacht (do not use for market bot) |

---

## Production (Server)

When deployed on a shared server, ports may differ:

- **API:** Often bound to `127.0.0.1:8004` (or similar) for reverse proxy
- **Frontend:** Served via Nginx; no dev server port
- **Database:** `127.0.0.1:5435` if PostgreSQL used

See `README.md` and deployment docs for production configuration.
