# Live Trading Mode Setup Guide

## Overview

This guide explains how to configure and safely use the Market Pie5 Bot in live (sandbox) trading mode with real money through the Schwab API.

## Table of Contents
1. [Important Safety Notice](#️-important-safety-notice)
2. [Dry-Run Mode](#-dry-run-mode-new)
3. [Configuration](#configuration) — incl. [Capital & Position Sizing](#4-capital--position-sizing)
4. [Safety Features](#safety-features)
5. [Running in Live Mode](#running-in-live-mode)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## ⚠️ Important Safety Notice

**WARNING: Live trading mode executes real trades with real money. Test thoroughly in paper trading mode first!**

Before enabling live mode:
1. **Test in dry-run mode first** (see [Dry-Run Mode](#-dry-run-mode-new) below)
2. Thoroughly test your strategy in paper trading mode
3. Start with small amounts you can afford to lose
4. Understand all risks involved in automated trading
5. Keep monitoring logs and alerts closely
6. Have a plan for emergencies and unexpected behavior

## 🧪 Dry-Run Mode (NEW)

**Dry-run mode** validates your live trading workflow without executing actual trades. This is the **safest way** to test your configuration before going live.

### What Dry-Run Mode Does

When enabled, dry-run mode:
- ✅ Validates all API credentials
- ✅ Performs all risk checks (capital floor, risk threshold)
- ✅ Tests stock filtering logic
- ✅ Constructs and validates order payloads
- ✅ Tests API authentication
- ✅ Logs everything that would happen
- ❌ **Does NOT** place actual orders on Schwab

### Enabling Dry-Run Mode

Add to your `.env` file:

```bash
# Enable dry-run mode
DRY_RUN_MODE=true

# Keep paper trading OFF for realistic testing
PAPER_TRADING_MODE=false

# Use your REAL Schwab credentials
SCHWAB_API_KEY=your_actual_app_key
SCHWAB_APP_SECRET=your_actual_app_secret
SCHWAB_CALLBACK_URL=your_actual_redirect_uri
SCHWAB_ACCOUNT_ID=your_actual_account_number
```

### Running Dry-Run Validation

```bash
# Set dry-run mode
export DRY_RUN_MODE=true

# Run the bot
python3 main.py
```

The bot will execute your trading strategy but instead of placing orders, it will:
1. Log: `[DRY-RUN MODE] ✓ All validations passed`
2. Show the complete order payload
3. Generate a mock order ID like `DRY_RUN_AAPL_BUY_1234567890`
4. Report success without touching your account

### Dry-Run Test Suite

Run comprehensive dry-run tests:

```bash
# Run all dry-run validation tests
export DRY_RUN_MODE=true
python3 -m unittest test_live_mode_dry_run -v
```

This test suite validates:
- Credential validation
- Order payload construction (BUY/SELL, LIMIT/MARKET)
- Risk management checks
- Capital floor protection
- Stock filtering
- Multiple order sequences
- No actual API calls are made

### When to Use Dry-Run Mode

Use dry-run mode when:
- ✅ First time setting up live trading
- ✅ Testing new Schwab API credentials
- ✅ Validating configuration changes
- ✅ Before enabling live mode after a long break
- ✅ Testing new trading strategies
- ✅ Troubleshooting API connectivity issues

Before enabling live mode:

## Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
# Trading Mode - SET THIS CAREFULLY
PAPER_TRADING_MODE=false  # Set to 'false' for live trading

# Schwab API Credentials (Required for live mode)
SCHWAB_API_KEY=your_actual_app_key
SCHWAB_APP_SECRET=your_actual_app_secret
SCHWAB_CALLBACK_URL=your_actual_redirect_uri
SCHWAB_ACCOUNT_ID=your_actual_account_number

# Risk Management Settings
BOT_RISK_THRESHOLD=0.05  # Max 5% of capital at risk per trade
BOT_MIN_ALLOCATION=50    # Minimum trade size
BOT_MAX_ALLOCATION=500   # Maximum trade size
BOT_TRAILING_STOP_PERCENT=0.05  # 5% trailing stop loss

# Order Type Configuration (NEW)
# Control order types for BUY and SELL actions in live trading
# LIMIT: Execute at specified price or better (good for price control on entries)
# MARKET: Execute immediately at current market price (good for quick exits)
BOT_DEFAULT_BUY_ORDER_TYPE=LIMIT    # Default: LIMIT for price control
BOT_DEFAULT_SELL_ORDER_TYPE=MARKET  # Default: MARKET for faster execution

# Capital Protection
CAPITAL_FLOOR_PERCENT=0.10  # Stop trading if capital drops below 10% of starting

# Alerts (Highly recommended for live mode)
ENABLE_ALERTS=true
ALERT_EMAIL=operator@example.com
```

### 2. Schwab API Setup

Follow these steps to get your Schwab API credentials:

1. Visit [developer.schwab.com](https://developer.schwab.com)
2. Sign in with your Schwab account
3. Create a new application:
   - App Type: Personal
   - Scopes: Enable "Trading" permissions
4. Note your credentials:
   - API Key (App Key)
   - App Secret
   - Callback URL (redirect URI)
5. Find your Account ID in your Schwab account dashboard

**Important**: Keep your API credentials secure. Never commit them to version control or share them.

### 3. Validation

Before running in live mode, validate your configuration:

```bash
# Test configuration validation
python3 -c "
import main
is_valid, issues = main.validate_configuration()
if is_valid:
    print('✓ Configuration is valid')
else:
    print('✗ Configuration has issues:')
    for issue in issues:
        print(f'  - {issue}')
"
```

### 4. Capital & Position Sizing

Use different capital and sizing for **dry-run vs live**, and start **very small** when first going live.

#### Dry-run vs live capital

| Phase | `BOT_TOTAL_CAPITAL` | Notes |
|-------|---------------------|--------|
| **Dry-run / paper** | `10000` (or more) | Simulate a larger portfolio; no real money. Used for position sizing and risk checks. |
| **Live start** | `1000` (or less) | Start with an amount you can afford to lose. **In live mode**, if `USE_SCHWAB_CAPITAL_IN_LIVE=true` (default), the bot **fetches actual account cash/buying power from Schwab API** and uses that as `BOT_TOTAL_CAPITAL` instead of this config value. This ensures the bot trades based on your real available funds. |

#### Conservative live start

When first going live, use **very small** position sizes:

- `BOT_MIN_ALLOCATION=50` — minimum $ per trade  
- `BOT_MAX_ALLOCATION=200` — cap $ per trade  
- `BOT_POSITION_SIZE=0.01` — 1% of capital per position  
- `BOT_RISK_THRESHOLD=0.02` — 2% max risk per trade  
- `CAPITAL_FLOOR_PERCENT=0.10` — stop trading if capital drops below 10% of starting

#### Relevant env vars

| Variable | Purpose |
|----------|---------|
| `BOT_TOTAL_CAPITAL` | Paper/dry-run capital; in live mode, overridden by Schwab API if `USE_SCHWAB_CAPITAL_IN_LIVE=true` |
| `USE_SCHWAB_CAPITAL_IN_LIVE` | In live mode, fetch capital from Schwab API account funds (default: `true`) |
| `BOT_MIN_ALLOCATION` | Minimum $ per trade |
| `BOT_MAX_ALLOCATION` | Maximum $ per trade |
| `BOT_POSITION_SIZE` | Fraction of capital per position (e.g. `0.01` = 1%) |
| `BOT_RISK_THRESHOLD` | Max risk per trade (e.g. `0.02` = 2%) |
| `CAPITAL_FLOOR_PERCENT` | Stop trading below this fraction of starting capital |

See [ROADMAP.md](ROADMAP.md) (User Workflow & Constraints) for the full capital/sizing notes.

## Safety Features

The bot includes multiple safety features for live trading:

### 1. Pre-Flight Validation

Before any live trade, the bot validates:
- ✅ API credentials are configured and not placeholders
- ✅ Capital is above the floor threshold
- ✅ Trade size doesn't exceed risk limits
- ✅ Stock passes quality filters (price, volume, volatility)

### 2. Error Handling

Comprehensive error handling for:
- **Authentication errors (401)**: Invalid or expired credentials
- **Rate limiting (429)**: Too many API requests
- **Timeouts**: 30-second timeout on all API calls
- **Connection errors**: Network issues
- **Unexpected errors**: All exceptions are caught and logged

### 3. Logging

All operations are logged with timestamps and context:
- **trading_bot.log**: Main application log (INFO, WARNING, ERROR)
- **alerts.log**: Critical alerts and significant events
- Console output: Real-time monitoring

### 4. Order Type Configuration

The bot supports configurable order types for BUY and SELL actions, optimized for swing trading:

#### Default Behavior

- **BUY Orders**: Use **LIMIT** orders by default for price control
  - Ensures you don't overpay during entry
  - Protects against price slippage
  - May not fill if price moves away from limit
  
- **SELL Orders**: Use **MARKET** orders by default for faster execution
  - Ensures position exits quickly
  - Better for taking profits or cutting losses
  - May experience minor slippage

#### Configuring Order Types

Set defaults in `.env`:

```bash
# Use LIMIT orders for BUY (price control)
BOT_DEFAULT_BUY_ORDER_TYPE=LIMIT

# Use MARKET orders for SELL (speed)
BOT_DEFAULT_SELL_ORDER_TYPE=MARKET

# Alternative: Use MARKET for both (fastest execution)
BOT_DEFAULT_BUY_ORDER_TYPE=MARKET
BOT_DEFAULT_SELL_ORDER_TYPE=MARKET

# Alternative: Use LIMIT for both (maximum price control)
BOT_DEFAULT_BUY_ORDER_TYPE=LIMIT
BOT_DEFAULT_SELL_ORDER_TYPE=LIMIT
```

#### Order Type Behavior

- **LIMIT Orders**:
  - Include a specific price in the order
  - Execute only at that price or better
  - BUY LIMIT: Execute at limit price or lower
  - SELL LIMIT: Execute at limit price or higher
  - May not fill if market moves away

- **MARKET Orders**:
  - Execute immediately at current market price
  - Guaranteed to fill (if market is open)
  - May experience slippage in volatile markets
  - No price specified in order

#### Example Scenarios

**Swing Trading (Recommended Defaults)**:
```bash
BOT_DEFAULT_BUY_ORDER_TYPE=LIMIT    # Careful entry
BOT_DEFAULT_SELL_ORDER_TYPE=MARKET  # Quick exit
```

**Day Trading**:
```bash
BOT_DEFAULT_BUY_ORDER_TYPE=MARKET   # Fast entry
BOT_DEFAULT_SELL_ORDER_TYPE=MARKET  # Fast exit
```

**Precision Trading**:
```bash
BOT_DEFAULT_BUY_ORDER_TYPE=LIMIT    # Controlled entry
BOT_DEFAULT_SELL_ORDER_TYPE=LIMIT   # Controlled exit
```

#### Validation

Invalid order types automatically fall back to defaults with a warning:
- Valid values: `LIMIT` or `MARKET`
- Case-insensitive: `limit`, `LIMIT`, `Limit` all work
- Invalid values: Logged and replaced with default

Log levels:
- `INFO`: Normal operations (trade executions, status updates)
- `WARNING`: Non-critical issues (rate limits, retries)
- `ERROR`: Failures requiring attention (API errors, validation failures)
- `CRITICAL`: System-level failures

### 4. Alerting

The AlertSystem sends notifications for:
- Live trade executions (success or failure)
- Capital floor breaches
- Significant P&L changes (>10% of capital)
- API authentication failures
- Rate limiting issues
- Bot pause/resume events

## Running in Live Mode

### Method 1: Command Line

```bash
# Ensure PAPER_TRADING_MODE=false in .env
python3 main.py
```

The bot will:
1. Validate your configuration
2. Show a confirmation prompt: **Type 'CONFIRM' to proceed**
3. Start executing trades via Schwab API

### Method 2: GUI

```bash
python3 gui.py
```

The GUI shows the current mode prominently and provides controls for:
- Starting/stopping the bot
- Viewing real-time logs
- Monitoring system resources
- Reviewing trade statistics

### Method 3: Programmatic

```python
import os
os.environ['PAPER_TRADING_MODE'] = 'false'

from main import TradingBot, validate_configuration

# Validate first
is_valid, issues = validate_configuration()
if not is_valid:
    print("Configuration invalid!")
    exit(1)

# Create bot and execute trades
bot = TradingBot(total_capital=10000.0)
result = bot.execute_trade('AAPL', 'BUY', 150.0)

if result['status'] == 'success':
    print(f"✓ Trade successful: {result['order_id']}")
else:
    print(f"✗ Trade failed: {result.get('message', 'Unknown error')}")
```

## Monitoring

### Real-Time Monitoring

Monitor these files during live trading:

```bash
# Watch main log
tail -f trading_bot.log

# Watch alerts
tail -f alerts.log

# Watch both
tail -f trading_bot.log alerts.log
```

### Key Metrics to Monitor

1. **Capital**: Ensure it stays above the floor
2. **Win Rate**: Should remain reasonable (40-60%)
3. **API Errors**: Shouldn't see frequent auth or rate limit errors
4. **Position Count**: Respect MAX_SIMULTANEOUS_POSITIONS
5. **Trade Size**: Stays within MIN/MAX_ALLOCATION bounds

## Troubleshooting

### Common Issues

#### 1. "Live mode credentials not configured or invalid"

**Solution**: Check that all Schwab credentials in `.env` are real values, not placeholders.

```bash
# Verify your .env file
grep -E "SCHWAB_API_KEY|SCHWAB_APP_SECRET|SCHWAB_CALLBACK_URL|SCHWAB_ACCOUNT_ID" .env
```

#### 2. "API authentication failed - invalid or expired credentials"

**Solutions**:
- Verify credentials at developer.schwab.com
- Check if API key has trading permissions
- Ensure account ID is correct
- OAuth token might have expired - regenerate if needed

#### 3. "API rate limit exceeded - too many requests"

**Solution**: The bot will automatically back off, but you can:
- Reduce trade frequency
- Add longer delays between trades
- Check for multiple bot instances running

#### 4. "Capital floor breach - trading paused"

**Solution**: This is intentional protection. To resume:
- Review recent trades and P&L
- Identify what went wrong
- Adjust strategy or risk parameters
- Capital must recover to >120% of floor to auto-resume

#### 5. "API request timed out after 30 seconds"

**Solution**:
- Check your internet connection
- Verify Schwab API status
- Consider increasing timeout in code if needed
- This is a transient error - bot will continue

### Emergency Stop

To immediately stop the bot:

1. **Press Ctrl+C** in the terminal
2. **Check open positions**: Review any open trades in Schwab
3. **Manual intervention**: Close positions manually if needed
4. **Review logs**: Check what went wrong

```bash
# View recent errors
grep ERROR trading_bot.log | tail -20

# View recent alerts
tail -20 alerts.log
```

## Best Practices

### 1. Start Small

- Begin with minimum allocation amounts
- Test with 1-2 symbols initially
- Gradually increase as confidence grows

### 2. Monitor Actively

- Keep logs open during trading hours
- Set up email alerts
- Review daily performance
- Check for unexpected behavior

### 3. Regular Reviews

- Review logs weekly
- Analyze win rates and P&L trends
- Adjust parameters based on performance
- Test changes in paper mode first

### 4. Risk Management

- Never risk more than you can afford to lose
- Keep BOT_RISK_THRESHOLD conservative (3-5%)
- Respect capital floor protection
- Diversify across multiple symbols

### 5. Testing

Run the test suite regularly:

```bash
# Test all features
python3 -m unittest discover -v

# Test live mode specifically
python3 -m unittest test_live_mode_features -v
```

## Security

### Protecting Your Credentials

1. **Never commit .env to version control**
   - Ensure `.gitignore` includes `.env`
   - Use `.env.example` for templates only

2. **File permissions**
   ```bash
   chmod 600 .env  # Only owner can read/write
   ```

3. **Rotate credentials regularly**
   - Change API keys periodically
   - Use different keys for testing vs production

4. **Monitor access**
   - Review API usage at developer.schwab.com
   - Watch for unexpected API calls
   - Set up Schwab account alerts

## Support and Resources

- **Schwab API Docs**: https://developer.schwab.com/products
- **Project GitHub**: https://github.com/operator/market-pie5-bot
- **Issues**: Report bugs via GitHub Issues
- **Logs**: Always include relevant log excerpts when seeking help

## Legal Disclaimer

This bot is provided for educational purposes. Trading stocks involves risk of financial loss. The authors are not responsible for any losses incurred. Use at your own risk. Always comply with securities regulations in your jurisdiction.

## Checklist Before Going Live

- [ ] **Tested in dry-run mode with real credentials** (`DRY_RUN_MODE=true`)
- [ ] Dry-run validation tests all pass
- [ ] Tested thoroughly in paper trading mode (>100 trades)
- [ ] All Schwab API credentials are configured correctly
- [ ] Validation passes with `validate_configuration()`
- [ ] Risk parameters are set conservatively
- [ ] Capital floor protection is enabled
- [ ] Alerts are configured and working
- [ ] Understand all features and limitations
- [ ] Have emergency stop procedure ready
- [ ] Monitoring setup (log files, alerts)
- [ ] Starting with small amounts
- [ ] Ready to actively monitor during trading hours

---

**Remember: Start in dry-run mode, then paper mode, test thoroughly, and only enable live mode when you're confident and understand all risks involved.**
