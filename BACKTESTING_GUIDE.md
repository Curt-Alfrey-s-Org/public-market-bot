# Backtesting Guide

## Overview

The Market Pie5 Bot includes a **dedicated backtesting mode** that allows you to test trading strategies on historical data without risking real capital. This mode supports two approaches:

1. **Forward Simulation Mode**: Simulates trading as if you were running the bot in real-time on historical data
2. **Swing Trading Mode (NEW!)**: "Go back in time" methodology that simulates buy-then-sell scenarios with realistic exit conditions

## NEW: Backtesting Instance Methods (Simplified API)

The bot now includes **instance methods** for backtesting, making it easier to run backtests programmatically:

### Quick Start with Instance Methods

```python
from main import TradingBot

# Create bot
bot = TradingBot(total_capital=10000.0)

# Run backtest with date range
results = bot.backtest_loop(
    start_date='2024-01-01',
    end_date='2024-12-31',
    symbols=['AAPL', 'MSFT', 'GOOGL']
)

# Print summary
bot.print_backtest_summary(results)
```

### Instance Method API

**`bot.backtest_loop(start_date, end_date, symbols)`**
- Runs a complete backtest over a specified date range
- **Parameters:**
  - `start_date` (str): Start date in 'YYYY-MM-DD' format
  - `end_date` (str): End date in 'YYYY-MM-DD' format
  - `symbols` (list): List of stock symbols to backtest
- **Returns:** Dictionary with backtest results and metadata

**`bot.print_backtest_summary(results=None)`**
- Prints a formatted summary of backtest results
- **Parameters:**
  - `results` (dict, optional): Backtest results dictionary. If None, uses current bot state
- **Output:** Prints formatted summary to console

### Example Usage

```python
from main import TradingBot

# Initialize bot
bot = TradingBot(total_capital=10000.0)

# Run backtest for Q1 2024
results = bot.backtest_loop('2024-01-01', '2024-03-31', ['AAPL', 'MSFT'])

# View summary
bot.print_backtest_summary(results)

# Access detailed metrics
metadata = results['metadata']
print(f"Win Rate: {metadata['win_rate']:.2%}")
print(f"Total P&L: ${metadata['total_pnl']:.2f}")
print(f"ROI: {metadata['roi_percent']:.2f}%")

# Check individual trades
for trade in results['trades']:
    print(f"{trade['date']}: {trade['action']} {trade['symbol']} @ ${trade['price']:.2f}")
```

### Backwards Compatibility

The old standalone function API is still supported for backwards compatibility:

```python
from main import TradingBot, backtest_loop

bot = TradingBot(total_capital=10000.0)

# Old API still works (delegates to instance method)
results = backtest_loop(bot, ['AAPL', 'MSFT'], period='1y')
```

## Features

- **Historical Data Analysis**: Uses real data from yfinance or synthetic data for testing
- **Realistic Trading Simulation**: Simulates buy/sell decisions based on actual price movements
- **Exit Strategy Testing**: Tests take profit, trailing stop, and stop loss strategies
- **Performance Metrics**: Calculates win rate, P&L, ROI, profit factor, and other key metrics
- **JSON Export**: Saves detailed results to `backtest_report.json`
- **Parameter Tuning**: Allows testing different risk management parameters
- **Swing Trading Focus**: Enforces minimum holding periods and swing trading rules

## Swing Trading Backtest (NEW!)

### What is Swing Trading Backtesting?

The new `run_swing_backtest()` method implements true "go back in time" testing:

1. **Iterate Through History**: For each historical date, simulate entering a position
2. **Look Forward**: Check future data to determine when the position would exit
3. **Realistic Exits**: Apply take profit, trailing stop, or stop loss based on actual high/low prices
4. **Track Outcomes**: Record whether each trade was a win or loss
5. **Calculate Statistics**: Output comprehensive metrics including win rate (targeting 70%+)

### Key Differences from Forward Simulation

| Feature | Forward Simulation | Swing Trading Backtest |
|---------|-------------------|------------------------|
| Methodology | Simulates real-time trading | "Go back in time" for each trade |
| Entry Points | Based on strategy signals | Tests all historical dates |
| Exit Logic | Checks stops sequentially | Looks forward to find exit |
| Holding Period | Variable | Enforced min/max (2-10 days typical) |
| Win Rate Focus | Secondary metric | Primary target (70%+) |
| Use Case | Strategy validation | Position sizing & exit tuning |

