# Production Readiness Checklist

**Target:** Real money trading with Schwab API  
**Current Status:** Phase 1 validation running on operator  
**Date:** February 2, 2026

---

## 🎯 Production Readiness Phases

### Phase A: Pre-Production Validation (IN PROGRESS)
**Goal:** Validate Phase 1 features in simulation  
**Timeline:** 30+ days (Feb 2 - Mar 5, 2026)  
**Status:** ✅ ACTIVE on operator

### Phase B: Schwab Sandbox Testing (NEXT)
**Goal:** Test with real Schwab API in sandbox mode  
**Timeline:** 7-14 days  
**Status:** ⏳ PENDING Phase A completion

### Phase C: Production Deployment (FINAL)
**Goal:** Live trading with real capital  
**Timeline:** Gradual rollout over 30 days  
**Status:** ⏳ PENDING Phase A & B completion

---

## 📋 Phase A: Current Validation Tasks

### ✅ Completed
- [x] PR #373 merged to main
- [x] Bot deployed to operator
- [x] Phase 1 features active (earnings calendar, stale detection)
- [x] Monitoring started

### 🔄 In Progress (30-day period)
- [ ] **Week 1 (Feb 2-9):** Initial stability monitoring
  - Bot uptime verification
  - Log error analysis
  - Feature validation
  
- [ ] **Week 2 (Feb 10-16):** Earnings filter effectiveness
  - Track trades skipped due to earnings
  - Measure earnings avoidance rate
  - Compare P&L impact
  
- [ ] **Week 3 (Feb 17-23):** Position duration analysis
  - Verify entry_time/exit_time accuracy
  - Analyze hold_duration_hours data
  - Check stale position alerts
  
- [ ] **Week 4+ (Feb 24-Mar 5):** Full metrics collection
  - Calculate ROI impact
  - Document edge cases
  - Performance optimization

### 📊 Validation Metrics to Collect
- [ ] Total trades executed
- [ ] Earnings filters triggered (count)
- [ ] Stale positions detected (> 48h)
- [ ] Average hold duration
- [ ] Win rate (with vs without earnings filter)
- [ ] P&L comparison
- [ ] Bot uptime percentage
- [ ] Error frequency
- [ ] Memory/CPU usage trends

---

## 📋 Phase B: Schwab Sandbox Setup

