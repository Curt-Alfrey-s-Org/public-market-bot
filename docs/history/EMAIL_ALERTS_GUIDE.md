# Email Alerts Configuration Guide

## Overview

Market Pie5 Bot now includes a complete email alert system that sends notifications for important trading events. The system uses SMTP to send professionally formatted HTML and plain-text emails with retry logic and exponential backoff.

## Features

✅ **Professional Email Templates**
- HTML emails with beautiful styling and responsive design
- Plain text fallback for compatibility
- Clear subject lines and timestamps
- Branded with Market Pie5 Bot logo styling

✅ **Robust Delivery**
- Automatic retry with exponential backoff (3 attempts by default)
- Handles transient network errors gracefully
- Skips retry on authentication errors
- Connection pooling for efficiency

✅ **Security**
- TLS/SSL encryption support
- Secure credential management via environment variables
- Timeout protection (30 seconds)

✅ **Flexibility**
- Works with Gmail, Outlook, Office 365, and other SMTP providers
- Configurable retry behavior
- Can be disabled without affecting bot operation

## Configuration

### 1. Basic Setup

Copy the example configuration to your `.env` file:

```bash
# Alert Configuration
ENABLE_ALERTS=true
ALERT_EMAIL=operator@example.com

# SMTP Email Configuration
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=operator@example.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
SMTP_FROM_NAME=Market Pie5 Bot
SMTP_MAX_RETRIES=3
SMTP_RETRY_DELAY=5
```

### 2. Provider-Specific Setup

#### Gmail

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password
3. Configure `.env`:
   ```bash
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=your_16_char_app_password
   SMTP_USE_TLS=true
   ```

#### Outlook / Hotmail / Live.com

1. Use your regular email password (or app password if 2FA enabled)
2. Configure `.env`:
   ```bash
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=your_password
   SMTP_USE_TLS=true
   ```

#### Office 365

1. Use your Office 365 credentials
2. Configure `.env`:
   ```bash
   SMTP_SERVER=smtp.office365.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=your_password
   SMTP_USE_TLS=true
   ```

#### Yahoo Mail

1. Generate an App Password:
   - Go to: https://login.yahoo.com/account/security
   - Enable 2-Step Verification
   - Create an App Password
2. Configure `.env`:
   ```bash
   SMTP_SERVER=smtp.mail.yahoo.com
   SMTP_PORT=587
   SMTP_USERNAME=operator@example.com
   SMTP_PASSWORD=your_app_password
   SMTP_USE_TLS=true
   ```

#### Custom SMTP Server

For other providers or self-hosted SMTP servers:

```bash
SMTP_SERVER=smtp.yourprovider.com
SMTP_PORT=587  # or 465 for SSL, 25 for unencrypted
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_USE_TLS=true  # or false for port 465 (SSL)
```

### 3. Advanced Configuration

**Retry Behavior:**
```bash
# Maximum number of retry attempts (default: 3)
SMTP_MAX_RETRIES=3

# Initial retry delay in seconds (exponential backoff applied)
# Delays will be: 5s, 10s, 20s, etc.
SMTP_RETRY_DELAY=5
```

**Sender Name:**
```bash
# Customize the sender name that appears in recipient's inbox
SMTP_FROM_NAME=My Trading Bot
```

**Disable Alerts:**
```bash
# Disable email alerts completely
ENABLE_ALERTS=false
```

## Testing Email Configuration

### Method 1: Use the demo test script (Recommended!)

We've included a dedicated test script that makes it easy to verify your configuration:

```bash
# Run the email configuration test
python3 demo_email_alert.py
```

The script will:
1. Check all your SMTP configuration settings
2. Report any missing or incorrect values
3. Send a test email to verify everything works
4. Provide troubleshooting tips if there are issues

**Example output:**
```
======================================================================
  MARKET PIE5 BOT - EMAIL ALERT CONFIGURATION TEST
======================================================================

📋 Checking SMTP Configuration...

✅ SMTP_SERVER: smtp.example.com
✅ SMTP_PORT: 587
✅ SMTP_USERNAME: operator@example.com
✅ SMTP_PASSWORD: **************** (hidden)
✅ SMTP_USE_TLS: true
✅ ALERT_EMAIL: operator@example.com
✅ ENABLE_ALERTS: true

✅ Configuration looks good! Ready to test email sending.

======================================================================
Ready to send test email? (y/n):
```

### Method 2: Manual test script

If you prefer, create a simple test script to verify your configuration:

```python
#!/usr/bin/env python3
import os
os.environ['ENABLE_ALERTS'] = 'true'
os.environ['ALERT_EMAIL'] = 'operator@example.com'
# Set other SMTP variables...

from main import AlertSystem

# Send test alert
AlertSystem.send_alert(
    "Test Alert",
    "This is a test email from Market Pie5 Bot.\n\nIf you receive this, email alerts are working!"
)
```

### Method 3: Trigger an alert during bot operation

The bot will automatically send alerts for:
- Capital floor breaches (10% loss)
- API connectivity issues
- Schwab authentication failures
- Critical errors
- PDT rule violations (in live mode)

## Email Content Examples

### HTML Email

Recipients will see a beautifully formatted email with:
- Purple gradient header with bot branding
- Yellow alert box highlighting the subject
- Clean, readable message content
- Timestamp footer
- Professional styling

