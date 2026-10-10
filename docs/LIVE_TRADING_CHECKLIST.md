# Live Trading Checklist & Safety Procedures

**Date:** January 26, 2026  
**Purpose:** Safety checklist and procedures before going live

---

## ⚠️ **CRITICAL: Read Before Live Trading**

**Trading with real money carries significant risk. Follow this checklist to minimize risk.**

---

## 📋 Pre-Live Trading Checklist

### ✅ Phase 1: Paper Trading Validation (REQUIRED)

- [ ] **Extended Paper Trading:** Run for at least 20-50 trades
- [ ] **All Features Tested:** ML filter, portfolio optimizer, adaptive learning
- [ ] **Performance Validated:** Win rate acceptable, no critical errors
- [ ] **Integration Tests Pass:** `python3 validate_integrations.py`
- [ ] **Email Alerts Working:** Test alerts received successfully
- [ ] **ML Model Trained:** Model trained with real trade data (not just synthetic)
- [ ] **Configuration Reviewed:** All settings appropriate for live trading

**Minimum:** 20 trades in paper mode with all integrations active

---

### ✅ Phase 2: Configuration Safety Check

- [ ] **Paper Mode Disabled:** `PAPER_TRADING_MODE=false` (double-check!)
- [ ] **Capital Floor Set:** `CAPITAL_FLOOR_PERCENT=0.30` (30% floor recommended)
- [ ] **Position Sizes Conservative:** `BOT_POSITION_SIZE=0.01` (1% per position)
- [ ] **Max Positions Limited:** `BOT_MAX_OPEN_POSITIONS=3` (start small)
- [ ] **Risk Threshold Low:** `BOT_RISK_THRESHOLD=0.01` (1% risk)
- [ ] **Stop Loss Set:** `BOT_STOP_LOSS_PERCENT=0.06` (6% stop loss)
- [ ] **Take Profit Set:** `HIGH_SALE_PERCENT=0.10` (10% take profit)
- [ ] **PDT Compliance:** Understand PDT rules if capital < $25k

---

### ✅ Phase 3: API & Authentication

- [ ] **Schwab API Credentials:** Valid and configured
- [ ] **OAuth Token:** `token.json` exists and valid
- [ ] **API Tested:** Successfully connected to Schwab API
- [ ] **Sandbox Tested:** Tested in sandbox mode (if available)
- [ ] **Account Access:** Verified account access and permissions
- [ ] **Short Selling:** Enabled only if broker supports and you understand risks

---

### ✅ Phase 4: Monitoring & Alerts

- [ ] **Email Alerts Configured:** SMTP working, test emails received
- [ ] **Alert Severity Set:** `ALERT_MIN_SEVERITY=WARNING` or `CRITICAL`
- [ ] **Monitoring Plan:** How you'll monitor bot (email, logs, dashboard)
- [ ] **Alert Response Plan:** What to do when critical alerts received
- [ ] **Backup Monitoring:** Secondary monitoring method (if primary fails)

---

### ✅ Phase 5: Risk Management

- [ ] **Capital Amount:** Only risk capital you can afford to lose
- [ ] **Capital Floor:** Set appropriate floor (30% recommended)
- [ ] **Position Limits:** Conservative position sizes
- [ ] **Concentration Limits:** Max positions, short exposure limits
- [ ] **PDT Understanding:** Know PDT rules and limitations
- [ ] **Stop Loss:** Every position has stop loss protection
- [ ] **Take Profit:** Profit targets set appropriately

---

### ✅ Phase 6: System Readiness

- [ ] **System Stable:** Bot runs stable for extended periods
- [ ] **No Memory Leaks:** Long-running sessions tested
- [ ] **Network Stable:** Internet connection reliable
- [ ] **Backup Plan:** What to do if bot crashes or network fails
- [ ] **Recovery Procedures:** How to recover from errors
- [ ] **Resource Monitoring:** System resources adequate

---

### ✅ Phase 7: Documentation & Knowledge

- [ ] **User Guide Read:** `docs/USER_GUIDE.md` reviewed
- [ ] **Configuration Guide:** `docs/CONFIGURATION_BEST_PRACTICES.md` reviewed
- [ ] **Email Setup:** `docs/EMAIL_ALERT_SETUP.md` reviewed
- [ ] **Integration Guide:** `docs/INTEGRATION_COMPLETE.md` reviewed
- [ ] **Troubleshooting:** Know how to troubleshoot common issues
- [ ] **Emergency Stop:** Know how to stop bot immediately

---

## 🚨 Emergency Procedures

### Immediate Stop

**If something goes wrong:**

1. **Stop Bot Immediately:**
   ```bash
   # Find process
   ps aux | grep main.py
   
   # Kill process
   kill <PID>
   
   # Or use Ctrl+C if running in terminal
   ```

2. **Check Positions:**
   - Log into broker account
   - Review all open positions
   - Manually close if needed

3. **Review Logs:**
   - Check `alerts.log` for errors
   - Review console output
   - Check email alerts

4. **Assess Damage:**
   - Calculate losses
   - Review what went wrong
   - Document issue

