# Alert System Testing Checklist

**Last Updated:** February 2, 2026  
**Status:** Implementation Complete - Ready for Testing

---

## Overview

The alert system has been fully implemented in the bot. This checklist guides you through manual testing to verify alerts work correctly with your email and SMS providers.

**Reference Documentation:**
- 📖 [EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md) - Complete email alert setup
- 📖 [SYSTEMD_SERVICE_GUIDE.md](SYSTEMD_SERVICE_GUIDE.md) - Service monitoring
- 📖 [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md) - Live trading setup with alerts

---

## Pre-Testing Setup

### 1. Email Configuration

#### Gmail Setup
```bash
# 1. Go to myaccount.google.com → Security
# 2. Enable 2-Step Verification
# 3. Create an App Password:
#    - Go to App Passwords
#    - Select Mail and Linux
#    - Generate password (16 characters)
# 4. Copy the generated password

# In .env file, set:
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_SMTP_USE_TLS=true
ALERT_EMAIL_USERNAME=operator@example.com
ALERT_EMAIL_PASSWORD=your-16-char-app-password
ALERT_EMAIL_FROM=operator@example.com
ALERT_EMAIL_TO=operator@example.com
```

#### Outlook/Office 365 Setup
```bash
# .env configuration:
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp-mail.outlook.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_SMTP_USE_TLS=true
ALERT_EMAIL_USERNAME=operator@example.com
ALERT_EMAIL_PASSWORD=your-password
ALERT_EMAIL_FROM=operator@example.com
ALERT_EMAIL_TO=operator@example.com
```

#### Custom SMTP Server
```bash
# For any SMTP server:
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=your-smtp-server.com
ALERT_EMAIL_SMTP_PORT=587  # or 25, 465
ALERT_EMAIL_SMTP_USE_TLS=true  # or false
ALERT_EMAIL_USERNAME=your-username
ALERT_EMAIL_PASSWORD=your-password
ALERT_EMAIL_FROM=operator@example.com
ALERT_EMAIL_TO=operator@example.com
```

### 2. Verify Configuration

```bash
cd /home/operator/market-bot/market-pie5-bot
source venv/bin/activate

# Test email configuration
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

print("Email Alert Configuration:")
print(f"  Enabled: {os.getenv('ALERT_EMAIL_ENABLED')}")
print(f"  SMTP Host: {os.getenv('ALERT_EMAIL_SMTP_HOST')}")
print(f"  SMTP Port: {os.getenv('ALERT_EMAIL_SMTP_PORT')}")
print(f"  From: {os.getenv('ALERT_EMAIL_FROM')}")
print(f"  To: {os.getenv('ALERT_EMAIL_TO')}")
EOF
```

---

## Test Cases

### Test 1: Email Alert - Trade Execution

**Purpose:** Verify bot sends email when a trade is executed

**Steps:**
1. Start bot in paper trading mode:
   ```bash
   export PAPER_TRADING_MODE=true
   python3 main.py
   ```

2. Wait for a trade to execute (check logs)

3. Check email inbox for trade alert

**Expected Result:**
- ✅ Email received within 2 minutes of trade
- ✅ Subject: `[Market Bot] Trade Executed: BUY SYMBOL @ PRICE`
- ✅ Email contains:
  - Trade details (symbol, side, price, quantity)
  - Account balance
  - Position info
  - Timestamp

**Failure Indicators:**
- ❌ Email not received
- ❌ Email in spam folder
- ❌ Email contains HTML only (no fallback)
- ❌ Missing information in body

---

### Test 2: Email Alert - Position Closed

**Purpose:** Verify alert when position is closed

**Steps:**
1. Wait for a position to close (or force close in paper trading)

2. Check email for position closure alert

**Expected Result:**
- ✅ Email received within 2 minutes
- ✅ Subject: `[Market Bot] Position Closed: SYMBOL`
- ✅ Email contains:
  - Entry and exit prices
  - Profit/loss amount and percentage
  - Exit reason
  - New account balance

**Failure Indicators:**
- ❌ Email not received
- ❌ Incomplete information
- ❌ Wrong profit/loss calculation

---

### Test 3: Email Alert - Daily Report

**Purpose:** Verify daily performance summary email

**Steps:**
1. Configure daily report email (if enabled)

2. Check for daily report email (typically at end of trading day)