## How to Enable Backtesting Mode

### 1. Update Your `.env` File

Add or update the following line in your `.env` file:

```bash
BACKTEST_MODE=true
```

### 2. Configure Other Parameters (Optional)

You can tune these parameters in your `.env` file to optimize performance:

```bash
# Risk Management
BOT_RISK_THRESHOLD=0.02          # Risk 2% per trade
BOT_TRAILING_STOP_PERCENT=0.03   # 3% trailing stop
BOT_TAKE_PROFIT_PERCENT=0.10     # 10% take profit target
BOT_STOP_LOSS_PERCENT=0.06       # 6% stop loss

# Position Sizing
BOT_POSITION_SIZE=0.01           # 1% of capital per position
BOT_MIN_ALLOCATION=100           # Minimum $100 per trade
BOT_MAX_ALLOCATION=5000          # Maximum $5000 per trade

# Capital Management
BOT_TOTAL_CAPITAL=10000          # Starting capital for backtest

# Symbol Selection
ENABLE_STOCK_SCREENER=true       # Use dynamic stock discovery
MAX_DISCOVERED_STOCKS=10         # Test up to 10 stocks
```

### 3. Using the Swing Backtest Programmatically

For advanced users who want to run swing backtests directly:

```python
from backtesting import Backtester

# Create backtester
backtester = Backtester(initial_capital=10000.0)

# Fetch historical data
historical_data = backtester.fetch_historical_data_yfinance('AAPL', period='1y')

# Run swing backtest
results = backtester.run_swing_backtest(
    historical_data=historical_data,
    take_profit_pct=0.10,      # 10% take profit
    trailing_stop_pct=0.03,    # 3% trailing stop  
    stop_loss_pct=0.06,        # 6% stop loss
    min_hold_days=2,           # Min 2 days hold
    max_hold_days=10,          # Max 10 days hold
    capital=10000.0
)

# View results
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print(f"Total P&L: ${results['total_pnl']:.2f}")

# Generate detailed report
backtester.generate_report('my_backtest_report.json')
```

### 4. Run the Bot

```bash
./start_bot.sh
```

Or directly with Python:

```bash
./venv/bin/python3 main.py
```

Or run the backtesting module standalone:

```bash
./venv/bin/python3 backtesting.py
```

## How It Works

When `BACKTEST_MODE=true`, the bot:

1. **Loads Historical Data**: Fetches 1 year of daily price data from yfinance for selected symbols
2. **Simulates Trading**: For each historical date:
   - Checks if conditions are met to enter a position (BUY)
   - If already in a position, checks exit conditions:
     - **Take Profit**: Triggered when price reaches target (default: +10%)
     - **Trailing Stop**: Triggered when price drops from high (default: -3%)
3. **Records Results**: Tracks each trade with entry/exit prices, P&L, and reason for exit
4. **Calculates Metrics**: Computes overall win rate, total P&L, ROI, etc.
5. **Saves to JSON**: Exports detailed results to `backtest_history_<timestamp>.json`

## Understanding the Results

### Forward Simulation Results

After traditional backtesting completes, you'll see output like this:

```
============================================================
BACKTEST COMPLETED
============================================================
Initial Capital: $10000.00
Final Capital: $10750.50
Total P&L: +$750.50
ROI: +7.51%
Total Trades: 45
Win Rate: 71.11%
============================================================
```

### Swing Backtest Results (NEW!)

After swing backtesting completes, you'll see enhanced output:

```
============================================================
SWING TRADING BACKTEST COMPLETED
============================================================
Initial Capital: $10000.00
Final Capital: $10850.30
Total P&L: +$850.30
ROI: +8.50%
Total Trades: 52
Winning Trades: 37
Losing Trades: 15
Win Rate: 71.15% ✓ (Target: 70%)
Profit Factor: 2.35
Avg Win: $95.50
Avg Loss: $-40.25
Avg Risk/Reward: 1:2.37
Avg Holding Period: 5.3 days
============================================================
```

### Key Metrics Explained

- **Initial Capital**: Starting balance for the backtest
- **Final Capital**: Ending balance after all trades
- **Total P&L**: Profit or loss (Final - Initial)
- **ROI**: Return on Investment as a percentage
- **Total Trades**: Number of completed buy/sell cycles
- **Winning Trades**: Trades that closed with profit
- **Losing Trades**: Trades that closed with loss
- **Win Rate**: Percentage of winning trades (Winning / Total)
  - ✓ indicates achieving 70%+ target
  - ✗ indicates below 70% target
