# Manual Start Button Guide

## Overview

The trading bot now requires **explicit user confirmation** before starting any trading activity. This ensures you have full control over when trading begins and allows you to review all settings before execution.

## Key Features

### 🛡️ No Auto-Trading
- **CLI Mode**: Requires user to type `START` before trading begins
- **Web GUI**: Start button applies current UI settings and begins trading
- Both modes require explicit user action - no automatic trading on startup

### ⚙️ Immediate Settings Application
- **Web GUI**: All settings take effect when you click Start
- **No Restart Required**: Change settings and start immediately
- **Settings Persistence**: Use "Apply Settings" button to save to `.env` file

### 📋 Complete Parameter Control
- All `.env` parameters are integrated and accessible
- Settings can be modified via:
  - `.env` file (persistent across restarts)
  - Web GUI (immediate effect, optionally save to `.env`)
  - Environment variables (for advanced users)

## CLI Mode

### Starting the Bot

1. Run the bot:
   ```bash
   python3 main.py
   ```

2. Review the configuration summary:
   ```
   ============================================================
   READY TO START TRADING
   ============================================================
   Mode: PAPER TRADING (Schwab Sandbox)
   Capital: $10000.00
   Symbols to trade: 5
   Max allocation: $500.00
   Risk threshold: 2.0%
   ============================================================
   ```

3. Confirm to start:
   ```
   Type 'START' to begin trading (or anything else to cancel): START
   ```

4. Trading begins after confirmation

### Canceling

To cancel trading:
- Type anything other than `START` (e.g., `CANCEL`, `NO`, or just press Enter)
- Press `Ctrl+C` at any time
- Bot will exit without executing any trades

### Example Session

```bash
$ python3 main.py
...
[Configuration and validation checks]
...

============================================================
READY TO START TRADING
============================================================
Mode: PAPER TRADING (Schwab Sandbox)
Capital: $10000.00
Symbols to trade: 5
Max allocation: $500.00
Risk threshold: 2.0%
============================================================

Type 'START' to begin trading (or anything else to cancel): START

--- Executing PAPER TRADING (Schwab Sandbox) Trades ---
[Trading begins]
```

## Web GUI Mode

### Starting the Bot

1. Launch the web GUI:
   ```bash
   ./start_web_gui.sh
   ```
   or
   ```bash
   python3 web_gui.py
   ```

2. Open browser to `http://localhost:8050`

3. Configure settings in the Settings tab (if desired)

4. Click the **Start** button in the header

5. Bot applies current UI settings and begins trading

### Key Behaviors

#### Settings Application
When you click **Start**:
- All current UI settings are applied immediately
- Settings are loaded into environment variables for this session
- Bot starts with your current configuration
- **Note**: Settings are NOT saved to `.env` unless you click "Apply Settings"

#### Settings Persistence
To make settings persist across restarts:
1. Configure settings in the Settings tab
2. Click **"Apply Settings"** button
3. Settings are saved to `.env` file
4. Next time you start the bot, these settings will be loaded automatically

#### Example Workflow

**For a quick test (no persistence):**
1. Adjust settings in Settings tab
2. Click **Start** button
3. Bot uses your settings for this session only

**For permanent configuration:**
1. Adjust settings in Settings tab
2. Click **"Apply Settings"** button
3. Click **Start** button
4. Settings persist for future sessions

## Configuration Parameters

### All Parameters from .env

The following parameters are fully integrated and can be configured:

#### Trading Mode
- `PAPER_TRADING_MODE` - Enable paper trading (true/false)
- `SCHWAB_SANDBOX_MODE` - Use Schwab sandbox (true/false)
- `SCHWAB_API_ENABLED` - Enable/disable Schwab API (on/off)

#### Capital & Risk Management
- `BOT_MIN_ALLOCATION` - Minimum trade allocation ($)
- `BOT_MAX_ALLOCATION` - Maximum trade allocation ($)
- `BOT_RISK_THRESHOLD` - Maximum risk per trade (%)
- `BOT_POSITION_SIZE` - Position size as % of capital
- `CAPITAL_FLOOR_PERCENT` - Stop trading if capital drops below this %

#### Stop Loss & Take Profit
- `BOT_TRAILING_STOP_PERCENT` - Trailing stop loss (%)
- `BOT_STOP_LOSS_PERCENT` - Fixed stop loss (%)
- `BOT_TAKE_PROFIT_PERCENT` - Take profit target (%)
- `DYNAMIC_STOP_ENABLED` - Enable dynamic stops (true/false)
- `MIN_TRAILING_STOP` - Minimum trailing stop (%)
- `MAX_TRAILING_STOP` - Maximum trailing stop (%)

#### Position Management
- `BOT_MAX_OPEN_POSITIONS` - Maximum concurrent positions
- `BOT_MAX_CONSECUTIVE_LOSSES` - Max losses before reducing allocation
- `PARTIAL_EXIT_ENABLED` - Enable partial exits (true/false)
- `PARTIAL_EXIT_PERCENTAGE` - % of position to exit partially

#### Stock Filtering
- `MIN_STOCK_PRICE` - Minimum stock price ($)
- `MIN_DAILY_VOLUME` - Minimum daily volume
- `MAX_STOCK_VOLATILITY` - Maximum volatility threshold
- `VOLATILITY_WINDOW` - Window for volatility calculation

