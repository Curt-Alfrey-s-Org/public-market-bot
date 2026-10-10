# Market Bot — Login & API Authorization

**Date:** 2026-02-04 · **Updated:** 2026-09-25 (security review findings 8 and 10, plus follow-up)

---

## Overview

The dashboard requires users to sign in at the splash screen before accessing the app.
There are **no built-in default accounts**: accounts come from environment variables
(see below) or from registered, email-verified database users. The old
`admin/admin123`, `user/user123` and `guest/guest123` logins no longer work.

---

## Flow

1. Visit dashboard → Splash screen with login form
2. Enter username and password
3. On success the API returns a signed JWT; the browser stores it and sends it as
   `Authorization: Bearer <token>` on every API call
4. Session persisted in `localStorage` (return visits skip login while the token is valid, 7 days)
5. Log out via sidebar → Returns to splash

---

## How the API authorizes requests (2026-09-25)

| Request | Result |
|---------|--------|
| `/api/health*`, `/api/auth/*`, `/api/v1/auth/*` | Open (login, registration, health) |
| Any other `/api/*` with a valid session JWT (admin, director or user) | Allowed (read endpoints) |
| Any other `/api/*` with `X-API-Key: $BOT_API_KEY` | Allowed for **read** endpoints only (scripts / monitoring) |
| No credentials, bad/expired token, token signed with another secret | **401** |
| **Control endpoints** without an **admin** JWT | **401** (no token) / **403** (non-admin token) |

Control endpoints (admin JWT required; the API key alone is **not** enough):

- `POST /api/bot/start`, `/api/bot/stop`, `/api/bot/shutdown`, `/api/bot/shutdown-server`
- `POST /api/bot/mode` (paper / sandbox / live / dry-run)
- `POST /api/pending-trades/approve`, `/api/pending-trades/reject`
- `PUT /api/settings`, `PUT /api/settings/ml-filter`
- `POST /api/trades/reset`, `POST /api/network/access`, `POST /api/system/run-tests`
- `GET /api/network/access/forbid`, `GET /api/network/access/allow` (these change the firewall despite being GETs; follow-up)
- Mobile: `POST /api/v1/bot/start`, `/api/v1/bot/stop`, `POST /api/v1/settings` (DB user with role `admin`)

Roles are read **only** from the signed token. A client-sent `X-User-Role` header is
ignored: it can neither grant privileges nor act as a "guest" switch. Tokens whose role
is not `admin`, `director` or `user` (e.g. `guest`) are rejected.

`GET /api/settings` is readable by any signed-in user, so it never returns
third-party API keys (Schwab, Hugging Face, Alpha Vantage, News API, Finnhub).
They come back as `********` when set and `""` when not. Set them in `.env`.

The web UI shows the role the server issued (`admin`, `director` or `user`).
Before this fix it showed non-admin accounts as `admin`. The server has always
enforced the real role.

Operator scripts that call control endpoints (`scripts/probe_all_modes.sh`,
`monitor_bot.py`, `yfinance_long_run.py`, `yfinance_mode_optimizer.py`) take an admin
token from `MARKET_BOT_ADMIN_TOKEN`, or log in with
`MARKET_BOT_ADMIN_USERNAME`/`MARKET_BOT_ADMIN_PASSWORD`. See `scripts/market_bot_auth.py`.

The frontend no longer ships any backend secret. `VITE_API_KEY` was removed from
`frontend/Dockerfile`, `docker-compose.yml` and the frontend code, because every
`VITE_*` value is compiled into the public JavaScript bundle.

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | `{ username, password }` → `{ success, token, user, role }` (`success=false` + `message` on bad credentials) |
| `/api/auth/me` | GET | Current user from the Bearer token → `{ role, sub }` |
| `/api/auth/logout` | POST | No server-side session; client clears token |
| `/api/v1/auth/login` | POST | Mobile login → `{ access_token, expires_in, user }` |

---

## Environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `JWT_SECRET` | **Yes in production** | Signs all session tokens (web and mobile; `JWT_SECRET_KEY` is accepted as a legacy alias). The API exits at startup with `CONFIGURATION ERROR: JWT_SECRET is not set` if it is missing, or if it is one of the old public placeholder strings. |
| `ENVIRONMENT` | No (default `production`) | Only `development`/`dev`/`test`/`testing`/`local` relax the JWT_SECRET requirement (a random per-process secret is used, so sessions end on restart). |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | For an env admin | Env admin account (both must be set). `ADMIN_PASSWORD_HASH` is also supported by `api/auth.py`. |
| `DIRECTOR_USERNAME` / `DIRECTOR_PASSWORD` | Optional | Env director account (both must be set). |
| `USER_USERNAME` / `USER_PASSWORD` | Optional | Env view-only account (both must be set). |
| `BOT_API_KEY` | Yes | Server-to-server key for scripts (`X-API-Key`). Never give it to the frontend. |

Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Placeholders for all of these are in `env.required.example`.

---

## Files

- `api/security_config.py` — JWT secret resolution (required in production)
- `api/auth.py` — tokens, `require_admin`, `authenticate_bearer_token`
- `api/main.py` — `RequireAuthMiddleware` (auth gate for `/api/*`)
- `api/routes/auth.py` — Login endpoint (env + DB users, no default accounts)
- `api/routes/v1/auth.py` — Mobile login/refresh
- `frontend/src/api/client.ts` — Sends the user's Bearer token (no API key)
- `frontend/src/api/auth.ts` — Auth API client
- `frontend/src/context/AuthContext.tsx` — Auth state
- `frontend/src/components/LoginForm.tsx` — Login form
- `frontend/src/components/SplashScreen.tsx` — Splash with login
- `tests/backend/test_control_endpoint_auth.py` — anonymous / guest / spoofed-header refusal tests

---

*Last Updated: 2026-09-25*