**Expected Result:**
- ✅ Email received at configured time
- ✅ Subject: `[Market Bot] Daily Report - YYYY-MM-DD`
- ✅ Email contains:
  - Total trades for day
  - Win rate
  - Total profit/loss
  - Key statistics

---

### Test 4: Email Alert - Error/Warning

**Purpose:** Verify error alerts are sent

**Steps:**
1. Simulate an error condition:
   ```bash
   # Set invalid API key to trigger error
   export SCHWAB_API_KEY="change-me"
   python3 main.py
   ```

2. Check email for error alert

**Expected Result:**
- ✅ Email received with error details
- ✅ Subject contains: `[Market Bot] ERROR` or `WARNING`
- ✅ Email contains stack trace and context

---

### Test 5: Email Retry Logic

**Purpose:** Verify retry mechanism works for failed sends

**Steps:**
1. Configure invalid SMTP server:
   ```bash
   ALERT_EMAIL_SMTP_HOST=invalid.smtp.server
   ```

2. Execute a trade

3. Verify bot retries (check logs for retry messages)

4. Fix SMTP configuration

5. Verify retry succeeds and email is sent

**Expected Result:**
- ✅ Logs show `[Attempt 1/3]` for each retry
- ✅ After 3 attempts, logs show final failure
- ✅ After fixing config, email is sent on next trade
- ✅ No "email already sent" duplicate issues

**Log Example:**
```
2026-02-02 12:34:56 - Sending alert email... [Attempt 1/3]
2026-02-02 12:34:58 - Connection timeout, retrying... [Attempt 2/3]
2026-02-02 12:35:00 - Successfully sent alert email
```

---

### Test 6: HTML and Plain Text Formats

**Purpose:** Verify email clients receive both HTML and plain text

**Steps:**
1. Execute a trade

2. In email client:
   - View email as HTML (should be formatted nicely)
   - View email as plain text (should be readable)

**Expected Result:**
- ✅ HTML version displays charts, colors, formatting
- ✅ Plain text version is readable and includes all info
- ✅ Both versions contain identical information
- ✅ No encoding issues (special characters display correctly)

---

### Test 7: Email Address Validation

**Purpose:** Verify invalid email addresses are handled gracefully

**Steps:**
1. Set invalid recipient email:
   ```bash
   ALERT_EMAIL_TO=invalid@[invalid.com
   ```

2. Execute a trade

3. Check logs for validation error

**Expected Result:**
- ✅ Logs show validation error
- ✅ Bot doesn't crash
- ✅ Bot continues trading despite email error
- ✅ Logs suggest fixing email configuration

---

### Test 8: High-Volume Alert Throttling

**Purpose:** Verify alerts don't spam during high-volume trading

**Steps:**
1. Execute 10 trades in succession

2. Check inbox for emails

**Expected Result:**
- ✅ Receive email for each trade
- ✅ No rate-limiting (all emails arrive)
- ✅ Or if throttled: emails are queued and sent in batches
- ✅ No duplicate emails

---

### Test 9: Unicode and Special Characters

**Purpose:** Verify international characters display correctly

**Steps:**
1. Trade a stock with special characters in name

2. Check email for correct display

3. Verify emails from different locales work

**Expected Result:**
- ✅ All characters display correctly
- ✅ No mojibake or encoding errors
- ✅ Symbols, currency signs, accents all work

---

### Test 10: Email Configuration Changes at Runtime

**Purpose:** Verify changes to email settings take effect

**Steps:**
1. Note current email configuration

2. Disable emails:
   ```bash
   ALERT_EMAIL_ENABLED=false
   ```

3. Execute trade - should NOT receive email

4. Re-enable and execute trade - should receive email

**Expected Result:**
- ✅ Emails stop when disabled
- ✅ Emails resume when re-enabled
- ✅ No need to restart bot for changes to take effect

---

## Testing Log Checklist

### What to Look For in Logs

When testing, monitor `journalctl` for these log messages:

```bash
journalctl -u market-pie5-bot -f
```

**Successful Alert:**
```
[INFO] Trade executed: BUY AAPL @ 150.25
[INFO] Sending alert email to operator@example.com
[INFO] Successfully sent alert email (delivered in 0.45s)
```

**Alert Retry:**
```
[INFO] Sending alert email... [Attempt 1/3]
[WARNING] Failed to send email: Connection timeout
[INFO] Retrying... [Attempt 2/3]
[INFO] Successfully sent alert email (retried)
```

**Alert Disabled:**
```
[DEBUG] Alert email disabled, skipping notification
```

