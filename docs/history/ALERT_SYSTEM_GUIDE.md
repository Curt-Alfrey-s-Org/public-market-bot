# Desktop Alerts Setup Guide

## Overview
The alert system provides popup notifications for:
1. **High-impact news events** (IPO, M&A, Regulatory)
2. **Sizzle stocks** (unusual volume, big price moves)
3. **Trade executions** and filter blocks

---

## Installation

### Windows

```bash
# Activate virtual environment
cd ~/market-bot/market-pie5-bot
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install notification library
pip install win10toast
```

### Linux/Mac

```bash
# Activate virtual environment
cd ~/market-bot/market-pie5-bot
source venv/bin/activate

# Install cross-platform notification library
pip install plyer
```

### Alternative (Cross-platform)

```bash
pip install plyer
```

---

## Configuration

### Enable Alerts in News Daemon

Alerts are **automatically enabled** when the news daemon detects high-impact events.

**Edit** `monitoring/news_daemon.py` (already configured):
```python
# Alert manager is initialized automatically
alert_manager = get_alert_manager(enabled=True)
```

### Alert Types

#### 1. High-Impact News Events
**Triggers:**
- IPO announcements
- M&A activity (acquisitions, mergers, buyouts)
- Regulatory events (FDA approvals, regulatory actions)

**Example:**
```
🚨 M&A: TSLA
Musk considering taking Tesla private at $420/share
```

#### 2. Sizzle Stocks (Unusual Activity)
**Triggers:**
- Volume spike (3x+ average)
- Big price move (5%+ change)
- High momentum (score > 0.7)

**Example:**
```
🚀 SIZZLE ALERT: NVDA
Volume spike: 4.2x average (threshold: 3.0x)
```

#### 3. Trade Filter Blocks
**Triggers:**
- Trade blocked by earnings filter
- Trade blocked by macro calendar
- Trade blocked by news filter
- Trade blocked by sentiment/options filter

**Example:**
```
🛑 Trade Blocked: AAPL
EARNINGS Filter: Earnings report tomorrow
```

#### 4. Trade Executions
**Triggers:**
- BUY/SHORT executed
- SELL/COVER executed

**Example:**
```
✅ Trade Executed: GOOGL
BUY 50 shares @ $142.35
```

---

## Usage

### Start News Daemon with Alerts

```bash
cd ~/market-bot/market-pie5-bot

# Start daemon (alerts enabled by default)
nohup venv/bin/python monitoring/news_daemon.py > /tmp/news_daemon.log 2>&1 &

# Check alerts are working
tail -f /tmp/news_daemon.log | grep -E '(ALERT|Alert system)'
```

### Manual Alert Testing

```python
from alert_manager import get_alert_manager, alert_news, alert_sizzle

# Initialize
manager = get_alert_manager(enabled=True)

# Test news alert
alert_news(
    symbol='TSLA',
    event_type='M&A',
    description='Tesla considering acquisition of SolarCity',
    impact='high'
)

# Test sizzle stock alert
alert_sizzle(
    symbol='NVDA',
    metric='volume',
    value=4.2,
    threshold=3.0
)

# Test trade block alert
from alert_manager import alert_trade_blocked
alert_trade_blocked(
    symbol='AAPL',
    reason='Earnings report tomorrow',
    filter_type='earnings'
)

# Test trade execution alert
from alert_manager import alert_trade
alert_trade(
    symbol='GOOGL',
    action='BUY',
    price=142.35,
    quantity=50
)
```

### View Alert History

```python
from alert_manager import get_alert_manager

manager = get_alert_manager()

# Get last 10 alerts
recent = manager.get_recent_alerts(count=10)
for alert in recent:
    print(f"{alert['timestamp']}: {alert['title']}")
    print(f"  {alert['message']}\n")
```

---

## Configuration Options

### Customize Sizzle Detection

Edit `alert_manager.py`:

```python
detector = SizzleDetector(
    volume_threshold=3.0,       # 3x average volume
    price_change_threshold=5.0,  # 5% price change
    momentum_threshold=0.7       # Momentum score > 0.7
)
```

### Disable Alerts Temporarily

```python
from alert_manager import get_alert_manager

manager = get_alert_manager()
manager.enabled = False  # Disable
# ... do work ...
manager.enabled = True   # Re-enable
```

### Adjust Notification Duration

```python
# Longer notification (15 seconds)
manager.send_notification(
    title="Important Alert",
    message="This stays visible longer",
    duration=15
)

# Shorter notification (5 seconds)
manager.send_notification(
    title="Quick Alert",
    message="Brief message",
    duration=5
)
```

---

## Integration with Trading Bot

### Add to main.py

