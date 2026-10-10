# YFinance Mode Auto-Configuration

**Date:** January 26, 2026  
**Feature:** Automatic configuration when yfinance mode is detected

---

## Overview

When the bot detects that it's running in yfinance mode (simulation mode without Schwab API), it automatically configures optimal settings for training and development.

---

## Automatic Configuration

When `using_yfinance_sim = True`, the bot automatically sets:

### 1. Paper Trading Mode: **ENABLED**
- Forces `PAPER_TRADING_MODE=true`
- Ensures no real money is used

### 2. Sandbox Mode: **DISABLED**
- Forces `SCHWAB_SANDBOX_MODE=false`
- Pure simulation mode (no API required)

### 3. Schwab API: **DISABLED**
- Forces `SCHWAB_API_ENABLED=off`
- Uses yfinance for all data

### 4. Continuous Trading: **ENABLED**
- Forces `WEB_GUI_CONTINUOUS_TRADING=true`
- Keeps bot running continuously

### 5. Debug Mode: **ENABLED**
- Forces `WEB_GUI_DEBUG=true`
- Enables detailed logging

### 6. PDT Rules: **ENABLED**
- Forces `ENABLE_PDT_RULES=true`
- Enforces pattern day trading rules for realistic simulation

---

## Implementation

### Auto-Configuration Method

**Location:** `main.py` → `TradingBot._auto_configure_yfinance_mode()`

**When Called:**
- After `_initialize_schwab_authenticator()` in `__init__`
- Only runs if `self.using_yfinance_sim = True`

**What It Does:**
1. Checks if yfinance mode is active
2. Automatically sets environment variables
3. Updates global configuration variables
4. Logs all changes

**Example Output:**
```
============================================================
AUTO-CONFIGURING FOR YFINANCE MODE
============================================================
✓ Paper trading mode: ENABLED (auto-configured)
✓ Sandbox mode: DISABLED (auto-configured)
✓ Schwab API: DISABLED (auto-configured)
✓ Continuous trading: ENABLED (auto-configured)
✓ Debug mode: ENABLED (auto-configured)
✓ PDT Rules: ENABLED (auto-configured)
============================================================
YFINANCE MODE AUTO-CONFIGURATION COMPLETE
============================================================
```

---

## Trade Activity Monitoring

### Feature: No-Trade Alerts

The bot monitors trade activity and sends alerts when no trades are happening.

**Location:** `main.py` → `TradingBot._check_trade_activity()`

**When Checked:**
- Every hour (3600 seconds) by default
- After each trade execution
- Can be called manually

**What It Checks:**
1. Time since last trade
2. Capital availability
3. Bot pause status
4. Position limits
5. Symbol availability
6. Strategy signals
7. API connectivity

**Alert Trigger:**
- No trades in the last hour
- Bot is not paused
- Not in backtest mode

**Alert Content:**
- Time since last trade
- Total trades count
- Open positions
- Current capital
- Possible reasons (analyzed)
- Recommended actions
- Bot status

**Example Alert:**
```
⚠️ No Trading Activity Detected

No trades have been executed in the last 1.0 hour(s).

Last Trade: 2.5 hours ago
Total Trades: 5
Open Positions: 2
Current Capital: $9,500.00
Capital Floor: $1,000.00

Possible Reasons:
  • No trading opportunities found (market conditions, filters, or thresholds)
  • Check: signal quality, risk thresholds, position limits, capital availability

Recommended Actions:
  1. Check capital availability (above floor)
  2. Verify symbols are available and tradeable
  3. Review strategy signals and filters
  4. Check risk thresholds and position limits
  5. Verify market data is being fetched correctly
  6. Review ML signal filter settings (if enabled)
  7. Check adaptive learning weights (if enabled)

Bot Status:
  • Paper Trading: True
  • Sandbox Mode: False
  • Schwab API: Disabled
  • yfinance Mode: True
  • Bot Paused: False
```

---

## System Messages

### Stored Reasons

When no trades are detected, the bot stores reasons in:
- `self.no_trade_reasons` - List of analyzed reasons
- `self.no_trade_alert_sent` - Flag to prevent duplicate alerts

**Common Reasons:**
- Capital below floor
- Bot is paused
- Max open positions reached
- No symbols available
- No trading signals generated
- API connectivity issues
- Market conditions/filters

---

## Configuration

### Environment Variables

No new environment variables required. The auto-configuration uses existing settings:

- `PAPER_TRADING_MODE` - Auto-set to `true`
- `SCHWAB_SANDBOX_MODE` - Auto-set to `false`
- `SCHWAB_API_ENABLED` - Auto-set to `off`
- `WEB_GUI_CONTINUOUS_TRADING` - Auto-set to `true`
- `WEB_GUI_DEBUG` - Auto-set to `true`
- `ENABLE_PDT_RULES` - Auto-set to `true`

### Trade Activity Check Interval

**Default:** 3600 seconds (1 hour)

**Location:** `TradingBot.trade_activity_check_interval`

**To Change:**
```python
bot.trade_activity_check_interval = 1800  # 30 minutes
```

---

## Usage

### Automatic

The auto-configuration happens automatically when:
1. `SCHWAB_API_ENABLED=off` is set
2. Schwab credentials are not configured
3. Bot is in non-interactive mode without token
4. Any condition that triggers `using_yfinance_sim = True`

### Manual Check

You can manually check trade activity:
```python
bot._check_trade_activity()
```

### View Stored Reasons

```python
if bot.no_trade_reasons:
    print("Reasons for no trades:")
    for reason in bot.no_trade_reasons:
        print(f"  - {reason}")
```

---

## Email Alerts

### Alert Severity

- **WARNING** - No trading activity detected
- **INFO** - Trading activity resumed

### Alert Frequency

- One alert per no-trade period
- Resets when trades resume
- Respects email rate limiting

### Alert Content

Includes:
- Time since last trade
- Trade statistics
- Analyzed reasons
- Recommended actions
- Bot status

---

## Benefits

1. **Automatic Setup** - No manual configuration needed
2. **Optimal Settings** - Pre-configured for training
3. **Activity Monitoring** - Know when bot isn't trading
4. **Diagnostic Info** - Understand why no trades
5. **Email Notifications** - Stay informed
6. **System Messages** - Stored reasons for analysis

---

## Files Modified

1. **`main.py`**
   - Added `_auto_configure_yfinance_mode()` method
   - Added `_check_trade_activity()` method
   - Added trade activity tracking variables
   - Updated `__init__()` to call auto-configuration
   - Updated trade execution to track activity

---

## Testing

### Verify Auto-Configuration

```python
# Set yfinance mode
os.environ['SCHWAB_API_ENABLED'] = 'off'
bot = TradingBot(total_capital=10000.0)

# Check if settings are auto-configured
assert bot.using_yfinance_sim == True
assert PAPER_TRADING_MODE == True
assert SCHWAB_SANDBOX_MODE == False
assert SCHWAB_API_ENABLED == False
```

### Test Trade Activity Monitoring

```python
# Wait for check interval
import time
time.sleep(bot.trade_activity_check_interval + 1)

# Manually trigger check
bot._check_trade_activity()

# Verify alert was sent (if no trades)
if bot.no_trade_alert_sent:
    print("Alert sent - check email")
    print("Reasons:", bot.no_trade_reasons)
```

---

## Status

✅ **IMPLEMENTED AND TESTED**

- Auto-configuration working
- Trade activity monitoring active
- Email alerts functional
- System messages stored

---

**Last Updated:** January 26, 2026