#### Trading Behavior
- `TRADING_FREQUENCY` - Seconds between trades
- `SIMULATED_WIN_RATE` - Win rate for paper trading
- `WEB_GUI_MAX_SYMBOLS` - Max symbols to trade
- `WEB_GUI_CONTINUOUS_TRADING` - Enable continuous mode (true/false)

#### API Configuration
- `SCHWAB_API_KEY` - Schwab API key
- `SCHWAB_APP_SECRET` - Schwab app secret
- `SCHWAB_CALLBACK_URL` - OAuth callback URL
- `SCHWAB_ACCOUNT_ID` - Trading account ID
- `HUGGINGFACE_API_KEY` - HuggingFace API key (for AI features)
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage key (for fundamentals)
- `NEWS_API_KEY` - News API key (for sentiment)
- `FINNHUB_API_KEY` - Finnhub key (for news)

#### Resource Management
- `BOT_ENABLE_THROTTLING` - Enable CPU/memory throttling (true/false)
- `BOT_MAX_CPU_PERCENT` - Max CPU usage (%)
- `BOT_MAX_MEMORY_PERCENT` - Max memory usage (%)
- `BOT_THROTTLE_DELAY` - Throttle delay (seconds)

#### User Profile
- `USER_PROFILE_NAME` - Display name
- `USER_PROFILE_USERNAME` - Username handle

## Benefits

### 🔒 Safety
- No accidental trading
- Review configuration before starting
- Cancel at any time

### 🎯 Control
- Choose exactly when to trade
- Configure all parameters
- Test different strategies safely

### 🚀 Convenience
- Immediate settings application (web GUI)
- No restart required for most changes
- Clear feedback on what's being used

### 📊 Transparency
- See exact configuration before trading
- Logs show which settings are active
- Know whether settings are persisted or temporary

## Troubleshooting

### CLI Mode Issues

**Problem**: Confirmation prompt doesn't appear
- **Solution**: Make sure you're running in an interactive terminal
- **Note**: Non-interactive mode (like cron jobs) won't work - use web GUI or modify code

**Problem**: Bot exits after typing START
- **Solution**: Check logs for error messages
- **Solution**: Verify .env configuration is valid

### Web GUI Issues

**Problem**: Start button doesn't work
- **Solution**: Check browser console for errors
- **Solution**: Ensure all required settings have valid values
- **Solution**: Check web GUI logs in terminal

**Problem**: Settings don't persist
- **Solution**: Click "Apply Settings" to save to .env
- **Note**: Just clicking Start only applies for current session

**Problem**: Bot uses old settings
- **Solution**: Make sure you clicked "Apply Settings" 
- **Solution**: Check .env file has correct values
- **Solution**: Restart web GUI to reload .env

## Migration Guide

### From Old Version

If you're upgrading from a version without manual start:

**CLI Mode:**
- **Before**: Bot started trading immediately
- **After**: Bot requires START confirmation
- **Impact**: Add one extra step to start trading
- **Benefit**: Can't accidentally start trading

**Web GUI:**
- **Before**: Had to restart bot to apply settings
- **After**: Settings apply immediately on Start
- **Impact**: More convenient, faster iteration
- **Benefit**: Test different configurations quickly

## Best Practices

### Development & Testing
1. Use web GUI for rapid iteration
2. Don't save to .env until you're satisfied
3. Use paper trading mode for safe testing
4. Review logs to verify settings

### Production Trading
1. Configure settings in .env file
2. Use "Apply Settings" to persist configuration
3. Review configuration summary before starting
4. Use live mode only after thorough testing

### Safety Guidelines
1. Always review settings before starting
2. Start with small capital for testing
3. Monitor first few trades closely
4. Keep capital floor at 10%+ for safety

## Examples

### Example 1: Quick Test with Custom Settings

```bash
# Web GUI approach
./start_web_gui.sh

# In browser:
# 1. Settings tab: Set Capital to $100, Max Allocation to $10
# 2. Click Start (don't click Apply Settings)
# 3. Bot trades with these settings
# 4. Stop bot
# 5. Next time: back to .env defaults
```

### Example 2: Permanent Configuration Change

```bash
# Web GUI approach
./start_web_gui.sh

# In browser:
# 1. Settings tab: Configure desired settings
# 2. Click "Apply Settings" (saves to .env)
# 3. Click Start
# 4. Bot trades with new settings
# 5. Next time: uses these saved settings
```

### Example 3: CLI with Environment Overrides

```bash
# Override settings for this run only
BOT_MAX_ALLOCATION=1000 BOT_RISK_THRESHOLD=0.05 python3 main.py

# Type START when prompted
# Bot uses these values for this session only
```

## Summary

✅ **Manual Control**: No auto-trading, explicit user confirmation required  
✅ **Flexible Configuration**: Multiple ways to set parameters  
✅ **Immediate Application**: Web GUI settings take effect on Start  
✅ **Persistent Storage**: Save settings to .env for future use  
✅ **Complete Integration**: All .env parameters accessible  
✅ **Clear Feedback**: Logs show active configuration  

The bot is now safer, more flexible, and easier to configure!
