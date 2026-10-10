# yfinance Simulation Mode - Auto-Fallback Feature

## Overview

The bot now includes **automatic fallback to yfinance simulation mode** when the Schwab API is unavailable, **and further falls back to random price simulation** if yfinance is also unavailable. This feature allows you to:

- ✅ **Auto-switch to sim mode** if not connected to Schwab API
- ✅ **Use yfinance** for realistic price data during simulations
- ✅ **Use random prices** as last resort when no APIs available
- ✅ **Keep sim trade data and real-world trade data separate**
- ✅ **Test and learn patterns** without Schwab API connectivity

## How It Works

### Mode Priority

When running in **sandbox mode** (`PAPER_TRADING_MODE=true` and `SCHWAB_SANDBOX_MODE=true`):

1. **First**, bot attempts to connect to Schwab Sandbox API
2. **If Schwab API fails**, bot automatically switches to **yfinance simulation mode**
3. **If yfinance also fails**, bot uses **random price simulation** as last resort
4. **Trade data is tagged** with the mode it was executed in (`yfinance_sim`, `schwab_sandbox`, `pure_simulation`, etc.)
5. **Separate trade history files** are saved for each mode

### Complete Fallback Chain

The bot now has a complete fallback chain to ensure it can always operate:

```
Sandbox Mode:   Schwab API → yfinance → Random Simulation
Live Mode:      Schwab API → yfinance (no random fallback)
Pure Sim Mode:  yfinance → Random Simulation
```

This means **the bot will never fail to start** in sandbox mode, even with no internet connection or API access!

### Trade Data Separation

All trades are tagged with their execution mode:

- `yfinance_sim` - Trades executed using yfinance prices (auto-fallback from Schwab)
- `pure_simulation` - Trades executed with random prices (last resort fallback)
- `schwab_sandbox` - Trades executed via Schwab Sandbox API
- `live_trading` - Real trades via Schwab Production API

### Trade History Files

Trade history is automatically saved to separate files based on mode:

```
trade_history_yfinance_sim_20260118_123456.json
trade_history_sandbox_20260118_123456.json
trade_history_simulation_20260118_123456.json
trade_history_live_20260118_123456.json
```

Each file contains:
- **Metadata**: Mode, timestamp, win rate, P&L
- **Trades**: All trades executed in that mode with full details

## Configuration

### Enable Sandbox Mode with Auto-Fallback

In your `.env` file:

```bash
# Enable paper trading
PAPER_TRADING_MODE=true

# Enable sandbox mode (will auto-fallback to yfinance if Schwab unavailable)
SCHWAB_SANDBOX_MODE=true
```

### Pure yfinance Simulation Mode

To use yfinance simulation without attempting Schwab connection:

```bash
# Enable paper trading
PAPER_TRADING_MODE=true

# Disable sandbox mode to skip Schwab API
SCHWAB_SANDBOX_MODE=false
```

## Usage Examples

### Example 1: Sandbox Mode with Auto-Fallback

```python
# Bot starts in sandbox mode
# Attempts Schwab API connection
# If Schwab API fails, automatically switches to yfinance sim

from main import TradingBot

bot = TradingBot(total_capital=10000.0)

# Get stock price - will use yfinance if Schwab unavailable
price, volume = bot.get_stock_price('AAPL')

# Execute trade - automatically uses correct mode
bot.execute_trade('AAPL', 'BUY', price, volume)

# Check current mode
if bot.using_yfinance_sim:
    print("Using yfinance simulation mode")
else:
    print("Using Schwab API")
```

### Example 2: Filter Trades by Mode

```python
# Get all trades
all_trades = bot.trade_history

# Filter by mode
sim_trades = bot.get_trades_by_mode('yfinance_sim')
sandbox_trades = bot.get_trades_by_mode('schwab_sandbox')
live_trades = bot.get_trades_by_mode('live_trading')

print(f"yfinance sim trades: {len(sim_trades)}")
print(f"Schwab sandbox trades: {len(sandbox_trades)}")
print(f"Live trades: {len(live_trades)}")
```

### Example 3: Save Trade History

```python
# Save trade history to file
# Filename is auto-generated based on mode and timestamp
bot.save_trade_history()

# Or specify custom filename
bot.save_trade_history('my_trades.json')
```

## Benefits

### 1. **Continuous Operation**

Bot doesn't crash when Schwab API is unavailable - it automatically switches to yfinance simulation mode, and if that's also unavailable, uses random price simulation. **The bot will always work!**

### 2. **Realistic Testing (when possible)**

Use real market data from yfinance to test trading strategies and learn patterns when internet is available.

### 3. **Offline Training**

Even without any internet connection, the bot can train using random price simulation. Perfect for:
- Testing strategy logic
- Learning trading patterns
- Debugging without API dependencies
- CI/CD environments without external network access

### 4. **Data Separation**

Sim trades and real trades are clearly separated, making it easy to:
- Analyze sim performance separately from live trades
- Compare sim results to real results
- Track which strategies work in simulation vs production

### 4. **Learning and Development**

Perfect for:
- Testing new strategies without Schwab API credentials
- Learning trading patterns on real historical data (when yfinance available)
- Practicing with simulated prices (when no APIs available)
- Developing and debugging without API connectivity
- Running in CI/CD pipelines without external dependencies