- **Profit Factor**: Gross profit divided by gross loss
  - 2.0+ is excellent (win twice as much as you lose)
  - 1.5-2.0 is good
  - 1.0-1.5 is acceptable
  - < 1.0 is losing strategy
- **Avg Win/Loss**: Average profit per winning trade / loss per losing trade
- **Avg Risk/Reward**: Ratio of average win to average loss
  - 1:2 means you make $2 for every $1 you risk
  - Higher is better
- **Avg Holding Period**: Average number of days positions are held
  - 2-10 days is typical for swing trading
  - < 2 days may indicate day trading behavior
  - > 10 days may indicate position trading

## Analyzing Results

### 1. Review the JSON File

The backtest saves detailed results to `backtest_history_<timestamp>.json`:

```json
{
  "metadata": {
    "timestamp": "2026-01-20T19:30:00.000000",
    "period": "1y",
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "initial_capital": 10000.0,
    "final_capital": 10750.5,
    "total_pnl": 750.5,
    "roi_percent": 7.51,
    "total_trades": 45,
    "winning_trades": 32,
    "losing_trades": 13,
    "win_rate": 0.7111,
    "parameters": {
      "risk_threshold": 0.02,
      "trailing_stop_percent": 0.03,
      "take_profit_percent": 0.10,
      "stop_loss_percent": 0.06,
      "position_size": 0.01,
      "min_allocation": 100,
      "max_allocation": 5000
    }
  },
  "trades": [
    {
      "date": "2025-02-15",
      "symbol": "AAPL",
      "action": "BUY",
      "price": 182.50,
      "result": {...}
    },
    {
      "date": "2025-02-20",
      "symbol": "AAPL",
      "action": "SELL",
      "price": 195.30,
      "triggered_by": "take_profit",
      "pnl": {
        "pnl": 128.00,
        "pnl_percent": 7.01,
        "holding_period_days": 5
      }
    },
    ...
  ]
}
```

### 2. Identify Best Performing Symbols

Look at which symbols generated the most profit or had the highest win rates.

### 3. Analyze Exit Triggers

Check what percentage of trades exited via:
- **take_profit**: Strategy worked as intended
- **trailing_stop**: Protected profits or cut losses
- **backtest_end**: Position held to end of test period

## Tuning for 70%+ Win Rate

To achieve a 70% or higher win rate with swing trading backtests, experiment with these parameter adjustments:

### Strategy 1: Asymmetric Risk/Reward (Recommended)

Use wider stops and tighter targets to increase win probability:

```python
results = backtester.run_swing_backtest(
    historical_data=data,
    take_profit_pct=0.06,     # Tighter target: 6%
    trailing_stop_pct=0.02,   # Tighter trailing: 2%
    stop_loss_pct=0.08,       # Wider stop: 8%
    min_hold_days=2,
    max_hold_days=10
)
```

**Trade-off**: Higher win rate but lower profit factor (smaller wins, larger losses)

### Strategy 2: Swing Sweet Spot

Balance between win rate and profit factor:

```python
results = backtester.run_swing_backtest(
    historical_data=data,
    take_profit_pct=0.08,     # Moderate target: 8%
    trailing_stop_pct=0.03,   # Standard trailing: 3%
    stop_loss_pct=0.06,       # Moderate stop: 6%
    min_hold_days=3,          # Longer minimum hold
    max_hold_days=12          # Extended max hold
)
```

**Trade-off**: Balanced approach for consistent performance

### Strategy 3: Trending Market Optimizer

For strong trending markets (bull or bear):

```python
results = backtester.run_swing_backtest(
    historical_data=data,
    take_profit_pct=0.12,     # Wider target to ride trends: 12%
    trailing_stop_pct=0.04,   # Wider trailing: 4%
    stop_loss_pct=0.05,       # Tighter stop: 5%
    min_hold_days=3,
    max_hold_days=15          # Longer hold for trends
)
```

**Trade-off**: Lower win rate (50-60%) but higher profit factor (3.0+)

### Strategy 4: High-Probability Scalper

For choppy/ranging markets:

```python
results = backtester.run_swing_backtest(
    historical_data=data,
    take_profit_pct=0.04,     # Very tight target: 4%
    trailing_stop_pct=0.015,  # Very tight trailing: 1.5%
    stop_loss_pct=0.06,       # Moderate stop: 6%
    min_hold_days=1,          # Allow quick exits
    max_hold_days=5           # Short hold period
)
```

