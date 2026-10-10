# Email Alert System Setup Guide

**Date:** January 26, 2026  
**Status:** ✅ Complete - Ready for Testing

---

## 📧 Quick Setup

### 1. Configure SMTP Settings in `.env`

```bash
# Enable alerts
ENABLE_ALERTS=true
ALERT_EMAIL=operator@example.com

# SMTP Configuration
SMTP_SERVER=smtp.example.com        # For Gmail
SMTP_PORT=587                     # For TLS (Gmail, Outlook)
SMTP_USERNAME=operator@example.com
SMTP_PASSWORD=your_app_password   # See provider-specific instructions below
SMTP_USE_TLS=true
SMTP_FROM_NAME=Market Pie5 Bot

# Alert Severity Filtering
ALERT_MIN_SEVERITY=INFO           # Only send emails for this severity and above

# Email Rate Limiting
EMAIL_RATE_LIMIT_ENABLED=true
EMAIL_MAX_PER_HOUR=20             # Maximum emails per hour
EMAIL_MIN_INTERVAL_SECONDS=60     # Minimum seconds between emails
```

---

## 🔐 Provider-Specific Setup

### Gmail

1. **Enable 2-Factor Authentication** (required for app passwords)
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App-Specific Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "Market Pie5 Bot"
   - Copy the 16-character password

3. **Configure `.env`**
   ```bash
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App-specific password (no spaces)
   SMTP_USE_TLS=true
   ```

### Outlook / Office 365

1. **Use Regular Password** (if 2FA not enabled)
   ```bash
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=your_regular_password
   SMTP_USE_TLS=true
   ```

2. **Use App Password** (if 2FA enabled)
   - Go to: https://account.microsoft.com/security
   - Enable 2-Step Verification
   - Generate app password
   - Use app password in `SMTP_PASSWORD`

### Other Providers

**Yahoo Mail:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**Custom SMTP:**
```bash
SMTP_SERVER=your_smtp_server.com
SMTP_PORT=587  # or 465 for SSL, 25 for unencrypted
SMTP_USE_TLS=true  # or false for SSL/unencrypted
```

---

## 🧪 Testing

### Quick Test

```bash
# Test CRITICAL alert (default)
python3 test_email_alerts.py

# Test all severity levels
python3 test_email_alerts.py --test-all

# Test specific severity
python3 test_email_alerts.py --severity WARNING
```

### What to Check

1. **Email Received:**
   - Check inbox (and spam folder)
   - Verify HTML formatting
   - Check severity badge/color

2. **Rate Limiting:**
   - Send multiple alerts quickly
   - Should see rate limiting messages in logs
   - Only allowed number sent per hour

3. **Severity Filtering:**
   - Set `ALERT_MIN_SEVERITY=WARNING`
   - INFO alerts should not be emailed
   - WARNING and CRITICAL should be emailed

---

## 📊 Alert Severity Levels

### INFO
- **Use for:** Informational messages, routine updates
- **Examples:** Trading resumed, routine status updates
- **Color:** Blue (#17a2b8)

### WARNING
- **Use for:** Important warnings, non-critical issues
- **Examples:** PDT warnings, resource throttling
- **Color:** Yellow/Orange (#ffc107)

### CRITICAL
- **Use for:** Urgent issues requiring immediate attention
- **Examples:** Trading errors, capital floor breaches, system failures
- **Color:** Red (#dc3545)

---

## ⚙️ Configuration Options

### Alert Severity Filtering

```bash
# Only send CRITICAL alerts
ALERT_MIN_SEVERITY=CRITICAL

# Send WARNING and CRITICAL
ALERT_MIN_SEVERITY=WARNING

# Send all alerts (INFO, WARNING, CRITICAL)
ALERT_MIN_SEVERITY=INFO
```

### Rate Limiting

```bash
# Disable rate limiting (not recommended)
EMAIL_RATE_LIMIT_ENABLED=false

# Allow more emails per hour
EMAIL_MAX_PER_HOUR=50

# Shorter interval between emails
EMAIL_MIN_INTERVAL_SECONDS=30
```

### Retry Configuration

```bash
# More retry attempts
SMTP_MAX_RETRIES=5

# Longer retry delay
SMTP_RETRY_DELAY=10
```

---

## 🔍 Troubleshooting

### Email Not Received

1. **Check Configuration:**
   ```bash
   # Verify settings
   python3 -c "from main import ENABLE_ALERTS, ALERT_EMAIL, SMTP_USERNAME; print(f'Alerts: {ENABLE_ALERTS}, Email: {ALERT_EMAIL}, SMTP: {SMTP_USERNAME}')"
   ```

2. **Check Logs:**
   - Look for "Email alert sent successfully" messages
   - Check for SMTP errors
   - Review `alerts.log` file

3. **Test SMTP Connection:**
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.example.com', 587)
   server.ehlo()
   server.starttls()
   server.login('operator@example.com', 'your_password')
   server.quit()
   ```

### Authentication Errors

- **Gmail:** Use app-specific password, not regular password
- **Outlook:** Enable "Less secure app access" or use app password
- **2FA:** Must use app-specific password if 2FA enabled

### Rate Limiting Too Aggressive

- Increase `EMAIL_MAX_PER_HOUR`
- Decrease `EMAIL_MIN_INTERVAL_SECONDS`
- Or disable: `EMAIL_RATE_LIMIT_ENABLED=false`

### Too Many Emails

- Increase `ALERT_MIN_SEVERITY` (e.g., to WARNING or CRITICAL)
- Enable rate limiting
- Reduce `EMAIL_MAX_PER_HOUR`

---

## 📝 Alert Examples

### Critical Alert (Trading Error)
```
Subject: [CRITICAL] Live Trading Error
Severity: CRITICAL
Color: Red
```

### Warning Alert (PDT Warning)
```
Subject: [WARNING] PDT Warning
Severity: WARNING
Color: Yellow
```

### Info Alert (Trading Resumed)
```
Subject: [INFO] Trading Resumed
Severity: INFO
Color: Blue
```

---

## ✅ Verification Checklist

- [ ] SMTP credentials configured in `.env`
- [ ] `ENABLE_ALERTS=true` set
- [ ] `ALERT_EMAIL` set to your email
- [ ] Test email received successfully
- [ ] HTML formatting looks correct
- [ ] Severity badges/colors display properly
- [ ] Rate limiting works (if enabled)
- [ ] Severity filtering works (if configured)

---

## 🎯 Next Steps

1. **Configure SMTP credentials** in `.env`
2. **Run test script:** `python3 test_email_alerts.py --test-all`
3. **Verify emails received** in inbox
4. **Adjust configuration** as needed
5. **Monitor alerts** during live trading

---

**Ready for production use!**
