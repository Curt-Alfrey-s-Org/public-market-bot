# Work Tree: Production Readiness & React Native Conversion

**Quick reference for prioritized work items to get market-pie5-bot production-ready and mobile-capable.**  
**Last Updated:** February 12, 2026

---

## Phase 1: Server Production (14-20 days) ⚡ PRIORITY

### High Priority (Must Have)

#### 1. Startup Recovery (Days 1-2) — **CRITICAL**
```
Impact: Prevents data loss on restart; essential for reliability
Effort: 4-6 hours
Files: api/main.py, api/startup.py (new)

TODO:
- [ ] Add @app.on_event("startup") in api/main.py
- [ ] Implement initialize_bot_data() in api/startup.py
  - Check if bot_state.json or database is empty
  - If empty, fetch initial data from yfinance (with timeout)
  - Log status and timestamp
- [ ] Return 503 Service Unavailable until init complete
- [ ] Update /api/health to report initialization status
- [ ] Test: Database wipe → restart → verify data loads
- [ ] Document expected startup time in README
```

#### 2. API Retry Logic (Days 3-4) — **CRITICAL**
```
Impact: Handles network failures, timeouts; prevents silent data loss
Effort: 6-8 hours
Files: api/utils/retries.py (new), api/routes/bot.py (modify)

TODO:
- [ ] Create api/utils/retries.py with:
  - async def with_retry(func, max_retries=3, backoff_factor=2)
  - Handle TimeoutError, ConnectionError separately
  - Log attempts and backoff timing
- [ ] Wrap yfinance calls with with_retry()
- [ ] Wrap Schwab API calls with with_retry()
- [ ] Cache last successful fetch for fallback
- [ ] Distinguish transient (retry) vs permanent (fail) errors
- [ ] Test: Simulate network failure → verify retries → check logs
```

#### 3. Secrets Security (Days 5) — **HIGH**
```
Impact: Prevents API keys in docker-compose.yml and logs
Effort: 3-4 hours
Files: docker-compose.yml (.env), .env.example (update)

TODO:
- [ ] Review docker-compose.yml; move secrets to .env.production
- [ ] Update .env.example with placeholders (no real values)
- [ ] Add validation in api/config.py:
  - Read from environ via pydantic BaseSettings
  - Raise error if required secrets missing
- [ ] Add secret sanitization in logs (no API key output)
- [ ] Test: Run with .env.production → verify no secrets in logs
```

#### 4. Database Backups (Days 6) — **HIGH**
```
Impact: Data recovery if database corrupted or lost
Effort: 3-4 hours
Files: scripts/backup_postgres.sh (new), .cron (new)

TODO:
- [ ] Create scripts/backup_postgres.sh:
  docker exec market-pie5-bot-postgres pg_dump -U user -d db > backup_$(date).sql
- [ ] Create cron job: 0 2 * * * /path/to/backup_postgres.sh
- [ ] Documentation: Location, retention (30 days), restore steps
- [ ] Modify /api/health to include last_backup_timestamp
- [ ] Test: Create backup → drop table → restore → verify data
```

#### 5. Graceful Shutdown (Days 7) — **MEDIUM**
```
Impact: Prevents incomplete trades on shutdown; clean exit
Effort: 2-3 hours
Files: api/main.py

TODO:
- [ ] Add @app.on_event("shutdown") in api/main.py
  - Save bot state to file
  - Close database connections
  - Mark in-flight trades as 'pending'
  - Log shutdown complete
- [ ] Update docker-compose.yml:
  stop_signal: SIGTERM
  stop_grace_period: 30s
- [ ] Test: Send SIGTERM → verify clean exit in logs
```

#### 6. Structured Logging (Days 8) — **MEDIUM**
```
Impact: Easier debugging and monitoring in production
Effort: 4-5 hours
Files: api/config.py (logging setup)

TODO:
- [ ] Switch to structlog for JSON output:
  import structlog
  logger = structlog.get_logger()
  logger.info("event", symbol="AAPL", qty=10)
- [ ] Keep 7 days of logs; rotate daily
- [ ] Create GET /api/logs endpoint (filterable by symbol/date)
  - Return logs from trading_bot.log
  - Support filter params: symbol, status, start_date, end_date
- [ ] (Optional) Send errors to Sentry or CloudWatch
```

