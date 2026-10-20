# Public Website Roadmap - market-bot.example.com

## Overview

Deploy market-pie5-bot as a **public demo website** showcasing the trading bot's capabilities in read-only/guest mode with user authentication.

**URL:** https://market-bot.example.com
**Server:** Ubuntu Pro with nginx (CNAME ready)
**Mode:** yfinance-only (Schwab integration grayed out for public)

## Timestamped Logs and Image Pulls

- Use timestamped Docker logs for debugging: `docker logs --timestamps -f --tail 80 <service>`
- Avoid pulling on start; prefer local images by setting `pull_policy: if_not_present` (or `never`) in compose, or run `docker-compose up -d --no-build`

## User Roles & Access Levels

### 1. Guest (No Account Required)
**Access:**
- ✅ View live trading dashboard (read-only)
- ✅ See performance charts and statistics
- ✅ Watch bot cycles in real-time
- ✅ View trade history (last 7 days)
- ❌ No Schwab integration visibility
- ❌ Cannot modify settings
- ❌ Cannot start/stop bot
- ❌ Limited data export

**Features Visible:**
- Live P&L chart
- Win/loss ratio
- Current positions (symbol, entry price, P&L%)
- Recent trades table
- Strategy indicators (SMA, RSI, MACD status)
- Market conditions (Phase 2 filters: macro, FOMO, options)

### 2. User (Free Registration)
**Access:**
- ✅ All Guest features
- ✅ View full trade history (all time)
- ✅ Export trades to CSV/JSON
- ✅ Create watchlists
- ✅ Set custom alerts (price targets, P&L thresholds)
- ✅ Access backtest results
- ✅ View Phase 1 & Phase 2 analytics
- ❌ No Schwab integration
- ❌ Cannot start/stop bot (view-only)
- ❌ Cannot modify bot parameters

**Registration:**
- Email + password (email verification required)
- Optional: GitHub/Google OAuth
- Free tier: No credit card required

### 3. Admin (Site Operators)
**Access:**
- ✅ All User features
- ✅ Start/stop bot
- ✅ Modify trading parameters (risk, capital, strategies)
- ✅ View Schwab integration settings (grayed out, config-only)
- ✅ User management (view users, disable accounts)
- ✅ System logs and diagnostics
- ✅ Deploy updates
- ✅ Database backup/restore

**Admin Panel Features:**
- Bot control (start/stop/restart)
- Parameter tuning (risk threshold, trailing stop, etc.)
- Strategy enable/disable
- Phase 2 filter configuration
- System health monitoring
- User activity logs

## Website Architecture

### Frontend (React/Dash)

**Current:** Dash app (web_gui.py)
**Enhancement:** Add authentication layer + role-based UI

**Pages:**

1. **Landing Page** (Public)
   - Hero section: "AI-Powered Trading Bot"
   - Feature highlights (Phase 1 + Phase 2)
   - Performance stats (last 30 days)
   - "Try Demo" (Guest) or "Sign Up" (User)

2. **Dashboard** (Guest/User/Admin)
   - Live trading view (updated every 5 seconds)
   - P&L chart (Plotly)
   - Position cards (symbol, entry, current, P&L%)
   - Trade feed (real-time updates)
   - Phase 2 indicators (macro events, FOMO alerts, options flow)

3. **Trade History** (Guest: 7d, User: All, Admin: All + exports)
   - Filterable table (date, symbol, action, P&L, strategy)
   - Export buttons (CSV, JSON)
   - Performance analytics (win rate, avg hold time, best/worst)

4. **Analytics** (User/Admin)
   - Strategy performance breakdown
   - Phase 2 filter effectiveness
   - Hold time distribution
   - Sector performance
   - Market condition correlation

5. **Settings** (Admin Only)
   - Bot parameters
   - Strategy toggles
   - Risk management
   - Phase 2 thresholds
   - User management

6. **Docs/Help** (All)
   - Trading strategy guide
   - Phase 2 feature explanations
   - FAQ
   - API documentation (for developers)

### Backend (FastAPI + Authentication)

**Current:** FastAPI server in `api/main.py`
**Enhancement:** Add JWT authentication + RBAC

**New Endpoints:**