**Alert Error:**
```
[ERROR] Failed to send email after 3 attempts: Invalid credentials
[ERROR] Please verify ALERT_EMAIL_* settings in .env file
```

---

## Troubleshooting Guide

### Problem: Email Never Arrives

**Checklist:**
- [ ] Check spam/junk folder
- [ ] Verify `ALERT_EMAIL_TO` address is correct
- [ ] Check `ALERT_EMAIL_ENABLED=true` in .env
- [ ] Verify SMTP credentials are correct
- [ ] Check logs for errors: `journalctl -u market-pie5-bot | grep -i email`

**Solutions:**
```bash
# Test SMTP connection
python3 << 'EOF'
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
USERNAME = "operator@example.com"
PASSWORD = "change-me"

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(USERNAME, PASSWORD)
    print("✓ SMTP connection successful")
    server.quit()
except Exception as e:
    print(f"✗ SMTP connection failed: {e}")
EOF
```

---

### Problem: Email Contains No Information

**Checklist:**
- [ ] Email body is empty or very short
- [ ] Missing trade details
- [ ] Check logs for data fetch errors

**Solution:**
```bash
# Check bot logs for errors
journalctl -u market-pie5-bot -n 100 | grep -i "error\|warning"
```

---

### Problem: Gmail App Password Not Working

**Steps:**
1. Verify 2-Step Verification is enabled
2. Generate new app password
3. Copy exactly (includes spaces)
4. Paste into .env: `ALERT_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx`
5. Restart bot

---

### Problem: High Email Failure Rate

**Checklist:**
- [ ] SMTP server is accessible (run telnet test)
- [ ] Credentials are correct
- [ ] Check ISP/firewall for port 587 blocking
- [ ] Verify TLS settings match server requirements

**Fix:**
```bash
# Check firewall
sudo ufw allow 587/tcp

# Test SMTP port
telnet smtp.example.com 587
```

---

## Success Criteria

✅ **Alert Testing Complete When:**

- [ ] Test 1: Trade execution emails arrive
- [ ] Test 2: Position closure emails arrive
- [ ] Test 3: Daily report emails arrive (if configured)
- [ ] Test 4: Error alerts work
- [ ] Test 5: Retry logic functions correctly
- [ ] Test 6: HTML and plain text both work
- [ ] Test 7: Invalid emails handled gracefully
- [ ] Test 8: High volume trades don't crash alerts
- [ ] Test 9: Special characters display correctly
- [ ] Test 10: Runtime config changes work
- [ ] Logs show no errors or warnings
- [ ] No emails in spam folder
- [ ] Bot continues running after alert failures

---

## During Phase A Monitoring

### Daily Alert Verification

Each day during your 30-day Phase A:

```bash
# 1. Check bot is running
systemctl status market-pie5-bot

# 2. Verify emails received today
journalctl -u market-pie5-bot --since '24 hours ago' | grep -i "email"

# 3. Check alert counts
journalctl -u market-pie5-bot --since '24 hours ago' | grep -c "Successfully sent alert"

# 4. Look for errors
journalctl -u market-pie5-bot --since '24 hours ago' | grep -i "error.*email"
```

### Weekly Report Template

Create weekly summary:
```
Week of [DATE]:
- Total trades: [N]
- Total emails sent: [N]
- Failed emails: [N]
- Email latency: [avg time in seconds]
- Issues encountered: [list or "None"]
```

---

## Next Steps After Testing

1. **Systemd Service:** Set up auto-restart (see [SYSTEMD_SERVICE_GUIDE.md](SYSTEMD_SERVICE_GUIDE.md))

2. **Monitoring:** Add cron job to monitor bot and alerts

3. **Phase A:** Continue 30-day monitoring with alerts enabled

4. **Documentation:** Update README if any custom alert settings needed

---

## Reference

- [EMAIL_ALERTS_GUIDE.md](EMAIL_ALERTS_GUIDE.md) - Complete email setup and troubleshooting
- [LIVE_MODE_GUIDE.md](LIVE_MODE_GUIDE.md) - Live trading with alerts
- [SYSTEMD_SERVICE_GUIDE.md](SYSTEMD_SERVICE_GUIDE.md) - Service management and monitoring
- Bot source: Check `main.py` for alert implementation details

---

**Last Tested:** [Your Date]  
**Tester:** [Your Name]  
**Tests Passed:** [#/10]  
**Notes:** [Any observations]