## Alerts

When auto-fallback occurs, the bot sends alerts:

### Fallback to yfinance
```
Subject: Auto-Fallback to yfinance Sim Mode
Message: Schwab API unavailable. Bot automatically switched to yfinance simulation mode.
         All trades will be marked as 'yfinance_sim' for separation from real trades.
```

### Fallback to Random Simulation
```
Subject: Using Random Price Simulation
Message: Both Schwab and yfinance APIs are unavailable. Bot will use random price simulation.
         This is useful for testing strategies and learning trading patterns.
         To use real market data, ensure:
           1. Internet connection is working
           2. yfinance is installed (pip install yfinance)
           3. Schwab API credentials are configured (optional)
```

Alerts are logged to:
- Console output
- `alerts.log` file
- Email (if configured)

## Monitoring Mode Changes

### During Startup

```
[SANDBOX MODE] Attempting to connect to Schwab API...
[WARNING] Schwab sandbox API unavailable, checking yfinance fallback...
[WARNING] yfinance also unavailable
[INFO] Falling back to random price simulation mode
[SUCCESS] Using random price simulation (APIs unavailable)
```

OR if yfinance is available:

```
[SANDBOX MODE] Attempting to connect to Schwab API...
[WARNING] Schwab sandbox API unavailable, checking yfinance fallback...
[SUCCESS] yfinance API available (price: $150.00)
[INFO] Auto-switching to yfinance simulation mode
```

### During Trading

With yfinance:
```
[YFINANCE SIM MODE: BUY]
  Symbol: AAPL
  Price: $150.00
  Volume: 1,000,000
  Mode: yfinance simulation (auto-fallback)
```

With random simulation:
```
[SIMULATION MODE: BUY]
  Symbol: AAPL
  Price: $127.43
  Volume: 5,234,891
  Mode: random simulation (last resort fallback)
```

### In Summary

With yfinance available:
```
Mode: YFINANCE SIMULATION (Auto-fallback from Schwab API)
PDT Protection: Disabled (yfinance sim mode - unlimited day trades)
Total Trades: 25
yfinance sim trades: 25
```

With random simulation:
```
Mode: RANDOM SIMULATION (No API available)
PDT Protection: Disabled (simulation mode - unlimited day trades)
Total Trades: 25
pure_simulation trades: 25
```

## Testing

Run the test suite to verify auto-fallback functionality:

```bash
python3 test_yfinance_sim.py
```

Tests cover:
- ✅ Auto-fallback when Schwab API fails
- ✅ Trade mode tagging
- ✅ Trade filtering by mode
- ✅ API connectivity validation
- ✅ Trade history saving
- ✅ Behavior when both APIs unavailable

## API Requirements

### yfinance (Recommended)

```bash
pip install yfinance
```

yfinance provides:
- Real-time stock prices
- Historical data
- Volume information
- No API key required

### Schwab API (Optional)

Only needed if you want to use Schwab Sandbox or Production API. If not configured or unavailable, bot will automatically use yfinance.

## Troubleshooting

### Issue: Bot still crashes when Schwab API unavailable

**Solution**: This should no longer happen! The bot now has a complete fallback chain. If you're still seeing crashes, please check:
1. That you're using the latest version of the code
2. That `PAPER_TRADING_MODE=true` in your .env file
3. The specific error message in the logs

### Issue: Bot using random prices instead of yfinance

**Solution**: This means yfinance is not available. Check that:
1. yfinance is installed (`pip install yfinance`)
2. You have internet connectivity
3. Check the logs for yfinance-specific errors

### Issue: Web GUI price chart not showing data

**Solution**: The price chart should now always work, even with random prices. Check:
1. That the bot is running (click Start button)
2. That symbols are added to the watchlist
3. The browser console for JavaScript errors
4. The bot logs for price fetching errors

### Issue: Trade history files not being created

**Solution**: Check that the bot has write permissions in the current directory.

### Issue: Can't distinguish sim trades from real trades

**Solution**: Use the `mode` field in trade history or filter using `get_trades_by_mode()`:
```python
sim_trades = bot.get_trades_by_mode('yfinance_sim')
random_trades = bot.get_trades_by_mode('pure_simulation')
live_trades = bot.get_trades_by_mode('live_trading')
```

### Issue: All trades showing as random/simulated

**Cause**: This means both Schwab and yfinance APIs are unavailable.

**Solution**: 
1. For yfinance data: Check internet connection and run `pip install yfinance`
2. For Schwab data: Configure Schwab API credentials
3. If testing/training: This is expected behavior and works fine!

## Future Enhancements

Potential future features:
- CSV export for sim vs real trade comparison
- Performance analytics separated by mode
- Backtesting integration with yfinance historical data
- Strategy comparison across different modes

## See Also

- [Main README](README.md) - General bot documentation
- [Environment Variables](docs/archive/ENVIRONMENT_VARIABLES_SUMMARY.md) - Configuration guide
- [Web GUI Guide](WEB_GUI_GUIDE.md) - Browser-based interface
- [Live Mode Guide](LIVE_MODE_GUIDE.md) - Production trading guide
