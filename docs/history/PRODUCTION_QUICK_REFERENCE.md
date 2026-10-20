# Production Quick Reference - Market-Pie5-Bot

**Last Updated:** February 2, 2026  
**Current Status:** Phase A Validation (Day 1/30)

---

## 🚨 Emergency Commands

### Immediate Stop (From Anywhere)
```bash
ssh operator@192.0.2.21 "pkill -9 -f 'python3.*main.py'"
```

### Graceful Emergency Stop
```bash
ssh operator@192.0.2.21 "~/market-bot/market-pie5-bot/scripts/emergency_stop.sh 'Manual override'"
```

### Check Bot Status
```bash
ssh operator@192.0.2.21 "~/market-bot/market-pie5-bot/scripts/bot_monitor.sh"
```

---

## 📊 Daily Monitoring

### Health Check (Run Daily)
```bash
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && ./scripts/bot_monitor.sh"
```

### Live Log Monitoring
```bash
ssh operator@192.0.2.21 "tail -f ~/market-bot/market-pie5-bot/bot_phase1_run.log"
```

### Recent Errors
```bash
ssh operator@192.0.2.21 "tail -500 ~/market-bot/market-pie5-bot/bot_phase1_run.log | grep -i 'error\|critical'"
```

### Trade Summary
```bash
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && python3 -c \"import json; trades=json.load(open('trade_history.json')); print(f'Total trades: {len(trades)}'); print(f'Last trade: {trades[-1]}' if trades else 'No trades')\""
```

---

## 🚀 Bot Control

### Start Bot (Manual)
```bash
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && nohup python3 main.py > bot_run.log 2>&1 &"
```

### Stop Bot (Graceful)
```bash
ssh operator@192.0.2.21 "pkill -TERM -f 'python3.*main.py'"
```

### Restart Bot
```bash
ssh operator@192.0.2.21 "pkill -f 'python3.*main.py'; sleep 5; cd ~/market-bot/market-pie5-bot && nohup python3 main.py > bot_run.log 2>&1 &"
```

---

## 🌐 Network Control

`ADMIN_TOKEN` must be an **admin** session JWT, e.g. from `POST /api/auth/login` with your
`ADMIN_USERNAME`/`ADMIN_PASSWORD`. Allow/forbid change the firewall and need an admin (since 2026-09-25).
Reading the status works with any signed-in user.

### Allow Internet Connection
```bash
curl -s http://127.0.0.1:8004/api/network/access/allow \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
```

### Forbid Internet Connection
```bash
curl -s http://127.0.0.1:8004/api/network/access/forbid \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
```

### Check Connection Status
```bash
curl -s http://127.0.0.1:8004/api/network/access \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
```

**Note:** When internet is forbidden, the bot can only access local network and localhost. External API calls (yfinance, Schwab) will be blocked.

---

## 🔐 Production Deployment (Phase C)

### Pre-Production Checklist
- [ ] Schwab API credentials configured in `.env`
- [ ] Alert system tested (email/SMS)
- [ ] Emergency procedures documented
- [ ] Capital limits set correctly
- [ ] PDT rules enabled
- [ ] Risk thresholds configured
- [ ] Backup/restore tested
- [ ] Team trained on emergency stop

### Enable Production Mode

**⚠️ WARNING: This enables real money trading!**

```bash
# Edit .env on operator
PAPER_TRADING_MODE=false
SCHWAB_SANDBOX_MODE=false
BOT_ENABLED=true

# Set capital limits
BOT_STARTING_CAPITAL=10000.00
BOT_RISK_THRESHOLD=0.02
BOT_TRAILING_STOP_PERCENT=0.03
```

### Start Production Bot via Systemd

```bash
# Install service (one time)
ssh operator@192.0.2.21 "sudo cp ~/market-bot/market-pie5-bot/scripts/market-bot.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable market-bot.service"

# Start service
ssh operator@192.0.2.21 "sudo systemctl start market-bot.service"

# Check status
ssh operator@192.0.2.21 "sudo systemctl status market-bot.service"

# View logs
ssh operator@192.0.2.21 "journalctl -u market-bot.service -f"
```

---

## 📈 Phase A Validation (Current)

**Duration:** February 2 - March 5, 2026 (30 days)  
**Mode:** Simulation (yfinance fallback)  
**Goal:** Validate Phase 1 features

### Daily Tasks (Week 1)
1. Run `bot_monitor.sh` once per day
2. Check for errors in logs
3. Verify earnings calendar working
4. Confirm trade duration tracking
5. Test stale position detection

### Weekly Tasks
1. Review trade history for anomalies
2. Check system resource usage
3. Test emergency stop procedure
4. Verify all monitoring scripts work
5. Document any issues found

### Completion Criteria
- [ ] 30 days of stable operation
- [ ] No critical errors
- [ ] Phase 1 features validated
- [ ] All monitoring tools tested
- [ ] Emergency procedures documented

---

## 📋 Alert Configuration

### Setup Email Alerts