### 🔐 Authentication & Credentials
- [ ] **Schwab Developer Account**
  - [ ] Create app at developer.schwab.com
  - [ ] Get SCHWAB_API_KEY
  - [ ] Get SCHWAB_APP_SECRET
  - [ ] Configure callback URL (https://127.0.0.1:8182)
  - [ ] Note SCHWAB_ACCOUNT_ID from sandbox

- [ ] **Environment Configuration**
  - [ ] Copy .env.example to .env
  - [ ] Set SCHWAB_API_KEY
  - [ ] Set SCHWAB_APP_SECRET
  - [ ] Set SCHWAB_CALLBACK_URL
  - [ ] Set SCHWAB_ACCOUNT_ID
  - [ ] Set SCHWAB_SANDBOX_MODE=true
  - [ ] Set PAPER_TRADING_MODE=true
  - [ ] Verify SCHWAB_ENCRYPT_TOKEN=true

- [ ] **OAuth Token Generation**
  - [ ] Run initial OAuth flow: `python3 main.py`
  - [ ] Complete browser authorization
  - [ ] Verify token.json created and encrypted
  - [ ] Test token refresh (wait 30 min, verify auto-refresh)
  - [ ] Backup token.json securely

### 🧪 Sandbox Testing Tasks
- [ ] **API Connectivity**
  - [ ] Test account info retrieval
  - [ ] Test market data quotes
  - [ ] Test order placement (sandbox)
  - [ ] Test order cancellation
  - [ ] Test position queries
  - [ ] Verify error handling for API failures

- [ ] **Order Types & Execution**
  - [ ] Test market orders
  - [ ] Test limit orders
  - [ ] Test stop-loss orders
  - [ ] Test short selling (if enabled)
  - [ ] Test order rejection handling
  - [ ] Verify order status tracking

- [ ] **Risk Management Validation**
  - [ ] Test PDT compliance (day trade counting)
  - [ ] Test capital floor protection
  - [ ] Test position size limits
  - [ ] Test max open positions
  - [ ] Test trailing stops
  - [ ] Verify all safety checks active

- [ ] **Integration Testing**
  - [ ] Run 100+ sandbox trades
  - [ ] Verify earnings filter works with real API
  - [ ] Test stale position detection with real positions
  - [ ] Verify trade recording accuracy
  - [ ] Test recovery from API outages
  - [ ] Stress test with high volume

### 📝 Sandbox Documentation
- [ ] Document all API errors encountered
- [ ] Record order execution latencies
- [ ] Note any rate limit issues
- [ ] Document workarounds needed
- [ ] Create troubleshooting guide

---

## 📋 Phase C: Production Deployment

### 🛡️ Safety Measures (CRITICAL)
- [ ] **Emergency Controls**
  - [ ] Implement kill switch (manual stop)
  - [ ] Set up emergency contact system
  - [ ] Create rollback plan
  - [ ] Define max daily loss threshold
  - [ ] Test bot pause/resume functionality

- [ ] **Regulatory Compliance**
  - [ ] Verify PDT rules active (PAPER_TRADING_MODE=false enables PDT)
  - [ ] Confirm account meets $25k minimum for day trading
  - [ ] Validate proper order types for compliance
  - [ ] Review SEC/FINRA requirements
  - [ ] Ensure proper record keeping

- [ ] **Risk Limits Configuration**
  - [ ] Set BOT_TOTAL_CAPITAL (starting capital)
  - [ ] Set BOT_RISK_THRESHOLD (default: 2% per trade)
  - [ ] Set BOT_STOP_LOSS_PERCENT (default: 3%)
  - [ ] Set BOT_MAX_OPEN_POSITIONS (default: 10)
  - [ ] Configure capital floor (10% of start)
  - [ ] Set max drawdown threshold

### 🔧 Production Environment Setup
- [ ] **Server Configuration**
  - [ ] Choose production server (operator or dedicated)
  - [ ] Install all dependencies
  - [ ] Configure systemd service for auto-restart
  - [ ] Set up log rotation
  - [ ] Configure backup schedule
  - [ ] Test server reboot recovery

- [ ] **Environment Variables (Production)**
  - [ ] PAPER_TRADING_MODE=false ⚠️ REAL MONEY
  - [ ] SCHWAB_SANDBOX_MODE=false ⚠️ LIVE API
  - [ ] SCHWAB_API_ENABLED=on
  - [ ] Set appropriate BOT_TOTAL_CAPITAL
  - [ ] Enable ENABLE_PDT_RULES (auto-enabled in prod)
  - [ ] Configure alert email (SMTP settings)
  - [ ] Set LOG_LEVEL=INFO (not DEBUG)

- [ ] **Monitoring & Alerts**
  - [ ] Set up real-time alert system
  - [ ] Configure email alerts for:
    - Trading paused (capital floor)
    - API connection lost
    - Unexpected errors
    - Large losses (>5%)
    - PDT limit approaching
  - [ ] Set up SMS alerts (critical only)
  - [ ] Create monitoring dashboard
  - [ ] Set up log aggregation

### 📊 Production Monitoring
- [ ] **Daily Checks**
  - [ ] Bot status (running/paused)
  - [ ] Daily P&L review
  - [ ] Open positions count
  - [ ] Day trade count (PDT)
  - [ ] Error log review
  - [ ] API health status

- [ ] **Weekly Reviews**
  - [ ] Win rate analysis
  - [ ] Strategy performance comparison
  - [ ] Earnings filter effectiveness
  - [ ] Position duration trends
  - [ ] Risk-adjusted returns
  - [ ] Drawdown analysis

- [ ] **Monthly Audits**
  - [ ] Full P&L reconciliation with Schwab
  - [ ] Trade log audit
  - [ ] Cost basis verification
  - [ ] Tax preparation data
  - [ ] Strategy optimization review
  - [ ] Risk model validation

### 🚀 Gradual Rollout Plan
- [ ] **Week 1: Minimal Capital Test**
  - [ ] Start with $1,000 - $5,000 only
  - [ ] Max 2-3 positions
  - [ ] Monitor every trade manually
  - [ ] Verify all systems working
  - [ ] Goal: Zero issues

- [ ] **Week 2: Increased Capital**
  - [ ] Increase to 25% of target capital
  - [ ] Max 5 positions
  - [ ] Daily monitoring
  - [ ] Validate earnings filter in production
  - [ ] Goal: Positive P&L

- [ ] **Week 3: Half Capital**
  - [ ] Increase to 50% of target capital
  - [ ] Max 7 positions
  - [ ] Monitor stale position detection
  - [ ] Validate all Phase 1 features
  - [ ] Goal: Stable performance

- [ ] **Week 4+: Full Deployment**
  - [ ] Deploy 100% of target capital
  - [ ] Max 10 positions (or configured limit)
  - [ ] Weekly monitoring (not daily)
  - [ ] Full automation active
  - [ ] Goal: Consistent returns

---

## 🔒 Security Checklist

- [ ] **Credentials Protection**
  - [ ] Never commit .env to git (verify .gitignore)
  - [ ] Never commit token.json to git
  - [ ] Use encrypted tokens (SCHWAB_ENCRYPT_TOKEN=true)
  - [ ] Rotate encryption keys periodically
  - [ ] Secure backup of credentials (encrypted)
  - [ ] Limit access to production server

- [ ] **API Security**
  - [ ] Use HTTPS for all API calls (Schwab default)
  - [ ] Validate SSL certificates
  - [ ] Implement rate limit handling
  - [ ] Log all API requests (without credentials)
  - [ ] Monitor for suspicious activity
  - [ ] Set up IP whitelist if available

- [ ] **Server Security**
  - [ ] SSH key authentication only
  - [ ] Disable password auth
  - [ ] Firewall configured
  - [ ] Automatic security updates
  - [ ] Regular backup verification
  - [ ] Intrusion detection system

---

## ⚠️ Critical Pre-Production Checks

### Before Switching to PAPER_TRADING_MODE=false:

1. [ ] **Triple-Check Environment Variables**
   ```bash
   # MUST verify these settings:
   PAPER_TRADING_MODE=false       # ⚠️ REAL MONEY
   SCHWAB_SANDBOX_MODE=false      # ⚠️ LIVE API
   BOT_TOTAL_CAPITAL=<actual>     # ⚠️ REAL CAPITAL
   ```

2. [ ] **Verify Account Balance**
   - Actual Schwab account balance ≥ BOT_TOTAL_CAPITAL
   - Account meets PDT requirements ($25k+ for day trading)
   - Sufficient buying power for planned trades

3. [ ] **Test Kill Switch**
   - Manually stop bot: `pkill -f "python3 main.py"`
   - Verify all orders cancelled or closed
   - Test emergency contact procedure
   - Verify capital floor pauses trading

4. [ ] **Risk Limits Final Check**
   - Max loss per trade: 2% of capital
   - Max total drawdown: 10% (capital floor)
   - Max open positions: Configured limit
   - PDT day trade limit: 3 per 5 days (if <$25k)

5. [ ] **Backup & Recovery**
   - Backup all configuration files
   - Backup credentials (encrypted)
   - Document manual recovery procedure
   - Test recovery from backup

---

## 📞 Emergency Contacts & Procedures

### Emergency Stop Procedure
1. SSH to production server
2. Kill bot process: `pkill -f "python3 main.py"`
3. Verify process stopped: `ps aux | grep main.py`
4. Check open positions via Schwab app
5. Manually close positions if needed
6. Document incident

### Contact Information
- [ ] Primary admin: ___________________
- [ ] Secondary admin: ___________________
- [ ] Schwab support: 1-888-245-6864
- [ ] Emergency email: ___________________

### Critical Thresholds
- Max daily loss before manual intervention: $_______
- Max open position loss: $_______
- Max API error rate: _____%
- Bot down time threshold: ______ minutes

---

## 📈 Success Criteria

### Phase A (Validation - 30 days)
- ✅ Bot runs 99%+ uptime
- ✅ Zero critical errors
- ✅ Earnings filter reduces losses
- ✅ Stale position detection accurate
- ✅ All metrics collected

### Phase B (Sandbox - 14 days)
- ✅ 100+ successful sandbox trades
- ✅ All order types working
- ✅ PDT compliance verified
- ✅ Risk limits enforced
- ✅ API error handling robust

### Phase C (Production - 30 days)
- ✅ Positive net P&L
- ✅ Win rate ≥ 55%
- ✅ Max drawdown < 10%
- ✅ All safety systems working
- ✅ Zero regulatory violations

---

## 🎯 Next Immediate Actions

1. **Continue Phase A validation** (23 days remaining)
2. **Monitor operator bot daily** for first week
3. **Collect validation metrics** per checklist
4. **Register Schwab Developer Account** (can do in parallel)
5. **Begin drafting emergency procedures**

**Target Production Start:** March 10-15, 2026 (after Phase A & B complete)

