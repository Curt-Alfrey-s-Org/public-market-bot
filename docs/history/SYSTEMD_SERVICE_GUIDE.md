# Systemd Service Setup Guide for market-pie5-bot

**Last Updated:** February 2, 2026

---

## Overview

This guide walks you through setting up the market-pie5-bot as a systemd service on your Raspberry Pi 5 or Linux machine. A systemd service allows the bot to:

- ✅ **Auto-start on system boot** - Bot runs automatically when your Pi starts
- ✅ **Auto-restart on crashes** - If the bot crashes, systemd automatically restarts it
- ✅ **Centralized logging** - All output goes to journalctl for easy monitoring
- ✅ **Easy management** - Control the bot with simple commands like `systemctl start/stop`
- ✅ **Headless operation** - Run without a display or terminal

---

## Prerequisites

1. **Bot Installation Complete**
   - Market-pie5-bot is installed at `/home/operator/market-bot/market-pie5-bot`
   - Virtual environment created: `./venv`
   - Dependencies installed: `pip install -r requirements.txt`

2. **Configuration Files**
   - `.env` file configured with your API keys and settings
   - `.env.example` exists as a reference

3. **User Account**
   - User `operator` exists on your system
   - User owns the bot directory and can execute Python scripts

---

## Installation Steps

### Step 1: Verify Prerequisites

```bash
# Check if bot directory exists
ls -la /home/operator/market-bot/market-pie5-bot/main.py

# Check if virtual environment exists
ls -la /home/operator/market-bot/market-pie5-bot/venv/

# Check if .env file exists
ls -la /home/operator/market-bot/market-pie5-bot/.env
```

If any of these fail, set up the bot first before proceeding.

### Step 2: Run Installation Script

```bash
# Make the script executable
chmod +x /home/operator/market-bot/market-pie5-bot/install_systemd_service.sh

# Run with sudo (required for systemd installation)
sudo bash /home/operator/market-bot/market-pie5-bot/install_systemd_service.sh
```

The script will:
- Verify your installation
- Copy the service file to `/etc/systemd/system/`
- Reload systemd
- Provide next steps and commands

### Step 3: Enable Auto-Start (Optional)

To have the bot start automatically on system boot:

```bash
sudo systemctl enable market-pie5-bot
```

To disable auto-start:

```bash
sudo systemctl disable market-pie5-bot
```

---

## Service Management

### Start the Service

```bash
sudo systemctl start market-pie5-bot
```

### Stop the Service

```bash
sudo systemctl stop market-pie5-bot
```

### Restart the Service

```bash
sudo systemctl restart market-pie5-bot
```

### Check Service Status

```bash
systemctl status market-pie5-bot
```

Output will show:
- **Active** or **Inactive** status
- **Loaded** or **Not Found** (if service file is recognized)
- **PID** of the running process
- **Last restart time** and **restart count**

---

## Monitoring and Logging

### View Real-Time Logs

Follow bot logs as they happen:

```bash
# Follow logs with auto-refresh (Ctrl+C to exit)
journalctl -u market-pie5-bot -f

# Follow logs with timestamps
journalctl -u market-pie5-bot -f --all
```

### View Historical Logs

```bash
# Last 50 lines
journalctl -u market-pie5-bot -n 50

# Last 100 lines
journalctl -u market-pie5-bot -n 100

# View logs since last boot
journalctl -u market-pie5-bot -b

# View logs from the last 2 hours
journalctl -u market-pie5-bot --since '2 hours ago'

# View logs from a specific date
journalctl -u market-pie5-bot --since '2026-02-01 00:00:00' --until '2026-02-02 00:00:00'

# View with pagination
journalctl -u market-pie5-bot | less

# Export logs to a file
journalctl -u market-pie5-bot > bot_logs.txt

# View with different output formats
journalctl -u market-pie5-bot -o json-pretty  # JSON format
journalctl -u market-pie5-bot -o short-precise  # More detailed timestamps
```

### Check Restart Status

```bash
# View service details including restarts
systemctl status market-pie5-bot

# View systemd logs for the service
journalctl -xe

# Check service restart count
systemctl show market-pie5-bot | grep NRestarts
```

---

## Systemd Service File Configuration