```python
# Authentication
POST   /api/auth/register       # User registration
POST   /api/auth/login          # JWT token generation
POST   /api/auth/refresh        # Token refresh
GET    /api/auth/me             # Current user info

# User Management (Admin only)
GET    /api/users               # List all users
PUT    /api/users/{id}          # Update user (role, status)
DELETE /api/users/{id}          # Disable user

# Bot Control (Admin only)
POST   /api/bot/start           # Start trading
POST   /api/bot/stop            # Stop trading
POST   /api/bot/restart         # Restart bot
PUT    /api/bot/config          # Update parameters

# Public/Guest Endpoints
GET    /api/dashboard/stats     # Real-time stats (P&L, positions, trades)
GET    /api/dashboard/chart     # P&L time series
GET    /api/trades/recent       # Last N trades (Guest: 100, User: unlimited)

# User Endpoints
GET    /api/trades/export       # Export full history
POST   /api/watchlist           # Create/update watchlist
GET    /api/analytics           # Performance analytics

# WebSocket (Real-time updates)
WS     /api/ws/dashboard        # Live trading feed
```

### Database Schema

**New Tables:**

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- 'guest', 'user', 'admin'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table (JWT tracking)
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlists table
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(10) NOT NULL,
    alert_type VARCHAR(50),  -- 'price_above', 'price_below', 'pnl_target'
    threshold DECIMAL(10, 2),
    is_triggered BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Deployment Plan

### Phase 1: Infrastructure Setup (Week 1)