### Plain Text Email

For email clients that don't support HTML:
```
╔════════════════════════════════════════════════════════════════╗
║                  MARKET PIE5 BOT ALERT                         ║
╚════════════════════════════════════════════════════════════════╝

SUBJECT: Capital Floor Breach

Your trading capital has fallen below the 10% floor threshold.
Bot has been paused automatically for safety.

Current capital: $900.00
Floor threshold: $1,000.00 (10% of initial capital)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timestamp: 2026-01-21 12:34:56

This alert was automatically generated by Market Pie5 Bot.
Please do not reply to this email.
```

## Troubleshooting

### "SMTP authentication failed"

**Problem:** Wrong credentials or app password not used.

**Solutions:**
1. Verify your username and password in `.env`
2. For Gmail: Use an App Password, not your regular password
3. For Outlook: Try enabling "less secure app access" or use app password
4. Check for typos in SMTP_USERNAME and SMTP_PASSWORD

### "Connection timed out"

**Problem:** Network issues or wrong server/port.

**Solutions:**
1. Verify SMTP_SERVER is correct (e.g., `smtp.example.com`)
2. Verify SMTP_PORT is correct (587 for TLS, 465 for SSL)
3. Check firewall rules on Raspberry Pi
4. Ensure internet connectivity
5. Try increasing timeout (requires code modification)

### "Email alert would be sent to..." (not actually sent)

**Problem:** Missing SMTP configuration.

**Solutions:**
1. Ensure all SMTP_* variables are set in `.env`
2. Restart the bot after updating `.env`
3. Check logs for specific error messages

### "No recipient email configured"

**Problem:** ALERT_EMAIL not set.

**Solution:** Set ALERT_EMAIL in `.env`

### Emails going to spam

**Problem:** Email provider marking bot emails as spam.

**Solutions:**
1. Add the bot's email address to your contacts
2. Mark one email as "Not Spam"
3. Create a filter to always deliver bot emails to inbox
4. Use a dedicated email address for the bot

## Logs

Email alert activity is logged in multiple places:

1. **Console/File Logs:** Check `trading_bot.log` for email send attempts and errors
2. **Alerts Log:** Check `alerts.log` for all alerts (with or without email)
3. **Bot Output:** Real-time console output shows email status

Example log entries:
```
INFO - Email alert sent successfully to operator@example.com
WARNING - SMTP error on attempt 1/3: Connection timeout
INFO - Retrying in 5 seconds...
ERROR - Failed to send email after 3 attempts
```

## Security Best Practices

1. **Use App Passwords:** Never use your main email password
2. **Dedicated Email:** Consider using a separate email account just for the bot
3. **Secure .env:** Ensure `.env` file permissions are restricted (`chmod 600 .env`)
4. **Don't Commit:** Never commit `.env` file to version control
5. **TLS Enabled:** Always use TLS encryption (SMTP_USE_TLS=true)
6. **Regular Rotation:** Change app passwords periodically
7. **Monitor Access:** Check email account login history regularly

## Performance Considerations

- Email sending is non-blocking (errors don't crash the bot)
- Failed emails don't prevent other bot operations
- Retry logic uses exponential backoff to avoid hammering SMTP servers
- Connection pooling reduces overhead for multiple alerts
- 30-second timeout prevents hanging on network issues

## Alert Types

The bot will send email alerts for:

| Alert Type | When Triggered | Priority |
|-----------|---------------|----------|
| Capital Floor Breach | Capital drops below 10% threshold | High |
| PDT Violation Risk | Approaching day trade limit | High |
| API Connection Lost | Schwab API becomes unavailable | Medium |
| Authentication Error | OAuth token expired/invalid | High |
| Data Source Warning | Using fallback data (yfinance → random) | Medium |
| Critical Error | Unexpected error that stops bot | High |

## Customizing Alerts

To customize alert content or add new alert types, modify the `AlertSystem` class in `main.py`:

```python
# Send custom alert
AlertSystem.send_alert(
    "Custom Alert Subject",
    "Your custom message here.\n\nMultiple lines supported."
)
```

## FAQ

**Q: Can I send alerts to multiple email addresses?**  
A: Currently, only one recipient is supported. You can use email forwarding rules to distribute to multiple addresses.

**Q: Can I customize the email template?**  
A: Yes! Edit the `_create_html_template()` and `_create_plain_text()` methods in `main.py`.

**Q: Do alerts work in paper trading mode?**  
A: Yes! Alerts work in all modes (paper, sandbox, and live).

**Q: What if I don't want to receive some types of alerts?**  
A: Currently, all alerts are sent. Future versions may add alert filtering.

**Q: Can I use a local SMTP server?**  
A: Yes! Just configure SMTP_SERVER to your local server address.

**Q: How much does this cost?**  
A: Email alerts are free using Gmail, Outlook, and most other providers' free tiers.

## Support

For issues with email alerts:

1. Check this guide for troubleshooting steps
2. Review logs in `trading_bot.log` and `alerts.log`
3. Test with the provided test script
4. Open a GitHub issue with:
   - Your SMTP provider (Gmail, Outlook, etc.)
   - Error messages from logs (sanitize credentials!)
   - Steps you've already tried

---

**Last Updated:** January 21, 2026  
**Status:** Production Ready ✅