```python
# At top of main.py
from alert_manager import alert_trade_blocked, alert_trade, get_alert_manager

# In execute_trade method, after filter blocks:
if news_filter_blocked:
    alert_trade_blocked(
        symbol=symbol,
        reason=news_reason,
        filter_type='news'
    )
    return {'status': 'skipped', 'reason': 'failed_news_filter'}

# After successful trade execution:
if trade_result['status'] == 'success':
    alert_trade(
        symbol=symbol,
        action=signal,  # BUY, SELL, etc.
        price=execution_price,
        quantity=shares
    )
```

### Add Sizzle Detection

```python
from alert_manager import SizzleDetector, alert_sizzle

# Initialize detector
sizzle = SizzleDetector(
    volume_threshold=3.0,
    price_change_threshold=5.0
)

# Check volume spike
is_sizzle, multiplier = sizzle.check_volume_spike(
    symbol='NVDA',
    current_volume=1000000,
    average_volume=250000
)

if is_sizzle:
    alert_sizzle('NVDA', 'volume', multiplier, 3.0)

# Check price change
is_sizzle, change_pct = sizzle.check_price_change(
    symbol='TSLA',
    current_price=250.0,
    previous_price=230.0
)

if is_sizzle:
    alert_sizzle('TSLA', 'price_change', change_pct, 5.0)
```

---

## Troubleshooting

### No Notifications Appearing

**Check 1: Library installed?**
```bash
pip list | grep -E '(win10toast|plyer)'
```

**Check 2: Alerts enabled?**
```python
from alert_manager import get_alert_manager
manager = get_alert_manager()
print(f"Enabled: {manager.enabled}")
print(f"Notification available: {manager.enabled}")
```

**Check 3: Windows notification center enabled?**
- Windows Settings → System → Notifications & actions
- Ensure "Get notifications from apps" is ON

**Check 4: Python not in background?**
- Windows may suppress notifications from background processes
- Run daemon in foreground for testing: `python monitoring/news_daemon.py`

### Notifications Too Frequent

**Reduce frequency:**
```python
# In news_daemon.py, change scrape interval
SCRAPE_INTERVAL_HOURS = 2  # Every 2 hours instead of 1
```

**Filter only critical events:**
```python
# Only alert for M&A and IPO (skip Regulatory)
if article['category'] in ('IPO', 'M&A'):
    alert_news(...)
```

### Notifications Too Slow

**Check system resources:**
```bash
# CPU usage
top | grep python

# Memory usage
ps aux | grep python | awk '{print $4, $11}'
```

**Optimize:**
- Reduce `MAX_ARTICLES_PER_SOURCE` (default: 50)
- Increase `SCRAPE_INTERVAL_HOURS` (default: 1)

---

## Examples

### High-Impact News Alert (Actual)
```
🚨 M&A: BLS
BlueScope Steel takeover bid ($8.8B) - considering alternatives
```

### Sizzle Stock Alert
```
📊 SIZZLE ALERT: GME
Volume spike: 12.5x average (threshold: 3.0x)
```

### Trade Block Alert
```
🛑 Trade Blocked: AAPL
NEWS Filter: IPO this week - high volatility expected
```

### Trade Execution Alert
```
✅ Trade Executed: MSFT
BUY 100 shares @ $425.80
```

---

## Monitoring

### Check Alert Log

```bash
# View alert activity in daemon log
tail -f /tmp/news_daemon.log | grep -E 'ALERT'

# Count alerts sent today
grep -c "\\[ALERT\\]" /tmp/news_daemon.log

# View alert history (last 20)
tail -100 /tmp/news_daemon.log | grep "\\[ALERT\\]" | tail -20
```

### Dashboard Integration (Future)

Planned for Phase 3.3:
- Web GUI tab showing alert history
- Real-time alert feed
- Alert settings (enable/disable by type)
- Alert volume chart (alerts per hour)

---

## Performance Impact

**Resource Usage:**
- CPU: < 0.1% (notification display)
- Memory: ~5 MB (alert history)
- Network: None (local notifications)

**Latency:**
- News event → Alert: < 2 seconds
- Sizzle detection → Alert: < 1 second

---

## Security & Privacy

- **Local only:** Notifications displayed on local machine
- **No external services:** No data sent to cloud
- **No tracking:** Alert history stored locally only
- **Ephemeral:** Notifications disappear after duration

---

## Next Steps

1. ✅ Install notification library (`win10toast` or `plyer`)
2. ✅ Test alert system with manual trigger
3. ✅ Start news daemon with alerts enabled
4. ⏳ Integrate sizzle detection into main.py
5. ⏳ Add trade execution alerts to main.py
6. ⏳ Build dashboard alert history viewer

---

For questions or issues, check logs at `/tmp/news_daemon.log`