### Medium Priority (Should Have)

#### 7. Data Persistence & Archival (Days 9-10) — **MEDIUM**
```
Impact: Historical audit trail; data recovery
Effort: 5-7 hours
Files: database models (new archive table)

TODO:
- [ ] Create data_archives table:
  - bot_name, data_type, snapshot_date, data (JSONB), created_at
  - Index on (bot_name, snapshot_date DESC)
- [ ] Before UPDATE on trades/market data, move old row to archive
- [ ] Retention policy: 12 months
- [ ] Export archives quarterly to CSV
- [ ] Document restoration process
```

#### 8. Write Queue / Pending Operations (Days 11-12) — **OPTIONAL** (skip if startup reliable)
```
Impact: Handles database connection loss during trades
Effort: 6-8 hours
Files: api/models/pending_operations.py (new)

TODO:
- [ ] Create pending_operations table:
  - operation_type, data (JSONB), status, retry_count, created_at
- [ ] Before critical write (trade, balance update):
  1. Insert to pending_operations (guaranteed)
  2. Execute actual operation
  3. Mark as 'completed'
- [ ] On startup, retry any 'pending' operations
- [ ] Monitor and alert if count > threshold
```

---

## Phase 2: Mobile API Readiness (5-7 days)

### Required for App Launch

#### A. API Versioning (Day 1)
```
Impact: Stable contract for mobile app; can evolve backend without breaking apps
Files: api/routes/* (add /api/v1/ prefix)

TODO:
- [ ] Add /api/v1/ prefix to all endpoints:
  - Auth: POST /api/v1/auth/login, POST /api/v1/auth/refresh
  - Bot: GET /api/v1/bot/status, POST /api/v1/bot/start, POST /api/v1/bot/stop
  - Trades: GET /api/v1/trades, GET /api/v1/trades/{id}
- [ ] Keep old paths as deprecated (log warning)
- [ ] Document version contract in docs/MOBILE_API.md
- [ ] Update tests for new paths
```

#### B. Consistent Error Responses (Day 2)
```
Impact: Mobile app can parse errors reliably
Files: api/middleware/errors.py (new)

TODO:
- [ ] Define ErrorResponse schema:
  {
    "error": "invalid_credentials",
    "message": "Username or password incorrect",
    "status_code": 401,
    "timestamp": "2026-02-12T..."
  }
- [ ] Catch all exceptions in middleware
- [ ] Return 401 for invalid/missing token (not 403)
- [ ] Document error codes: 400, 401, 403, 404, 500
```

#### C. Token Management (Day 3)
```
Impact: Mobile app knows token lifespan; can refresh before expiry
Files: api/routes/auth.py (modify)

TODO:
- [ ] Add token expiry: exp = datetime.utcnow() + timedelta(hours=24)
- [ ] Implement POST /api/v1/auth/refresh
  - Accept refresh_token in Authorization header
  - Return new access_token + expires_in (seconds)
- [ ] Document token structure and lifespan
```

#### D. Mobile API Documentation (Days 4-5)
```
Impact: Front-end devs know endpoint signatures and auth flow
Files: docs/MOBILE_API.md (new)

TODO:
- [ ] Create docs/MOBILE_API.md:
  Base URL: https://market-bot.example.com/api/v1
  
  Auth:
  - POST /auth/login → { access_token, expires_in }
  - POST /auth/refresh → { access_token, expires_in }
  
  Bot:
  - GET /bot/status → { running, symbol, mode, ..., last_update }
  - POST /bot/start, POST /bot/stop
  - POST /bot/configure (settings)
  
  Trades:
  - GET /trades?limit=50&offset=0 → { trades[], total, has_more }
  - GET /trades/{id} → { trade with all fields }
  
  Config:
  - GET /config → { minAppVersion, features {}, maintenanceMode }
- [ ] Include request/response examples for each endpoint
- [ ] Document authentication (Bearer token in Authorization header)
```