**Trade-off**: Highest win rate potential (75%+) but lowest profit factor

### Parameter Guidelines

| Metric | Conservative (High Win Rate) | Balanced | Aggressive (High Returns) |
|--------|------------------------------|----------|---------------------------|
| Take Profit | 4-6% | 8-10% | 12-15% |
| Trailing Stop | 1.5-2% | 3-4% | 4-5% |
| Stop Loss | 6-8% | 5-6% | 4-5% |
| Min Hold Days | 1-2 | 2-3 | 3-5 |
| Max Hold Days | 5-7 | 10-12 | 15-20 |
| Expected Win Rate | 70-80% | 60-70% | 50-60% |
| Expected Profit Factor | 1.2-1.8 | 1.8-2.5 | 2.5-4.0 |

### Tips for Optimization

1. **Test Multiple Periods**: Run backtests on 1y, 2y, and 5y data
2. **Different Market Conditions**: Test in bull markets, bear markets, and sideways markets
3. **Symbol Selection**: Higher quality stocks (liquid, low volatility) tend to have higher win rates
4. **Avoid Overfitting**: Don't optimize parameters on the same data you'll trade on
5. **Focus on Profit Factor**: Win rate alone doesn't guarantee profitability
   - 70% win rate with 1:0.5 R:R = losing strategy
   - 60% win rate with 1:2 R:R = profitable strategy
6. **Holding Period Matters**: Respect min_hold_days to avoid "lucky" exits

## Comparing Different Strategies

To test multiple parameter sets:

1. Run backtest with Strategy 1 parameters
2. Note the win rate and ROI in the results file
3. Update `.env` with Strategy 2 parameters
4. Run backtest again
5. Compare `backtest_history_*.json` files to find optimal settings

## Tips for Successful Backtesting

1. **Start with Reasonable Defaults**: Don't make extreme parameter changes initially
2. **Test Multiple Periods**: Try different date ranges to validate consistency
3. **Consider Market Conditions**: Bear markets vs. bull markets will affect results
4. **Don't Overfit**: Parameters that work perfectly on historical data may not work in live trading
5. **Review Individual Trades**: Look for patterns in winning vs. losing trades
6. **Test Multiple Symbol Sets**: Different stocks behave differently

## Limitations

- **Historical Data Only**: Backtesting uses past data; past performance doesn't guarantee future results
- **No Slippage Modeling**: Assumes you can buy/sell at exact prices (real trading has slippage)
- **No Market Impact**: Assumes your orders don't affect the market
- **Daily Data**: Uses daily OHLC data, not intraday tick data
- **Simplified Exit Logic**: Uses high/low prices for stop checks, which may be optimistic

## Switching Back to Live/Paper Trading

To disable backtesting mode and return to normal trading:

```bash
BACKTEST_MODE=false
```

Or remove the line from your `.env` file entirely (defaults to false).

## Troubleshooting

### "No historical data available"

**Solution**: Ensure you have internet connectivity and yfinance can fetch data for the symbols in your `scan_symbols.txt` file.

### "No symbols available for backtesting"

**Solution**: 
- Check that `scan_symbols.txt` exists and contains valid stock symbols
- Or enable `ENABLE_STOCK_SCREENER=true` to automatically discover symbols

### Win rate is too low

**Solution**:
- Adjust parameters as described in "Tuning for 70%+ Win Rate" section
- Consider using higher quality stocks with better liquidity
- Review individual trades to understand what's causing losses

### Backtest runs very slowly

**Solution**:
- Reduce `MAX_DISCOVERED_STOCKS` to test fewer symbols
- Use a shorter period (though this may reduce statistical significance)
- Ensure yfinance data is cached properly

## Next Steps

After backtesting:

1. **Review Results**: Analyze win rate, P&L, and trade details
2. **Optimize Parameters**: Adjust settings to improve performance
3. **Paper Trade**: Switch to `BACKTEST_MODE=false` and `PAPER_TRADING_MODE=true` to test in real-time
4. **Live Trade**: Only after confirming success in paper trading, switch to live mode

## Support

For questions or issues with backtesting mode:
- Check existing issues: https://github.com/operator/market-pie5-bot/issues
- Review project status: `PROJECT_STATUS.md`
- Create a new issue with details about your backtest configuration and results

---

**Happy Backtesting! 🚀📈**