**Tasks:**
1. ✅ Domain ready: market-bot.example.com
2. ✅ Ubuntu Pro server with nginx
3. ⏳ SSL certificate (Let's Encrypt)
4. ⏳ Configure nginx reverse proxy to FastAPI
5. ⏳ Set up PostgreSQL database
6. ⏳ Configure systemd service for bot

**Nginx Config:**
```nginx
server {
    listen 443 ssl http2;
    server_name market-bot.example.com;

    ssl_certificate /etc/letsencrypt/live/market-bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/market-bot.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Phase 2: Authentication System (Week 2)

**Tasks:**
1. Install dependencies:
   ```bash
   pip install python-jose[cryptography] passlib[bcrypt] python-multipart
   ```

2. Create authentication module:
   - `api/auth.py` - JWT token generation/validation
   - `api/users.py` - User CRUD operations
   - `api/middleware.py` - Role-based access control (RBAC)

3. Database migrations:
   - Create users, sessions, watchlists, alerts tables
   - Seed admin account

4. Environment variables:
   ```bash
   SECRET_KEY=<generate-random-key>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   REFRESH_TOKEN_EXPIRE_DAYS=30
   ```

### Phase 3: Frontend Enhancement (Week 3)

**Tasks:**
1. Add authentication UI:
   - Login/Register modals
   - Password reset flow
   - Session management

2. Role-based UI rendering:
   - Guest: Read-only dashboard
   - User: Full analytics + exports
   - Admin: Bot controls + user management

3. Gray out Schwab features:
   - Settings page: Show Schwab section but disabled
   - Tooltip: "Schwab integration available for private deployments"

4. Add WebSocket for real-time updates:
   - Live trade feed
   - Position updates
   - P&L chart streaming

### Phase 4: yfinance-Only Mode (Week 4)

**Tasks:**
1. Create deployment config:
   ```python
   # config/public.py
   PUBLIC_MODE = True
   PAPER_TRADING_MODE = True  # Force paper trading
   SCHWAB_SANDBOX_MODE = False  # Disable Schwab entirely
   ENABLE_PDT_RULES = False  # No PDT for demo
   YFINANCE_FALLBACK = True  # Use yfinance exclusively
   ```

2. Modify main.py:
   - Skip Schwab authentication entirely
   - Use yfinance for all price data
   - Remove Schwab API calls

3. Update web_gui.py:
   - Gray out Schwab settings
   - Add "Demo Mode" banner
   - Show data source: "yfinance (15-min delayed)"

### Phase 5: Testing & Launch (Week 5)

**Tasks:**
1. Security audit:
   - SQL injection prevention
   - XSS protection
   - Rate limiting (prevent abuse)
   - CSRF tokens

2. Performance testing:
   - Load test (100+ concurrent users)
   - WebSocket stress test
   - Database query optimization

3. Monitoring:
   - Prometheus metrics
   - Grafana dashboards
   - Error tracking (Sentry)
   - Uptime monitoring (UptimeRobot)

4. Launch:
   - Beta test with 10 users
   - Public announcement
   - Documentation site
   - Video demo

## Security Considerations

### 1. Data Protection
- Passwords: bcrypt hashing (cost factor 12)
- JWT tokens: HS256 with random secret key
- HTTPS only (redirect HTTP to HTTPS)
- Rate limiting: 100 req/min per IP
- Database: Encrypted at rest

### 2. Bot Isolation
- yfinance-only: No real trading
- No Schwab credentials on public server
- Separate database (public vs private)
- Firewall rules (only port 443 open)

### 3. User Privacy
- No PII collection (email only)
- Optional analytics (Google Analytics opt-in)
- GDPR compliance (data export, deletion)
- Terms of Service + Privacy Policy

## Cost Estimate

**Monthly Operating Costs:**
- Domain: $12/year = $1/month
- Ubuntu Pro: $0 (free for personal use)
- SSL Certificate: $0 (Let's Encrypt)
- Server: $0 (already owned)
- Total: **~$1/month**

**One-Time Costs:**
- Development: 5 weeks @ contractor rates (if outsourced)
- Security audit: $500-1000 (optional)

## Success Metrics

**KPIs to Track:**
- Daily active users (DAU)
- Sign-up conversion rate (Guest → User)
- Average session duration
- Page views per session
- Trade history exports (engagement)
- Uptime % (target: 99.9%)

**Goals (6 months):**
- 1,000+ registered users
- 100+ daily active users
- <500ms average API response time
- 99.9% uptime

## Roadmap Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Infrastructure | nginx, SSL, PostgreSQL, systemd |
| 2 | Authentication | JWT, user tables, RBAC |
| 3 | Frontend | Login UI, role-based views, WebSockets |
| 4 | yfinance Mode | Public config, Schwab gray-out, demo banner |
| 5 | Testing & Launch | Security audit, load testing, beta launch |
| 6+ | Monitoring & Iteration | User feedback, feature requests, optimization |

## Future Enhancements (Post-Launch)

**Phase 6: Advanced Features**
- [ ] Paper trading competitions (leaderboard)
- [ ] Custom strategy builder (no-code)
- [ ] Mobile app (React Native)
- [ ] API access for developers (paid tier)
- [ ] Social features (share trades, follow strategies)
- [ ] AI assistant chatbot (trading Q&A)

**Phase 7: Monetization (Optional)**
- [ ] Premium tier ($10/month):
  - Private bot instance
  - Custom indicators
  - Priority support
  - Schwab integration (private deployment)
- [ ] Enterprise tier ($100/month):
  - Multi-bot management
  - White-label deployment
  - Custom development

## Technical Stack Summary

**Frontend:**
- Framework: Dash (Plotly) + React components
- Styling: TailwindCSS / Bootstrap 5
- Charts: Plotly.js
- WebSockets: Socket.IO

**Backend:**
- API: FastAPI (Python 3.10+)
- Authentication: JWT (python-jose)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Task Queue: Celery (for background jobs)

**Infrastructure:**
- Server: Ubuntu Pro 22.04 LTS
- Web Server: nginx
- SSL: Let's Encrypt (certbot)
- Process Manager: systemd
- Monitoring: Prometheus + Grafana

**Bot:**
- Mode: yfinance-only (paper trading)
- Strategies: All Phase 1 + Phase 2 features
- Data: yfinance (15-min delayed quotes)
- No real money trading

---

## Next Steps (Immediate)

1. **Set up SSL certificate:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d market-bot.example.com
   ```

2. **Install PostgreSQL:**
   ```bash
   sudo apt install postgresql postgresql-contrib
   sudo -u postgres createdb marketbot_public
   ```

3. **Create authentication module:**
   - Start with `api/auth.py`
   - Add user registration endpoint
   - Implement JWT token generation

4. **Update web_gui.py:**
   - Add login modal
   - Implement session management
   - Gray out Schwab sections

**Estimated Timeline:** 5 weeks to public launch
**Risk Level:** Low (no real trading, yfinance-only)
**Deployment Complexity:** Medium (authentication + RBAC)

---

**Last Updated:** 2026-02-02
**Status:** Planning Phase
**Owner:** Admin Team