#### E. Config Endpoint (Optional, Day 6)
```
Impact: Mobile app can check for required updates and feature flags
Files: api/routes/config.py (new)

TODO:
- [ ] Create GET /api/v1/config endpoint:
  {
    "minAppVersion": "1.0.0",
    "maintenanceMode": false,
    "features": {
      "live_trading": false,
      "advanced_orders": false
    },
    "apiVersion": "v1"
  }
- [ ] Mobile app calls on launch
- [ ] Show "Update required" if appVersion < minAppVersion
- [ ] Show "Maintenance" if maintenanceMode: true
```

---

## Phase 3: React Native App (9-16 days parallel or after Phase 2)

### Phase A: Infrastructure (Days 1-2)

```
Location: mobile/ directory (workspace root)
Tasks:
- [ ] npx create-expo-app market-bot-mobile
- [ ] npm install: expo, expo-router, expo-secure-store, asyncstorage-community, axios, zustand
- [ ] Create src/api/client.ts:
  - Axios instance with Bearer token from secure storage
  - Interceptors: 401 → logout, retry on 429/503
  - export apiClient
- [ ] Create src/context/AuthContext.tsx:
  - State: user, token, loading, error
  - login(username, password) → POST /api/v1/auth/login → save token
  - logout() → clear storage
  - refresh() → POST /api/v1/auth/refresh
  - useAuth() hook
- [ ] Create src/utils/storage.ts:
  - saveToken(), getToken(), clearStorage() using expo-secure-store
- [ ] Create app/_layout.tsx (root navigation):
  - If token exists: show AppStack (main screens)
  - Else: show AuthStack (login screen)
- [ ] Create app/(auth)/login.tsx:
  - TextInput for username, password
  - Button for login
  - Show loading spinner + error message
  - On success: navigate to main app
```

### Phase B: Auth & Settings (Days 3-4)

```
Tasks:
- [ ] Complete app/(auth)/login.tsx with error handling
- [ ] Create app/(app)/settings.tsx:
  - Show current user
  - Button: Logout → logout() → navigate to auth
  - Show app version (from package.json)
  - Show API version (from /api/v1/config)
- [ ] Create app/(app)/_layout.tsx (main app navigation):
  - Tabs: Dashboard, Trades, Settings
  - Or Drawer: Dashboard, Trades, Settings
```

### Phase C: Main Screens (Days 5-8)

```
Tasks:
- [ ] Create app/(app)/dashboard.tsx:
  - GET /api/v1/bot/status every 10s
  - Display: Running?, Symbol, Mode, Uptime
  - Buttons: Start, Stop, Refresh
  - Show loading state while fetching
- [ ] Create app/(app)/trades.tsx:
  - GET /api/v1/trades?limit=50&offset=0
  - FlatList with columns: Date, Symbol, Side, Qty, Price, PnL
  - "Load More" button for pagination
  - Tap row → navigate to detail
- [ ] Create app/(app)/details/[id].tsx:
  - GET /api/v1/trades/{id}
  - Show full trade info, decision notes, time executed, fees
  - Optional: Chart of symbol price at trade time
```

### Phase D: Polish & Error Handling (Days 9-10)

```
Tasks:
- [ ] Add loading states (spinner, skeleton) to all screens
- [ ] Add "No data" message when lists are empty
- [ ] Handle errors:
  - 401 → logout + redirect to login with message
  - 5xx → show error banner with retry button
  - Network offline → show "No internet" + cache last data
  - Timeout → show "Request timed out" + retry button
- [ ] Add accessibility:
  - Semantic labels on buttons/inputs
  - Color contrast WCAG AA
  - Screen reader support (VoiceOver/TalkBack)
- [ ] Optional: Offline cache in AsyncStorage
```

### Phase E: Build & Release (Days 11-16)

