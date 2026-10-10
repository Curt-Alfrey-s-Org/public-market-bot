# Emergency Procedures and Safety Scripts

Created: February 2, 2026

## Overview

Critical safety infrastructure for production deployment of market-pie5-bot. These scripts provide emergency controls, health monitoring, and automated alerts.

## Files Created

### 1. emergency_stop.sh
**Location:** `scripts/emergency_stop.sh`

**Purpose:** Immediate kill switch for all bot processes

**Usage:**
```bash
# Basic emergency stop
./scripts/emergency_stop.sh

# With reason logging
./scripts/emergency_stop.sh "API connection lost"
```

**Features:**
- Graceful shutdown with SIGTERM (5 second wait)
- Force kill (SIGKILL) if process doesn't respond
- Logs all emergency stops to `emergency_stops.log`
- Creates `.emergency_stop` marker file
- Returns exit code 0 on success, 1 on failure

**Deployment:**
```bash
# On operator server
chmod +x scripts/emergency_stop.sh

# Test (will stop bot if running)
./scripts/emergency_stop.sh "Test emergency stop"
```

### 2. bot_monitor.sh
**Location:** `scripts/bot_monitor.sh`

**Purpose:** Comprehensive health monitoring

**Usage:**
```bash
# Single check
./scripts/bot_monitor.sh

# Continuous monitoring (updates every 60s)
./scripts/bot_monitor.sh --continuous
```

**Monitored Metrics:**
- Process status (running/stopped)
- CPU and memory usage
- Process uptime
- Log file size and activity
- Recent errors (last 1000 lines)
- Trade count and last trade
- System resources (load, disk, memory)

**Output Example:**
```
==========================================
BOT HEALTH CHECK - 2026-02-02 15:30:45
==========================================
✓ Bot Process: RUNNING (PID: 123456)
  CPU: 5.2% | Memory: 8.1%
  Started: Sun Feb  2 10:18:23 2026

Log File Status:
  Size: 2.3M | Lines: 45678
  Last modified: 2026-02-02 15:30:42
  ✓ Recent activity detected
  ✓ No recent errors

Trade History:
  Total trades: 47
  Last trade: 2026-02-02 15:25:10 - AAPL BUY @ 178.50
```

**Deployment:**
```bash
chmod +x scripts/bot_monitor.sh

# Add to crontab for periodic checks
crontab -e
# Add: */15 * * * * /home/operator/market-bot/market-pie5-bot/scripts/bot_monitor.sh >> /home/operator/monitor.log 2>&1
```

### 3. market-bot.service
**Location:** `scripts/market-bot.service`

**Purpose:** Systemd service for automatic restart and management

**Features:**
- Auto-start on system boot
- Auto-restart on failure (max 5 attempts in 5 minutes)
- Graceful shutdown with 60s timeout
- Security hardening (NoNewPrivileges, PrivateTmp)
- Separate logs for stdout/stderr

**Installation:**
```bash
# On operator server
sudo cp scripts/market-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable market-bot.service

# Start the service
sudo systemctl start market-bot.service

# Check status
sudo systemctl status market-bot.service

# View logs
journalctl -u market-bot.service -f
```

**Commands:**
```bash
# Start bot
sudo systemctl start market-bot.service

# Stop bot
sudo systemctl stop market-bot.service

# Restart bot
sudo systemctl restart market-bot.service

# Disable auto-start
sudo systemctl disable market-bot.service
```

### 4. alert_manager_production.py
**Location:** `alert_manager_production.py`

**Purpose:** Email and SMS alerts for critical events

**Features:**
- Email alerts via SMTP (Gmail, etc.)
- SMS alerts via carrier email gateways
- Alert levels: INFO, WARNING, ERROR, CRITICAL
- Pre-configured alerts for common scenarios
- Configurable thresholds

**Configuration (.env):**
```bash
# Enable alerts
ALERTS_ENABLED=true

# Email settings
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=operator@example.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=operator@example.com

# SMS (optional) - use carrier email gateway
SMS_GATEWAY=operator@example.com

# Alert thresholds
ALERT_MAX_DAILY_LOSS_PCT=5.0
ALERT_MIN_CAPITAL_PCT=10.0
ALERT_ON_TRADES=false  # Set true to alert on every trade
```

**Carrier Email Gateways:**
- AT&T: `operator@example.com`
- Verizon: `operator@example.com`
- T-Mobile: `operator@example.com`
- Sprint: `operator@example.com`

**Usage in Bot:**
```python
from alert_manager_production import get_alert_manager, AlertLevel

alert_mgr = get_alert_manager()

# Critical alert (email + SMS)
alert_mgr.alert_bot_stopped("API connection lost")

# Error alert (email only)
alert_mgr.alert_api_failure("Schwab API", "Connection timeout")

# Custom alert
alert_mgr.send_alert(
    AlertLevel.WARNING,
    "Custom Alert",
    "Something requires attention",
    send_sms=False
)
```

