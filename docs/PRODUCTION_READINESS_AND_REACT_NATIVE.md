# Market Bot: Production Readiness & React Native Conversion

**Date:** February 12, 2026 (updated June 9, 2026 — drift check: Gaps 1, 6, 7, A, C verified implemented and marked done; see [ROADMAP.md](ROADMAP.md) for the current plan)  
**Current Status:** Functional bot with yfinance mode complete; ready for production hardening and mobile expansion  
**Scope:** Server-side production gaps, API readiness for mobile, and React Native (Expo) conversion steps

---

## Table of Contents

1. [Server: Production Readiness Checklist](#1-server-production-readiness-checklist)
2. [Server: API Ready for Mobile](#2-server-api-ready-for-mobile)
3. [React Native Conversion Guide](#3-react-native-conversion-guide)
4. [Summary & Next Steps](#4-summary--next-steps)

---

## 1. Server: Production Readiness Checklist

### 1.1 Already in Place ✅

- **Deployment:** Nginx reverse proxy, FastAPI backend, Cloudflare tunnel, Docker Compose
- **Database:** PostgreSQL with connection pooling
- **API:** Health check (`/api/health`), system status (`/api/system/health`), auth (login/logout)
- **Testing:** Comprehensive test framework in `tests/`
- **Docker Networking:** Correct `tunnel_network` and security (`127.0.0.1` localhost binding for API)
- **Environment:** `.env` example and documented configuration

### 1.2 Critical Production Gaps to Close

#### Gap 1: **Startup Data Recovery** ✅ DONE (verified 2026-06-09)
**Problem:** If database is empty or API fails to initialize bot state on startup, the bot serves stale/empty data until next scheduled task.

**Implemented:** `api/startup.py` module + FastAPI lifespan handler in `api/main.py`;
`/api/health` reports `startup_status.initialized`. Tested by `tests/backend/test_startup_recovery.py`.

**Fix:**
- [x] Add startup handling (lifespan) in `api/main.py` to:
  - Check if bot state is initialized (check `bot_state.json` or database)
  - If empty, trigger immediate initialization of data sources (yfinance, Schwab API)
  - Log initialization status and timestamp
  - Return 503 (Service Unavailable) until data is ready
- [x] Create `api/startup.py` module:
  ```python
  async def initialize_bot_data():
      """Initialize bot state on startup; run yfinance fetch if no data"""
      # Check if rankings/market data exists
      # If not, fetch from yfinance with timeout
      # Log when data is ready
  ```
- [x] Update health check to report "initializing" state during startup (`/api/health` → `startup_status`)
- [x] Document startup time expectations (README → `docs/API_RELIABILITY.md`, startup recovery section)

**Effort:** 4-6 hours  
**Testing:** Test database wipe → restart → verify data loads

---

#### Gap 2: **API Retry & Resilience** ⚠️ HIGH
**Problem:** yfinance timeouts, Schwab API failures, or network errors cause bot to hang or fail silently.

**Current Issue:**
```python
# Current pattern: fails immediately
try:
    data = yfinance.fetch(symbol, timeout=60)
except Exception as e:
    logger.error(f"Error: {e}")
    return None  # ❌ No retry, data lost
```

**Fix:**
- [ ] Implement exponential backoff retry in `api/utils/retries.py`:
  ```python
  async def with_retry(
      func, 
      max_retries=3, 
      backoff_factor=2, 
      timeout=30
  ):
      """Execute func with exponential backoff on transient errors"""
      for attempt in range(max_retries):
          try:
              return await asyncio.wait_for(func(), timeout=timeout)
          except (TimeoutError, ConnectionError) as e:
              if attempt < max_retries - 1:
                  wait_time = backoff_factor ** attempt
                  logger.warning(f"Retry {attempt+1}/{max_retries} after {wait_time}s: {e}")
                  await asyncio.sleep(wait_time)
              else:
                  logger.error(f"Failed after {max_retries} attempts: {e}")
                  raise
  ```
- [ ] Wrap yfinance calls and Schwab API calls with `with_retry()`
- [ ] Distinguish transient (timeout, 503) vs permanent (404, 403) failures
- [ ] Cache last successful fetch in memory/Redis for fallback
- [ ] Log retry attempts and backoff timing

**Effort:** 6-8 hours  
**Testing:** Simulate network failures → verify retries work → check logs

---

#### Gap 3: **Data Persistence & Archival** ⚠️ MEDIUM
**Problem:** Historical data is lost if database is wiped; no audit trail of old trades/decisions.

**Current Issue:**
- `rankings` or market data tables use UPSERT, overwriting older snapshots
- No historical archive table
- Trade history not consistently persisted across bot restarts

**Fix:**
- [ ] Create `data_archives` table for historical snapshots:
  ```sql
  CREATE TABLE data_archives (
      id SERIAL PRIMARY KEY,
      bot_name VARCHAR(50) NOT NULL,
      data_type VARCHAR(50),  -- 'market_snapshot', 'trade', 'decision'
      snapshot_date TIMESTAMP NOT NULL,
      data JSONB NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
  );
  CREATE INDEX idx_archives_bot_date ON data_archives(bot_name, snapshot_date DESC);
  ```
- [ ] Before UPDATE on live data tables, copy old row to `data_archives`
- [ ] Keep archives for ≥12 months; set retention policy in settings
- [ ] Export archives quarterly to CSV/JSON for backup
- [ ] Document restoration process

**Effort:** 5-7 hours  
**Testing:** Run bot for 1 cycle → verify archives → test restore

---

#### Gap 4: **Connection Loss & Write Queue** ⚠️ MEDIUM
**Problem:** If database connection drops during a trade, the trade is lost.

**Fix:**
- [ ] Implement write-ahead log (WAL) in `api/models/pending_operations.py`:
  ```sql
  CREATE TABLE pending_operations (
      id SERIAL PRIMARY KEY,
      operation_type VARCHAR(50),  -- 'trade', 'update_settings'
      data JSONB,
      status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
      retry_count INT DEFAULT 0,
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Before any critical write (trade, balance update):
  1. Insert to `pending_operations` (commit guaranteed first)
  2. Execute actual operation
  3. If successful, mark pending operation as 'completed'
  4. On startup, retry any 'pending' or 'failed' operations
- [ ] Monitor pending operations and send alert if count > threshold

**Effort:** 6-8 hours  
**Testing:** Kill database during trade → restart → verify trade is retried

---

#### Gap 5: **Secrets & Configuration Security** ⚠️ HIGH
**Current Issues:**
- API keys (VITE_API_KEY) in docker-compose.yml
- Schwab credentials in .env
- No environment-based secret rotation

**Fix:**
- [ ] Move all secrets to `.env.production` (git-ignored)
- [ ] Document required env vars in `.env.example`
- [ ] Use `python-dotenv` with validation:
  ```python
  from pydantic import BaseSettings, Field
  
  class Settings(BaseSettings):
      API_KEY: str = Field(..., description="Bot API key")
      SCHWAB_CLIENT_ID: str = Field(default="", description="Schwab OAuth client ID")
      DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
      
      class Config:
          env_file = ".env"
  ```
- [ ] Never log secrets; sanitize logs
- [ ] Support rotating secrets without restart (e.g., hot-reload endpoint for admins only)

**Effort:** 3-4 hours  
**Testing:** Verify .env.example has placeholders; check logs for no secrets

---

#### Gap 6: **Database Backups & Restore** ✅ DONE — scripts & docs (verified 2026-06-09; cron/restore-drill remain P1)
**Problem:** No documented backup/restore procedure.

**Implemented (scripts + docs):** `scripts/backup_postgres.sh` + `scripts/restore_postgres.sh`;
procedure documented in [POSTGRES_BACKUPS.md](POSTGRES_BACKUPS.md). Remaining hardening
(cron install — confirmed missing on `` 2026-06-09 — restore drill, offsite copy)
tracked as P1 in [ROADMAP.md](ROADMAP.md).

**Fix:**
- [x] Create `scripts/backup_postgres.sh`:
  ```bash
  #!/bin/bash
  BACKUP_DIR="/data/postgres_backups"
  mkdir -p "$BACKUP_DIR"
  docker exec market-pie5-bot-postgres pg_dump -U marketbot_user -d marketbot \
    > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
  ```
- [ ] Create cron job: `0 2 * * * /home/operator/market-pie5-bot/scripts/backup_postgres.sh` — *open: checked `` crontabs 2026-06-09, no market-pie5-bot backup cron installed (rankings-bot has one); tracked as P1 in [ROADMAP.md](ROADMAP.md)*
- [x] Document restore: `scripts/restore_postgres.sh` + [POSTGRES_BACKUPS.md](POSTGRES_BACKUPS.md)
- [ ] Test restore monthly; document location and retention (e.g., 30-day rolling backup) — *open, tracked as P1 in [ROADMAP.md](ROADMAP.md)*
- [ ] Add health check: `api/health` includes last backup timestamp — *open, tracked as P1 in [ROADMAP.md](ROADMAP.md)*

**Effort:** 3-4 hours  
**Testing:** Create backup → drop table → restore → verify data

---

#### Gap 7: **Graceful Shutdown** ✅ DONE (verified 2026-06-09)
**Problem:** Abrupt container shutdown may leave trades in limbo.

**Implemented:** FastAPI lifespan shutdown handler in `api/main.py` (state save + cleanup
after `yield`), `stop_signal: SIGTERM` + `stop_grace_period: 30s` in `docker-compose.yml`;
documented in [GRACEFUL_SHUTDOWN.md](GRACEFUL_SHUTDOWN.md).

**Fix:**
- [x] Add shutdown handling (lifespan) in `api/main.py`:
  ```python
  @app.on_event("shutdown")
  async def shutdown():
      logger.info("Server shutting down...")
      # Save bot state
      # Close database connections
      # Mark any in-flight trades as 'pending'
      logger.info("Shutdown complete")
  ```
- [x] Configure Docker to send SIGTERM with 30s grace period:
  ```yaml
  market-bot-api:
    stop_signal: SIGTERM
    stop_grace_period: 30s
  ```
- [x] Document graceful vs forced shutdown ([GRACEFUL_SHUTDOWN.md](GRACEFUL_SHUTDOWN.md))

**Effort:** 2-3 hours  
**Testing:** Send SIGTERM to container; verify logs show clean shutdown

---

#### Gap 8: **Logging & Observability** ⚠️ MEDIUM
**Problem:** Hard to diagnose production issues without centralized logging.

**Fix:**
- [ ] Structured logging: Use `structlog` for JSON output
  ```python
  import structlog
  logger = structlog.get_logger()
  logger.info("trade_executed", symbol="AAPL", quantity=10, side="BUY")
  ```
- [ ] Log retention: Keep 7 days of logs in container; rotate daily
- [ ] Expose `/api/logs` endpoint with filtering (symbol, status, date range)
- [ ] Optional: Send errors to external service (Sentry, CloudWatch) via webhook

**Effort:** 4-5 hours  
**Testing:** Run bot → check logs → filter by symbol → verify correctness

---

### 1.3 Production Checklist

**Before deploying to production, ensure:**

- [ ] **Website loads:** https://market-bot.example.com (no 502 or 503)
- [ ] **Auth works:** Login with test user → receive token → access protected routes
- [ ] **Database backups:** Auto backup running; test restore successful
- [ ] **Bot initializes:** Stop and restart bot → verify data loads and bot resumes
- [ ] **Retry logic:** Simulate network failure → verify retries and recovery
- [ ] **Secrets secured:** No API keys in logs or public files
- [ ] **Graceful shutdown:** Stop container → verify clean shutdown log
- [ ] **Health checks:** `/api/health` returns 200 with uptime and status

**Go-Live Readiness:** All 8 items above committed and tested.

---

## 2. Server: API Ready for Mobile

### 2.1 Current API Status ✅

- [x] **REST endpoints** — Bot data, trades, settings accessible
- [x] **CORS enabled** — Frontend can call API
- [x] **Auth system** — Login/logout + token validation

### 2.2 Gaps to Close

#### Gap A: **API Versioning & Stability Contract** ✅ DONE (verified 2026-06-09)

**Implemented:** versioned routers in `api/routes/v1/` (auth, bot, config, reports,
settings, stats, trades) mounted under `/api/v1/`; legacy `/api/...` paths still served.
Covered by `tests/backend/test_api_v1_integration.py`.

**Problem:** Endpoint paths may change; mobile app needs stable contract.

**Fix:**
- [x] Introduce `/api/v1/` prefix for all endpoints:
  ```
  POST  /api/v1/auth/login
  GET   /api/v1/trades
  GET   /api/v1/bot/status
  POST  /api/v1/bot/start
  ```
- [x] Keep old paths for backward compat (still served; no deprecation warning logged yet)
- [x] Document endpoints and changes ([MOBILE_API.md](MOBILE_API.md))
- [ ] Commit to semantic versioning: `MAJOR.MINOR.PATCH` — *not formalized; revisit at mobile launch*

**Effort:** 3-4 hours

---

#### Gap B: **Consistent Error Responses**
**Problem:** Error formats vary across endpoints; mobile app can't parse reliably.

**Fix:**
- [ ] Define error schema:
  ```json
  {
    "error": "invalid_credentials",
    "message": "Username or password incorrect",
    "status_code": 401,
    "timestamp": "2026-02-12T10:30:00Z"
  }
  ```
- [ ] Use middleware to catch exceptions and format consistently
- [ ] Document error codes: `400` (bad request), `401` (unauthorized), `403` (forbidden), `404` (not found), `500` (server error)
- [ ] Return 401 for invalid/missing token (not 403)

**Effort:** 2-3 hours

---

#### Gap C: **Token Management & Expiry** ✅ DONE (verified 2026-06-09)

**Implemented:** token expiry claims in `api/utils/jwt.py`; refresh endpoint
`POST /api/v1/auth/refresh` in `api/routes/v1/auth.py` (7-day grace period).
Covered by `tests/backend/test_auth_tokens.py` and `tests/backend/test_token_lifecycle.py`.

**Problem:** Mobile app needs to know how long tokens last and how to refresh.

**Fix:**
- [x] Add token expiry (`api/utils/jwt.py`):
  ```python
  token_data = {
      "sub": user_id,
      "exp": datetime.utcnow() + timedelta(hours=24),  # 24-hour expiry
      "iat": datetime.utcnow()
  }
  ```
- [x] Implement refresh endpoint:
  ```
  POST /api/v1/auth/refresh
  Headers: Authorization: Bearer <refresh_token>
  Returns: { "access_token": "change-me", "expires_in": 86400 }
  ```
- [x] Document token lifespan in API docs ([MOBILE_API.md](MOBILE_API.md))

**Effort:** 3-4 hours

---

#### Gap D: **Mobile API Documentation**
**Problem:** Front-end developers don't know endpoint signatures, auth flow, data shapes.

**Fix:**
- [ ] Create `docs/MOBILE_API.md`:
  ```markdown
  # Market Bot Mobile API
  
  **Base URL:** https://market-bot.example.com/api/v1
  
  ## Authentication
  
  ### Login
  POST /auth/login
  Body: { "username": "user", "password": "pass" }
  Response: { "access_token": "change-me", "expires_in": 86400 }
  
  ## Bot Status
  
  GET /bot/status
  Headers: Authorization: Bearer <token>
  Response: { "running": true, "symbol": "AAPL", "mode": "yfinance", ... }
  
  ## Trades
  
  GET /trades?limit=50&offset=0
  Headers: Authorization: Bearer <token>
  Response: { "trades": [...], "total": 150 }
  ```
- [ ] Keep docs in sync with code (use OpenAPI/Swagger if possible)

**Effort:** 2-3 hours

---

#### Gap E: **Config Endpoint (Optional)**
**Problem:** Mobile app can't know feature flags or required app version.

**Fix:**
- [ ] Create `GET /api/v1/config`:
  ```json
  {
    "minAppVersion": "1.0.0",
    "maintenanceMode": false,
    "features": {
      "live_trading": false,
      "advanced_orders": false
    },
    "apiVersion": "v1"
  }
  ```
- [ ] Mobile app checks on launch; shows "Update required" if `appVersion < minAppVersion`
- [ ] Shows "Maintenance" dialog if `maintenanceMode: true`

**Effort:** 1-2 hours

---

### 2.3 Mobile API Readiness Checklist

- [x] All endpoints under `/api/v1/` (auth, bot, trades, stats, reports, settings, config)
- [ ] Consistent error format (error code + message + 401 for auth) — *Gap B still open*
- [x] Token expiry documented; refresh endpoint implemented (`POST /api/v1/auth/refresh`)
- [x] `docs/MOBILE_API.md` complete with all endpoints and types
- [x] (Optional) Config endpoint for feature flags and version check (`GET /api/v1/config`)

**Go-Live for Mobile:** All items complete and tested on real device.

---

## 3. React Native Conversion Guide

### 3.1 Project Structure

Create `mobile/` directory at workspace root (same level as market-pie5-bot):

```
mobile/
├── app.json                      # Expo config
├── package.json
├── app/
│   ├── _layout.tsx              # Root navigation
│   ├── (auth)/
│   │   ├── login.tsx            # Login screen
│   │   └── signup.tsx           # (if enabled)
│   ├── (app)/
│   │   ├── _layout.tsx          # Main app navigation
│   │   ├── dashboard.tsx        # Bot status & quick actions
│   │   ├── trades.tsx           # Trade history
│   │   ├── settings.tsx         # User settings
│   │   └── details/[id].tsx     # Trade detail screen
│   └── +html.tsx                # Custom HTML (Expo Web)
├── src/
│   ├── api/
│   │   ├── client.ts            # Axios/fetch with Bearer auth
│   │   ├── bot.ts               # Bot status, trades, etc.
│   │   └── auth.ts              # Login, logout, token refresh
│   ├── context/
│   │   ├── AuthContext.tsx      # Auth state + login/logout
│   │   └── ConfigContext.tsx    # App config (feature flags, version)
│   ├── types/
│   │   ├── auth.ts              # User, Token types
│   │   ├── bot.ts               # Trade, BotStatus types
│   │   └── api.ts               # Error response type
│   ├── hooks/
│   │   ├── useAuth.ts           # Auth context hook
│   │   ├── useApi.ts            # API call with retry + error handling
│   │   └── useAsyncStorage.ts   # AsyncStorage helpers
│   └── utils/
│       ├── storage.ts           # AsyncStorage get/set token
│       ├── formatters.ts        # Date, currency formatting
│       └── logger.ts            # Structured logging
├── __tests__/
│   ├── api.test.ts              # API client tests
│   ├── auth.test.ts
│   └── screens.test.tsx
└── README.md                     # Setup and build instructions
```

---

### 3.2 Phases

#### Phase A: Setup and Core Infrastructure

**Duration:** 3-4 days  
**Owner:** Front-end dev lead

**Tasks:**

1. **Initialize Expo project:**
   ```bash
   npx create-expo-app market-bot-mobile --template
   cd market-bot-mobile
   npm install expo expo-router expo-splash-screen expo-secure-store asyncstorage-community
   npm install axios zod zustand react-native-date-time-picker
   npm install -D jest @testing-library/react-native typescript
   ```

2. **Create API client:**
   - File: `src/api/client.ts`
   - Handle Bearer token from secure storage
   - Support retry on 429/503 (use `with_retry` from backend)
   - Catch 401 → redirect to login
   - Use Axios with interceptors

3. **Create auth context:**
   - File: `src/context/AuthContext.tsx`
   - State: `user`, `token`, `loading`, `error`
   - Methods: `login(username, password)` → POST `/api/v1/auth/login` → save token
   - Methods: `logout()` → clear storage + clear state
   - Methods: `refresh()` → POST `/api/v1/auth/refresh`
   - On app launch, check if token exists; if so, auto-login

4. **Create storage helpers:**
   - File: `src/utils/storage.ts`
   - `saveToken(token)` → `expo-secure-store.setItemAsync(...)`
   - `getToken()` → `expo-secure-store.getItemAsync(...)`
   - `clearStorage()` → remove token + user data

5. **Set up navigation skeleton:**
   - File: `app/_layout.tsx` (root)
   - File: `app/(auth)/login.tsx`
   - File: `app/(app)/_layout.tsx` (main app)
   - Use Expo Router (file-based routing)
   - Auth stack when logged out; app stack when logged in

**Testing:** Manually test login flow; verify token is stored/retrieved.

---

#### Phase B: Auth & Login Screens

**Duration:** 2-3 days  
**Owner:** UI/UX or mobile dev

**Tasks:**

1. **Login screen:**
   - File: `app/(auth)/login.tsx`
   - UI: TextInput for username, password; Button for login
   - Use `useAuth()` hook to call `login(username, password)`
   - Show loading spinner during sign-in
   - Show error message if login fails (e.g., "Invalid credentials")
   - On success, navigate to main app
   - Optional: Remember username (not password) in AsyncStorage

2. **Signup screen (if enabled):**
   - Similar to login; POST `/api/v1/auth/signup` (if endpoint exists)
   - OR remove this and only allow admin-created accounts

3. **Settings/logout screen:**
   - File: `app/(app)/settings.tsx`
   - Show current user
   - Button: "Logout" → `useAuth().logout()` → navigate to login

**Testing:** Login with test account; logout; try invalid credentials.

---

#### Phase C: Main Screens

**Duration:** 4-5 days  
**Owner:** Mobile dev team

**Tasks:**

1. **Dashboard (Bot Status):**
   - File: `app/(app)/dashboard.tsx`
   - Endpoint: `GET /api/v1/bot/status`
   - Display: Bot online/offline, current symbol (if live), mode (yfinance/live), uptime
   - Action buttons: Start bot, stop bot, manual refresh
   - Auto-refresh every 10s (or poll with `useEffect` + interval)

2. **Trades List:**
   - File: `app/(app)/trades.tsx`
   - Endpoint: `GET /api/v1/trades?limit=50&offset=0`
   - Display: Table/list with columns: Date, Symbol, Side (BUY/SELL), Qty, Price, PnL
   - Support pagination (load more button or infinite scroll with FlashList)
   - Tap row → navigate to trade detail

3. **Trade Detail:**
   - File: `app/(app)/details/[id].tsx`
   - Endpoint: `GET /api/v1/trades/{id}`
   - Display: Full trade info, decision notes, time executed, fees
   - Optional: Chart of symbol price at trade time

4. **Settings Screen (Continued):**
   - Display app version (from `package.json`)
   - Display API version (from config endpoint)
   - Button: "Check for updates" → navigate to app store if update available

**Testing:** On physical device (iPhone or Android emulator):
- Load each screen
- Verify data displays correctly
- Test pagination/loading states
- Check error handling (e.g., offline → show "Cannot reach server")

---

#### Phase D: Polish & Error Handling

**Duration:** 2-3 days  
**Owner:** Mobile dev + QA

**Tasks:**

1. **Loading states:**
   - Show spinner/skeleton while data loads
   - Display "No data" message if list is empty
   - Show "Retrying..." if request fails, with retry button

2. **Error handling:**
   - 401 (Unauthorized) → logout + redirect to login with message
   - 5xx (Server error) → show error banner with retry button
   - Network offline → show "No internet" message; cache last data if possible
   - Timeout → show "Request timed out"; offer manual retry

3. **Accessibility:**
   - All buttons and inputs have semantic labels
   - Color contrast meets WCAG AA
   - Support screen reader (VoiceOver on iOS, TalkBack on Android)

4. **Offline support (optional):**
   - Cache trades list in AsyncStorage
   - Show cached data with "offline" badge if network is down
   - Queue trade actions (if POST /trades added) and sync when online

**Testing:** Test on both iOS and Android; use accessibility checker tool.

---

#### Phase E: Build & Release

**Duration:** 3-5 days (first time); 1 day for updates  
**Owner:** DevOps or mobile dev lead

**Tasks:**

1. **Build configuration:**
   - File: `app.json` (Expo)
     ```json
     {
       "expo": {
         "name": "Market Bot",
         "slug": "market-bot-mobile",
         "version": "1.0.0",
         "icon": "./assets/icon.png",
         "splash": { "image": "./assets/splash.png" },
         "platforms": ["ios", "android"],
         "android": {
           "package": "com.example.marketbot"
         },
         "ios": {
           "bundleIdentifier": "com.example.marketbot"
         }
       }
     }
     ```
   - Create icon (1024x1024) and splash (2048x2048)

2. **iOS build & distribution:**
   - Use EAS Build: `eas login` → `eas build --platform ios`
   - Create Apple Developer account + App ID + certificate
   - Submit to TestFlight for internal testing
   - Submit to App Store (review ~1-2 days)
   - Publish on App Store

3. **Android build & distribution:**
   - Use EAS Build: `eas build --platform android`
   - Create Google Play Developer account
   - Generate signing key: `eas credential`
   - Submit to Play Store (review ~few hours)
   - Publish on Play Store

4. **Version management:**
   - Bump `version` in `app.json` for each release
   - Tag git: `git tag v1.0.0`
   - Update changelog

**Testing:** Download from store on real device; verify login, trades, settings work.

---

### 3.3 Reusable Code from Web Frontend

**Existing code to reuse/adapt:**

1. **API types** (`frontend/src/types/`):
   - Copy `Trade`, `BotStatus`, `User` types to `mobile/src/types/`
   - Keep same naming for consistency

2. **Auth flow** (`frontend/src/context/AuthContext.tsx`):
   - Logic is similar; mobile uses `expo-secure-store` instead of `localStorage`
   - Reuse token validation logic

3. **API client** (`frontend/src/api/`):
   - Core HTTP logic can be adapted for React Native
   - Replace `fetch` with `axios` for better error handling

4. **Formatting utilities** (`frontend/src/utils/`):
   - Date formatting, currency formatting → copy as-is
   - Platform-specific code isolated in separate files

---

### 3.4 React Native App Checklist

**Screens:**
- [ ] Login screen (username + password)
- [ ] Dashboard (bot status, start/stop buttons)
- [ ] Trades list (pagination support)
- [ ] Trade detail (full info, optional chart)
- [ ] Settings (logout, version, links)

**Features:**
- [ ] Bearer token auth (from secure storage)
- [ ] Error handling (401 → logout, 5xx → retry, offline → message)
- [ ] Loading states (spinner, skeleton, "No data" message)
- [ ] Refresh endpoint supported (token expiry handling)
- [ ] Config endpoint integrated (version check, feature flags)

**Testing:**
- [ ] Manual on iOS device/simulator
- [ ] Manual on Android device/emulator
- [ ] Login/logout flow
- [ ] Offline handling
- [ ] Invalid token (401)

**Build & Release:**
- [ ] iOS: EAS Build → TestFlight → App Store
- [ ] Android: EAS Build → Play Store
- [ ] Signing certificates managed
- [ ] Version bumped for each release

---

## 4. Summary & Next Steps

### Final Checklist: Production + App Ready

**Server Production (14-20 days):**
1. [x] Startup recovery (Gap 1) — *done, verified 2026-06-09*
2. [ ] Retry logic (Gap 2) — *helper exists; full call-path audit tracked as P1 in [ROADMAP.md](ROADMAP.md)*
3. [ ] Data archival (Gap 3)
4. [ ] Write queue (Gap 4) — *Optional; skip if startup reliable*
5. [ ] Secrets security (Gap 5)
6. [x] Database backups (Gap 6) — *scripts & docs done; cron + restore drill remain P1*
7. [x] Graceful shutdown (Gap 7) — *done, verified 2026-06-09*
8. [ ] Structured logging (Gap 8) — *structlog only in `api/routes/logs.py`; rollout tracked as P1*
9. [ ] Production checklist passed

**Server for Mobile (5-7 days):**
1. [x] API versioning (`/api/v1/`) — *done, verified 2026-06-09*
2. [ ] Consistent error responses
3. [x] Token expiry + refresh endpoint — *done, verified 2026-06-09*
4. [x] Mobile API docs (`docs/MOBILE_API.md`)
5. [x] (Optional) Config endpoint (`GET /api/v1/config`)

**React Native App Phase A-B (5-7 days):**
1. [ ] Expo project + core infrastructure
2. [ ] Auth flow + login screen
3. [ ] Storage (async, secure token)

**React Native App Phase C-E (9-12 days):**
1. [ ] Main screens (dashboard, trades, detail, settings)
2. [ ] Error handling & loading states
3. [ ] Build & submit to stores

### Recommended Rollout

**Week 1-2:** Server production gaps + mobile API setup  
**Week 3:** React Native Phase A-B (infrastructure + auth)  
**Week 4-5:** React Native Phase C-D (screens + polish)  
**Week 6:** React Native Phase E (build & submit to stores)  

### Success Metrics

- **Server:** 1000+ trades/day without data loss; <2s API response time; 99.5% uptime
- **Mobile:** 1000+ downloads first month; 4.5+ star rating; <1% crash rate
- **Combined:** Users can trade and monitor from mobile app + web simultaneously

---

## References

- [Market Bot README](../README.md)
- [ROADMAP.md](../ROADMAP.md)
- [MISSION.md](../MISSION.md)
- Server: [docker-compose.yml](../docker-compose.yml)
- Mobile: Expo Docs https://docs.expo.dev
- React Native Navigation: https://reactnavigation.org (or Expo Router docs)
- Secure Storage: https://github.com/EvanBacon/expo-secure-store

