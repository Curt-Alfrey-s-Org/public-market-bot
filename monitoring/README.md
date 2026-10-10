# Monitoring Directory

This directory contains background services and daemons for 24/7 market monitoring.

## Services

### news_daemon.py

**Purpose:** 24/7 news monitoring and market intelligence gathering

**Schedule:**
- News scraping: Every 1 hour (CNBC, Yahoo Finance, MarketWatch)
- Intelligence cleanup: Daily at midnight (removes events >90 days old)
- Database backup: Daily at 2 AM
- Status report: Every 6 hours

**Features:**
- Continuous news scraping from multiple sources
- Automatic symbol extraction from articles
- High-impact event detection (IPO, M&A, Regulatory)
- Market intelligence database management
- Daily backups with 7-day retention

**Usage:**

```bash
# Manual run (foreground)
cd ~/market-bot/market-pie5-bot
venv/bin/python monitoring/news_daemon.py

# Run as systemd service (recommended)
sudo cp monitoring/marketbot-news-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable marketbot-news-monitor
sudo systemctl start marketbot-news-monitor

# Check status
sudo systemctl status marketbot-news-monitor

# View logs
tail -f /tmp/news_daemon.log
```

**Configuration:**
- Edit `news_daemon.py` constants:
  - `SCRAPE_INTERVAL_HOURS`: Hours between scrapes (default: 1)
  - `CLEANUP_RETENTION_DAYS`: Days to keep events (default: 90)
  - `MAX_ARTICLES_PER_SOURCE`: Max articles per source (default: 50)

**Database:**
- Location: `data/market_intelligence.json`
- Backups: `data/backups/market_intelligence_YYYYMMDD_HHMMSS.json`
- Backup retention: 7 days

**Logs:**
- Daemon output: `/tmp/news_daemon.log`
- Error log: `/tmp/news_daemon_error.log`

**Resource Usage:**
- Memory limit: 512 MB
- CPU quota: 25%
- Network: HTTP requests every hour (minimal bandwidth)

## Future Services

### price_monitor.py (Planned)
- Real-time price tracking
- Unusual volume detection
- Gap detection (after-hours moves)

### market_conditions.py (Planned)
- VIX monitoring
- Sector rotation tracking
- Market breadth indicators

### alert_manager.py (Planned)
- User alert notifications
- Trade signal alerts
- System health alerts