**Pre-configured Alerts:**
- `alert_bot_stopped()` - Bot process stopped
- `alert_excessive_loss()` - Daily loss exceeds threshold
- `alert_capital_floor_breach()` - Capital below safety floor
- `alert_api_failure()` - API connection issues
- `alert_trade_executed()` - Trade notification (optional)
- `alert_pdt_warning()` - Approaching PDT limit
- `alert_emergency_stop()` - Emergency stop triggered

**Testing:**
```bash
# Test email alerts
python3 alert_manager_production.py

# Check test alert in your inbox
```

## Emergency Contact Information

**Create emergency contact card:**
```bash
# File: emergency_contacts.txt
Bot Emergency: 555-123-4567
Primary Admin: John Doe (555-987-6543)
Schwab Support: 800-435-4000
System Admin: operator@example.com

Emergency Stop Command:
ssh operator@192.0.2.21 "~/market-bot/market-pie5-bot/scripts/emergency_stop.sh 'Manual override'"
```

## Integration with main.py

**Recommended additions to main.py:**

```python
# At top of file
from alert_manager_production import get_alert_manager, AlertLevel

# In __init__
self.alert_manager = get_alert_manager()

# On bot startup
self.alert_manager.send_alert(
    AlertLevel.INFO,
    "Bot Started",
    f"Trading bot started in {mode} mode\nCapital: ${self.total_capital:,.2f}"
)

# In trading loop error handling
except Exception as e:
    logger.critical(f"Critical error: {e}")
    self.alert_manager.alert_bot_stopped(str(e))
    raise

# In capital floor check
if self.total_capital < self.capital_floor:
    self.alert_manager.alert_capital_floor_breach(
        self.total_capital,
        self.capital_floor
    )

# In PDT tracking
if self.day_trades_this_week >= 2:
    self.alert_manager.alert_pdt_warning(self.day_trades_this_week)
```

## Pre-Production Checklist

Before enabling production trading:

- [ ] Test emergency_stop.sh in simulation mode
- [ ] Verify bot_monitor.sh detects running/stopped states
- [ ] Install and test systemd service (start/stop/restart)
- [ ] Configure SMTP credentials in .env
- [ ] Test email alerts with alert_manager_production.py
- [ ] Test SMS alerts (if configured)
- [ ] Add emergency contacts to documentation
- [ ] Set up monitoring cron job
- [ ] Document emergency procedures for all team members
- [ ] Create runbook with common scenarios

## Remote Emergency Access

**SSH Quick Commands:**
```bash
# Emergency stop from anywhere
ssh operator@192.0.2.21 "pkill -f 'python3.*main.py'"

# Check status
ssh operator@192.0.2.21 "pgrep -af 'python3.*main.py'"

# View recent errors
ssh operator@192.0.2.21 "tail -100 ~/market-bot/market-pie5-bot/bot_phase1_run.log | grep ERROR"

# Check capital
ssh operator@192.0.2.21 "grep -i 'total capital' ~/market-bot/market-pie5-bot/bot_phase1_run.log | tail -5"
```

## Testing Procedures

**Week 1 (Phase A Validation):**
1. Run `bot_monitor.sh` daily
2. Check for emergency stop marker: `ls -la .emergency_stop`
3. Verify alert emails arrive (test weekly)
4. Monitor systemd logs: `journalctl -u market-bot.service --since today`

**Week 2-3:**
1. Simulate emergency stop and verify recovery
2. Test systemd auto-restart: `sudo systemctl stop market-bot.service` (should restart)
3. Trigger test alerts for all scenarios
4. Document any false positives or missed alerts

**Week 4 (Pre-Sandbox):**
1. Full emergency drill
2. Verify all monitoring scripts work
3. Test alert thresholds
4. Update emergency contacts

## Production Deployment (Phase C)

When ready for production:

1. **Enable systemd service:**
   ```bash
   sudo systemctl enable market-bot.service
   sudo systemctl start market-bot.service
   ```

2. **Enable production alerts:**
   ```bash
   # In .env
   ALERTS_ENABLED=true
   ALERT_ON_TRADES=false  # Only for first week
   ```

3. **Set up monitoring cron:**
   ```bash
   # Check every 15 minutes
   */15 * * * * /home/operator/market-bot/market-pie5-bot/scripts/bot_monitor.sh >> /home/operator/monitor.log 2>&1
   ```

4. **Daily review checklist:**
   - Check bot_monitor.sh output
   - Review emergency_stops.log
   - Verify capital above floor
   - Check PDT count
   - Review trade history

## Notes

- All scripts are designed for Ubuntu/Linux environment (operator server)
- Emergency stop is fail-safe: if process doesn't respond, force kills
- Alert manager handles SMTP errors gracefully (logs but doesn't crash)
- Systemd service provides automatic recovery from crashes
- Monitor script can run continuously for live dashboard

## Next Steps

1. Deploy scripts to operator server
2. Test all emergency procedures in simulation mode
3. Configure email/SMS alerts
4. Install systemd service
5. Set up monitoring cron job
6. Document emergency contacts
7. Train team on emergency procedures