**Edit `.env`:**
```bash
ALERTS_ENABLED=true
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=operator@example.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=operator@example.com

# Optional SMS via email gateway
SMS_GATEWAY=operator@example.com

# Alert thresholds
ALERT_MAX_DAILY_LOSS_PCT=5.0
ALERT_MIN_CAPITAL_PCT=10.0
```

### Test Alerts
```bash
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && python3 alert_manager_production.py"
```

---

## 🛠️ Troubleshooting

### Bot Not Starting
```bash
# Check for error in log
ssh operator@192.0.2.21 "tail -100 ~/market-bot/market-pie5-bot/bot_run.log"

# Check Python environment
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && python3 -m py_compile main.py"

# Check dependencies
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && python3 -c 'import pandas, yfinance, requests'"
```

### Bot Stopped Unexpectedly
```bash
# Check emergency stop marker
ssh operator@192.0.2.21 "cat ~/market-bot/market-pie5-bot/.emergency_stop"

# Check emergency stop log
ssh operator@192.0.2.21 "tail ~/market-bot/market-pie5-bot/emergency_stops.log"

# Check system logs
ssh operator@192.0.2.21 "journalctl -u market-bot.service --since '1 hour ago'"
```

### High CPU/Memory Usage
```bash
# Check resource usage
ssh operator@192.0.2.21 "top -b -n 1 | grep python3"

# Check bot process details
ssh operator@192.0.2.21 "ps aux | grep 'python3.*main.py'"

# Check log file size
ssh operator@192.0.2.21 "du -h ~/market-bot/market-pie5-bot/*.log"
```

### API Connection Issues
```bash
# Check API health
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && python3 -c 'import yfinance as yf; print(yf.download(\"AAPL\", period=\"1d\"))'"

# Check .env configuration
ssh operator@192.0.2.21 "cd ~/market-bot/market-pie5-bot && grep -i 'api_key\|schwab' .env | grep -v '^#'"
```

---

## 📞 Emergency Contacts

**Primary Admin:** [Your Name/Phone]  
**Schwab Support:** 800-435-4000  
**Alert Email:** [Your alert email]  
**SMS Gateway:** [Your SMS number]  

### Escalation Procedure
1. Run `emergency_stop.sh` immediately
2. Check `emergency_stops.log` for details
3. Review bot logs for errors
4. Contact Schwab if trades need to be unwound
5. Document incident for post-mortem

---

## 📝 Key Files

| File | Purpose | Location |
|------|---------|----------|
| `main.py` | Core bot logic | `/home/operator/market-bot/market-pie5-bot/` |
| `.env` | Configuration | `/home/operator/market-bot/market-pie5-bot/` |
| `trade_history.json` | All trades | `/home/operator/market-bot/market-pie5-bot/` |
| `bot_state.json` | Current state | `/home/operator/market-bot/market-pie5-bot/` |
| `bot_phase1_run.log` | Runtime logs | `/home/operator/market-bot/market-pie5-bot/` |
| `emergency_stops.log` | Stop events | `/home/operator/market-bot/market-pie5-bot/` |

---

## 🎯 Success Metrics

### Phase A (Current)
- **Uptime Target:** >95%
- **Error Rate:** <1% of checks
- **Trade Tracking:** 100% of trades logged
- **Feature Validation:** All Phase 1 features working

### Phase B (Sandbox)
- **API Success Rate:** >99%
- **Trades Executed:** 100+ in sandbox
- **Order Types Tested:** All (market, limit, stop)
- **Error Handling:** All scenarios tested

### Phase C (Production)
- **Week 1:** Max $1,000 capital, monitor 24/7
- **Week 2-3:** Gradually increase to 25%, then 50%
- **Week 4+:** Full capital deployment
- **ROI Target:** Beat S&P 500 (market-dependent)
- **Max Drawdown:** <10% from peak

---

## 🔄 Regular Maintenance

### Daily (During Production)
- [ ] Check `bot_monitor.sh` output
- [ ] Review trade history
- [ ] Verify capital above floor
- [ ] Check PDT day trade count
- [ ] Review any alert emails

### Weekly
- [ ] Review P&L performance
- [ ] Check system resources
- [ ] Rotate log files if >100MB
- [ ] Test emergency stop
- [ ] Update documentation

### Monthly
- [ ] Full system backup
- [ ] Review and optimize strategies
- [ ] Update API credentials if needed
- [ ] Performance analysis report
- [ ] Security audit

---

## 📚 Documentation

- [PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md) - Full 3-phase plan
- [EMERGENCY_PROCEDURES.md](EMERGENCY_PROCEDURES.md) - Detailed safety procedures
- [PHASE1_DEPLOYMENT_LIVE.md](PHASE1_DEPLOYMENT_LIVE.md) - Current deployment status
- [README.md](README.md) - Project overview
- [WEB_GUI_GUIDE.md](WEB_GUI_GUIDE.md) - Web interface guide

---

**Remember:** Always test in simulation mode before making production changes!