```
Tasks:
- [ ] Create app.json with config:
  - name: "Market Bot"
  - version: "1.0.0"
  - icon, splash images (1024x1024, 2048x2048)
  - platforms: ["ios", "android"]
  - Bundle IDs
- [ ] iOS:
  - eas login
  - eas build --platform ios
  - TestFlight submission
  - App Store release
- [ ] Android:
  - eas build --platform android
  - eas credential (signing key)
  - Play Store submission
- [ ] Version management:
  - app.json version bump per release
  - Git tag: v1.0.0
  - Update CHANGELOG
- [ ] Test on real devices (iPhone + Android)
```

---

## Summary: Effort & Timeline

| Phase | Component | Days | Dependencies |
|-------|-----------|------|--------------|
| 1 | Startup recovery | 2 | None |
| 1 | Retry logic | 2 | Phase 1a |
| 1 | Secrets security | 1 | None |
| 1 | DB backups | 1 | None |
| 1 | Graceful shutdown | 1 | None |
| 1 | Structured logging | 1 | Phase 1d |
| 1 | Data archival | 2 | Optional |
| 1 | Write queue | 2 | Optional (skip) |
| **Phase 1 Total** | **8-12 days** (14-20 with optional) | |
| 2 | API versioning | 1 | None |
| 2 | Error responses | 1 | Phase 2a |
| 2 | Token expiry | 1 | Phase 2a |
| 2 | API docs | 2 | Phase 2a,b,c |
| 2 | Config endpoint | 1 | Optional |
| **Phase 2 Total** | **5-7 days** | Phase 1 complete |
| 3a | Infrastructure | 2 | Phase 2 complete |
| 3b | Auth screens | 2 | Phase 3a |
| 3c | Main screens | 4 | Phase 3a,b |
| 3d | Polish | 2 | Phase 3c |
| 3e | Build & release | 6 | Phase 3a-d |
| **Phase 3 Total** | **9-16 days** | Phase 2 complete |

**Grand Total:** 4-6 weeks (22-45 days)

---

## Recommended Execution Plan

### Week 1-2: Phase 1 (Server Production)
- **Days 1-7:** High-priority items (1, 2, 3, 4, 5, 6)
- **Days 8-14:** Medium-priority items (7, optional 8)
- **Parallel:** Code review, testing

### Week 2-3: Phase 2 (Mobile API) + Start Phase 3a (Infrastructure)
- **Days 1-4:** API versioning, error responses, token expiry
- **Days 5-7:** API docs, config endpoint
- **Days 1-2 (parallel):** React Native infrastructure setup

### Week 4-5: Phase 3 (React Native Conversion)
- **Days 1-2:** Auth screens
- **Days 3-6:** Main screens (dashboard, trades, detail)
- **Days 7-8:** Polish & error handling
- **Parallel:** QA testing, device compatibility

### Week 6: Phase 3e (Build & Release)
- **Days 1-3:** Build iOS and Android, internal testing
- **Days 4-6:** App Store and Play Store submission + release

---

## Quick Checklist for Go-Live

**Server Production:**
- [ ] All Phase 1 high-priority items complete
- [ ] https://market-bot.example.com loads (no 502)
- [ ] Login works; auth validation server-side
- [ ] Database backups running; restore tested
- [ ] Bot initializes on startup
- [ ] Secrets not in logs or docker-compose
- [ ] Graceful shutdown works

**Mobile API:**
- [ ] All endpoints under `/api/v1/`
- [ ] Consistent error format (401 for auth failures)
- [ ] Token expiry implemented; refresh endpoint works
- [ ] docs/MOBILE_API.md complete

**React Native App:**
- [ ] Auth flow tested (login/logout)
- [ ] Dashboard loads bot status
- [ ] Trades list works with pagination
- [ ] Error handling for 401, 5xx, network
- [ ] Building + testing on iOS and Android devices
- [ ] Version 1.0.0 released to App Store and Play Store

---

## References

- **Full details:** [docs/PRODUCTION_READINESS_AND_REACT_NATIVE.md](PRODUCTION_READINESS_AND_REACT_NATIVE.md)
- **Roadmap:** [ROADMAP.md](../ROADMAP.md)
- **README:** [README.md](../README.md)
- **Port assignments:** [../.github/PORT_ASSIGNMENTS.md](../../.github/PORT_ASSIGNMENTS.md)