The service file `/etc/systemd/system/market-pie5-bot.service` contains:

```ini
[Unit]
Description=Market Pie5 Trading Bot Service
After=network-online.target
Wants=network-online.target

[Service]
User=operator
Group=operator
WorkingDirectory=/home/operator/market-bot/market-pie5-bot
EnvironmentFile=/home/operator/market-bot/market-pie5-bot/.env

Type=simple
ExecStart=/home/operator/market-bot/market-pie5-bot/venv/bin/python3 /home/operator/market-bot/market-pie5-bot/main.py

# Auto-restart configuration
Restart=always
RestartSec=10              # Wait 10 seconds before restarting
StartLimitInterval=60s     # In 60-second window
StartLimitBurst=3          # Allow max 3 restarts

StandardOutput=journal
StandardError=journal
Timeout=0

[Install]
WantedBy=multi-user.target
```

### Key Configuration Options

| Setting | Purpose | Current Value |
|---------|---------|---------------|
| `User` | Service runs as this user | `operator` |
| `WorkingDirectory` | Working directory for the bot | Bot installation path |
| `EnvironmentFile` | Load environment variables from file | `.env` file |
| `Restart` | Auto-restart behavior | `always` |
| `RestartSec` | Delay before restart | `10` seconds |
| `StartLimitInterval` | Time window for restart limits | `60` seconds |
| `StartLimitBurst` | Max restarts in time window | `3` restarts |
| `Timeout` | Timeout for operations | `0` (unlimited) |
| `KillSignal` | Signal to terminate process | `SIGTERM` |
| `TimeoutStopSec` | Max time to wait for graceful stop | `30` seconds |

### Customization

To modify the service configuration:

```bash
# Edit the service file
sudo nano /etc/systemd/system/market-pie5-bot.service

# After editing, reload systemd
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart market-pie5-bot
```

Common customizations:
- Change `RestartSec=10` to different value for faster/slower restarts
- Modify `StartLimitBurst=3` to allow more/fewer restart attempts
- Add resource limits (memory, CPU) if needed

---

## Restart Behavior

### How Auto-Restart Works

The service is configured to restart automatically:

1. **Bot crashes or exits** → Systemd detects this
2. **Wait RestartSec (10 seconds)** → Delay before restart
3. **Restart the bot** → `python3 main.py` runs again
4. **Check limits** → Within 60 seconds, maximum 3 restarts allowed
5. **If limit exceeded** → Service stops and requires manual intervention

### View Restart Activity

```bash
# Check total restart count
systemctl show market-pie5-bot | grep NRestarts

# View logs for recent restarts
journalctl -u market-pie5-bot -n 100

# Monitor restarts in real-time
watch -n 1 'systemctl status market-pie5-bot | grep -E "(Active|Restart|NRestarts|Process)"'
```

---

## Troubleshooting

### Service Won't Start

**Problem:** `systemctl start market-pie5-bot` fails

**Solution:**

```bash
# Check service status for error details
systemctl status market-pie5-bot

# View error logs
journalctl -u market-pie5-bot -n 50

# Check if .env file is readable
ls -la /home/operator/market-bot/market-pie5-bot/.env

# Check if virtual environment exists
ls -la /home/operator/market-bot/market-pie5-bot/venv/bin/python3

# Verify permissions
sudo -u operator /home/operator/market-bot/market-pie5-bot/venv/bin/python3 --version
```

### Service Keeps Restarting

**Problem:** Bot restarts repeatedly, logs show errors

**Solution:**

```bash
# Check what's causing the crash
journalctl -u market-pie5-bot -f

# Look for error messages in the logs
journalctl -u market-pie5-bot | grep -i error

# Test if bot runs manually
cd /home/operator/market-bot/market-pie5-bot
source venv/bin/activate
python3 main.py

# Check .env file for missing configuration
cat .env | grep -E "^[A-Z_]+=.*$"
```

### Service Not Found

**Problem:** `market-pie5-bot.service not found`

**Solution:**

```bash
# Check if service file exists
ls -la /etc/systemd/system/market-pie5-bot.service

# If not, run installation script again
sudo bash /home/operator/market-bot/market-pie5-bot/install_systemd_service.sh

# Reload systemd
sudo systemctl daemon-reload
```