---

## 📊 Daily Monitoring Checklist

### Morning (Before Market Open)

- [ ] Check email alerts from overnight
- [ ] Review previous day's trades
- [ ] Verify bot is running
- [ ] Check system resources
- [ ] Review configuration

### During Trading Hours

- [ ] Monitor email alerts
- [ ] Check bot status periodically
- [ ] Review trade execution
- [ ] Monitor capital level
- [ ] Watch for errors

### End of Day

- [ ] Review all trades
- [ ] Check performance metrics
- [ ] Verify capital level
- [ ] Review alerts
- [ ] Plan next day adjustments

---

## 🔍 Weekly Review Checklist

- [ ] **Performance Review:** Win rate, returns, drawdowns
- [ ] **Configuration Review:** Adjust settings based on performance
- [ ] **ML Model Review:** Retrain if needed
- [ ] **Alert Review:** Adjust alert thresholds
- [ ] **Risk Review:** Verify risk management working
- [ ] **System Review:** Check for issues, optimize

---

## ⚙️ Recommended Live Trading Settings

### First Week (Very Conservative)

```bash
PAPER_TRADING_MODE=false
BOT_STARTING_CAPITAL=5000.00        # Small capital
BOT_POSITION_SIZE=0.01              # 1% per position
BOT_MAX_OPEN_POSITIONS=2            # Only 2 positions
BOT_RISK_THRESHOLD=0.01             # 1% risk
CAPITAL_FLOOR_PERCENT=0.30          # 30% floor
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.70  # High confidence only
ALERT_MIN_SEVERITY=CRITICAL         # Only critical alerts
```

### After Successful Week (Moderate)

```bash
BOT_STARTING_CAPITAL=10000.00       # Increase capital
BOT_POSITION_SIZE=0.015             # 1.5% per position
BOT_MAX_OPEN_POSITIONS=3            # 3 positions
BOT_RISK_THRESHOLD=0.015            # 1.5% risk
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.65  # Slightly lower
ALERT_MIN_SEVERITY=WARNING          # More alerts
```

### Production (After Validation)

```bash
BOT_STARTING_CAPITAL=25000.00       # Full capital (PDT threshold)
BOT_POSITION_SIZE=0.02              # 2% per position
BOT_MAX_OPEN_POSITIONS=5            # 5 positions
BOT_RISK_THRESHOLD=0.02             # 2% risk
ML_SIGNAL_FILTER_MIN_CONFIDENCE=0.60  # Balanced
ALERT_MIN_SEVERITY=WARNING          # Standard alerts
```

---

## 🛡️ Safety Rules

### Never Do These:

1. ❌ **Don't skip paper trading** - Always test first
2. ❌ **Don't use money you can't afford to lose**
3. ❌ **Don't disable capital floor** - Always have protection
4. ❌ **Don't ignore alerts** - Respond to critical alerts immediately
5. ❌ **Don't trade without stop loss** - Always have protection
6. ❌ **Don't exceed position limits** - Stay within risk parameters
7. ❌ **Don't ignore PDT rules** - Understand and comply

### Always Do These:

1. ✅ **Start with paper trading** - Test everything first
2. ✅ **Use conservative settings** - Start small, scale gradually
3. ✅ **Monitor closely** - Check bot regularly
4. ✅ **Set capital floor** - Protect your capital
5. ✅ **Enable all alerts** - Stay informed
6. ✅ **Review performance** - Learn and improve
7. ✅ **Have backup plan** - Know how to stop bot

---

## 📞 Emergency Contacts

**If critical issues occur:**

1. **Stop Bot:** Kill process immediately
2. **Check Broker:** Log into broker account
3. **Review Positions:** Check all open positions
4. **Document Issue:** Record what happened
5. **Fix Configuration:** Correct any misconfigurations
6. **Test in Paper:** Test fixes in paper mode before resuming live

---

## ✅ Final Pre-Launch Checklist

**Before enabling live trading, verify:**

- [ ] All Phase 1-7 checklists completed
- [ ] Paper trading successful (20+ trades)
- [ ] All integrations validated
- [ ] Email alerts working
- [ ] Configuration reviewed and appropriate
- [ ] Capital floor set
- [ ] Position sizes conservative
- [ ] Monitoring plan in place
- [ ] Emergency procedures understood
- [ ] Ready to start with small capital

---

## 🎯 Success Criteria

**You're ready for live trading when:**

1. ✅ Paper trading shows consistent performance
2. ✅ All integrations working correctly
3. ✅ Email alerts functioning
4. ✅ Configuration optimized
5. ✅ Risk management in place
6. ✅ Monitoring plan ready
7. ✅ Emergency procedures understood

---

## 📚 Additional Resources

- **User Guide:** `docs/USER_GUIDE.md`
- **Configuration Guide:** `docs/CONFIGURATION_BEST_PRACTICES.md`
- **Integration Guide:** `docs/INTEGRATION_COMPLETE.md`
- **Testing Guide:** `docs/TESTING_GUIDE.md`

---

**⚠️ Remember: Trading involves risk. Start small, monitor closely, scale gradually!**