### Logs Not Appearing

**Problem:** `journalctl -u market-pie5-bot` shows no output

**Solution:**

```bash
# Check if service is actually running
systemctl status market-pie5-bot

# Check all systemd logs for the service
journalctl -xe | grep market-pie5-bot

# View raw journal logs
journalctl --no-pager | tail -20

# Enable debug logging
systemctl set-environment LOGLEVEL=debug
systemctl restart market-pie5-bot
journalctl -u market-pie5-bot -f
```

---

## Monitoring Setup

### Create a Monitoring Cron Job

Add this cron job to monitor the bot's status:

```bash
# Edit crontab
crontab -e

# Add this line (checks bot status every 5 minutes)
*/5 * * * * systemctl is-active --quiet market-pie5-bot || /usr/bin/systemctl restart market-pie5-bot 2>&1 | logger -t market-pie5-bot-monitor
```

This will:
- Check if bot is running every 5 minutes
- Restart it if it's not running
- Log restart attempts to syslog

### View Cron Job Logs

```bash
# View cron activity
journalctl -u cron -f

# View market-pie5-bot cron logs
grep market-pie5-bot-monitor /var/log/syslog
```

### System Status Monitoring Script

Create `/usr/local/bin/check-bot-status.sh`:

```bash
#!/bin/bash
STATUS=$(systemctl is-active market-pie5-bot)
RESTART_COUNT=$(systemctl show market-pie5-bot | grep NRestarts | cut -d= -f2)

echo "Bot Status: $STATUS"
echo "Restarts: $RESTART_COUNT"

if [ "$STATUS" != "active" ]; then
    echo "WARNING: Bot is not running!"
    systemctl status market-pie5-bot
fi
```

Make executable and run:

```bash
chmod +x /usr/local/bin/check-bot-status.sh
/usr/local/bin/check-bot-status.sh
```

---

## Performance Notes

### Memory Usage

The service inherits resource limits from your system. To limit memory:

Edit `/etc/systemd/system/market-pie5-bot.service` and add:

```ini
[Service]
MemoryLimit=512M
CPUQuota=80%
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart market-pie5-bot
```

### Log Rotation

Systemd journal logs are automatically rotated. To configure:

```bash
# View journal disk usage
journalctl --disk-usage

# Limit journal size
sudo journalctl --vacuum-size=500M

# Limit journal to 7 days
sudo journalctl --vacuum-time=7d
```

---

## Next Steps

After setting up the systemd service:

1. **Enable auto-start:**
   ```bash
   sudo systemctl enable market-pie5-bot
   ```

2. **Test the service:**
   ```bash
   sudo systemctl restart market-pie5-bot
   systemctl status market-pie5-bot
   ```

3. **Monitor logs:**
   ```bash
   journalctl -u market-pie5-bot -f
   ```

4. **Set up monitoring cron job** (see Monitoring Setup section above)

5. **Test system restart:**
   - Reboot your system: `sudo reboot`
   - Bot should automatically start on boot
   - Verify: `systemctl status market-pie5-bot`

---

## Quick Reference

```bash
# Service management
sudo systemctl start market-pie5-bot
sudo systemctl stop market-pie5-bot
sudo systemctl restart market-pie5-bot
sudo systemctl status market-pie5-bot
sudo systemctl enable market-pie5-bot
sudo systemctl disable market-pie5-bot

# View logs
journalctl -u market-pie5-bot -f          # Follow live
journalctl -u market-pie5-bot -n 50       # Last 50 lines
journalctl -u market-pie5-bot --since '1 hour ago'

# Check restarts
systemctl show market-pie5-bot | grep NRestarts

# Edit service
sudo systemctl edit market-pie5-bot
sudo systemctl daemon-reload
```

---

## Support

For issues or questions:

1. Check logs: `journalctl -u market-pie5-bot -n 100`
2. Review this guide's Troubleshooting section
3. Check bot configuration in `.env`
4. Open an issue on GitHub with logs

---

**Installation Date:** February 2, 2026  
**Bot Version:** Refer to README.md  
**Service File:** `/etc/systemd/system/market-pie5-bot.service`
