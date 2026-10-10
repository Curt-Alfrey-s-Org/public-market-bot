# Better Mimic Live in Sim - Implementation Guide

This guide documents the new features that make simulation mode more realistic and closer to live trading behavior.

## Overview

Three major enhancements have been implemented to better mimic live trading in simulation:

1. **Historical Simulation with Frozen Time** - Backtest with deterministic date progression
2. **PDT Rule Enforcement in All Modes** - Realistic Pattern Day Trading limits
3. **ML Parameter Optimization** - AI-powered tuning for 70% win rate target

## Feature 1: Historical Simulation with Frozen Time

### Purpose

Previously, simulations always used current market data. Now you can "freeze time" and replay historical markets with exact date control, enabling:

- Deterministic backtesting (same results every run)
- Multi-day strategy testing without market changes
- Historical event analysis

### Usage

```python
from main import TradingBot

# Initialize bot
bot = TradingBot(total_capital=10000.0)

# Enable historical mode with date range
bot.enable_historical_mode('2023-01-01', '2023-12-31')

# Load historical data for symbols
bot.load_historical_data('AAPL', '2023-01-01', '2023-12-31')
bot.load_historical_data('MSFT', '2023-01-01', '2023-12-31')

# Get prices - automatically uses historical data
price, volume = bot.get_stock_price('AAPL')  # Gets price at current_sim_date

# Advance simulation time
bot.advance_sim_date(days=1)  # Move forward 1 day

# Continue trading with new date
price, volume = bot.get_stock_price('AAPL')  # Gets price at new date
```

### Key Methods

**`enable_historical_mode(start_date, end_date)`**
- Enables frozen time simulation
- Sets current simulation date to start_date
- Parameters: ISO format dates 'YYYY-MM-DD'

**`load_historical_data(symbol, start_date, end_date)`**
- Loads historical OHLCV data from yfinance
- Caches data for fast access during simulation
- Must be called before trading each symbol

**`advance_sim_date(days=1)`**
- Moves simulation forward by specified days
- Use to progress through historical data

**`get_historical_price(symbol)`**
- Returns price at current_sim_date
- Returns (price, volume) tuple or None
- Automatically called by get_stock_price() in historical mode

### Example: Backtesting Q1 2023

```python
bot = TradingBot(total_capital=10000.0)

# Set up historical simulation
bot.enable_historical_mode('2023-01-01', '2023-03-31')

# Load data for symbols
symbols = ['AAPL', 'MSFT', 'GOOGL']
for symbol in symbols:
    bot.load_historical_data(symbol, '2023-01-01', '2023-03-31')

# Simulate trading day by day
while bot.current_sim_date <= bot.historical_end:
    print(f"\nTrading on {bot.current_sim_date.strftime('%Y-%m-%d')}")
    
    for symbol in symbols:
        price, volume = bot.get_stock_price(symbol)
        # Execute trading logic here
        
    bot.advance_sim_date(days=1)

bot.print_summary()
```

## Feature 2: PDT Rule Enforcement in All Modes

### Purpose

Previously, PDT (Pattern Day Trading) rules were **disabled** in paper/sandbox modes, allowing unlimited day trades. This was unrealistic because:

- Users developed strategies that wouldn't work in live trading
- No preparation for PDT constraints
- False confidence in win rates

Now, PDT rules are **enforced in ALL modes** (paper, sandbox, production) to provide realistic training.

### What Changed

**Before:**
- Paper mode: Unlimited day trades ✗
- Sandbox mode: Unlimited day trades ✗
- Production mode: PDT enforced ✓

**After:**
- Paper mode: PDT enforced ✓
- Sandbox mode: PDT enforced ✓
- Production mode: PDT enforced ✓

### PDT Rules (Enforced in ALL modes)

- Accounts with capital **< $25,000**: Max 3 day trades per 5 business days
- Accounts with capital **≥ $25,000**: Unlimited day trades
- A "day trade" = buying and selling the same symbol on the same day

### Code Changes

The `check_pdt_compliance()` method now returns:

```python
# Before (Paper mode)
return True, "PDT rules disabled (simulation mode - unlimited day trades)"

# After (Paper mode)
if count >= 3 and self.total_capital < 25000:
    return False, f"PDT Limit Reached in simulation: {count}/3 day trades"
return True, f"PDT OK (simulation): {count}/3 day trades"
```

### Impact on Testing

**If you have capital < $25k:**
```python
bot = TradingBot(total_capital=10000.0)

# Simulate 3 day trades
bot.add_day_trade('AAPL')
bot.add_day_trade('MSFT')
bot.add_day_trade('GOOGL')

# 4th day trade will be blocked
can_trade, msg = bot.check_pdt_compliance()
# Returns: (False, "PDT Limit Reached in simulation: 3/3 day trades")
```

**To avoid PDT limits during testing:**
```python
# Option 1: Use capital ≥ $25k
bot = TradingBot(total_capital=30000.0)

# Option 2: Space out trades (don't day trade)
# Wait until next day to sell positions
```

### Benefits

1. **Realistic Training**: Learn to work within PDT constraints
2. **Strategy Validation**: Ensure strategies work with PDT limits
3. **Smooth Transition**: Move from sim to live without surprises

## Feature 3: ML Parameter Optimization (70% Win Rate Target)

### Purpose

Manually tuning 10+ trading parameters is time-consuming and suboptimal. The new ML optimizer uses HuggingFace AI to intelligently optimize parameters based on backtest results, targeting a **70% win rate**.

### Parameters Optimized

The ML optimizer tunes these 10 parameters:

1. `BOT_RISK_THRESHOLD` (0.01 - 0.05)
2. `BOT_TRAILING_STOP_PERCENT` (0.02 - 0.10)
3. `BOT_STOP_LOSS_PERCENT` (0.03 - 0.08)
4. `BOT_TAKE_PROFIT_PERCENT` (0.05 - 0.15)
5. `BOT_MAX_CONSECUTIVE_LOSSES` (2 - 5)
6. `BOT_MIN_ALLOCATION` ($50 - $200)
7. `BOT_MAX_ALLOCATION` ($300 - $1000)
8. `TRADING_FREQUENCY` (1 - 5 seconds)
9. `MIN_TRAILING_STOP` (0.01 - 0.05)
10. `MAX_TRAILING_STOP` (0.05 - 0.15)

### Setup

**1. Get HuggingFace API Key:**
- Visit: https://huggingface.co/settings/tokens
- Create a new token
- Add to `.env`:
```bash
HUGGINGFACE_API_KEY=hf_your_token_here
```

**2. Run Backtests:**
```python
from backtesting import Backtester
from backtrader_engine import run_backtest

# Run multiple backtests with different parameters
backtest_results = []

for risk_threshold in [0.02, 0.03, 0.04]:
    result = run_backtest(
        strategy='SMA',
        symbols=['AAPL', 'MSFT'],
        start_date='2023-01-01',
        end_date='2023-12-31',
        initial_capital=10000,
        risk_per_trade=risk_threshold
    )
    backtest_results.append(result)
```

**3. Optimize Parameters:**
```python
from main import TradingBot

bot = TradingBot(total_capital=10000.0)

# Run ML optimization
optimized_params, predicted_win_rate = bot.optimize_parameters_ml(backtest_results)

print(f"Predicted Win Rate: {predicted_win_rate:.1%}")
print("Optimized Parameters:")
for key, value in optimized_params.items():
    print(f"  {key}: {value}")
```

**4. Apply Optimized Parameters:**

The optimizer saves results to `ml_optimization_<timestamp>.json`. Update your `.env` with the suggested values:

```json
{
  "timestamp": "2024-01-20T12:00:00",
  "target_win_rate": 0.70,
  "predicted_win_rate": 0.72,
  "optimized_parameters": {
    "BOT_RISK_THRESHOLD": 0.025,
    "BOT_TRAILING_STOP_PERCENT": 0.04,
    "BOT_STOP_LOSS_PERCENT": 0.05,
    ...
  }
}
```

### How It Works

1. **Analysis Phase**: Analyzes your backtest results
   - Calculates average win rate, ROI, Sharpe ratio, max drawdown
   - Identifies performance patterns

2. **ML Optimization**: Sends data to HuggingFace (Meta-Llama-3-8B-Instruct)
   - Provides current performance metrics
   - Specifies target: 70% win rate
   - Defines parameter constraints

3. **Parameter Tuning**: AI suggests optimized parameters
   - Considers risk/reward tradeoffs
   - Balances win rate with drawdown
   - Optimizes for consistency

4. **Validation**: Validates all suggested parameters
   - Ensures values within safe ranges
   - Applies domain constraints
   - Prevents extreme/dangerous values

### Advanced Usage

**Custom Target Win Rate:**
```python
from ml_param_optimizer import MLParameterOptimizer

# Target 65% win rate instead of 70%
optimizer = MLParameterOptimizer(target_win_rate=0.65)
```

**Optimization from Trade History:**
```python
# Optimize using bot's trade history instead of backtests
bot = TradingBot(total_capital=10000.0)
# ... execute trades ...

# Optimize based on actual trading results
optimized_params, predicted_win_rate = bot.optimize_parameters_ml()
```

**Batch Optimization:**
```python
import glob
import json

# Load all backtest results
backtest_files = glob.glob('backtest_results_*.json')
backtest_results = []
for file in backtest_files:
    with open(file, 'r') as f:
        backtest_results.append(json.load(f))

# Optimize across all backtests
bot.optimize_parameters_ml(backtest_results)
```

## Integration in main()

The new features are automatically integrated into the main trading loop:

```python
def main():
    # ... bot initialization ...
    
    # ML Parameter Optimization runs at the end
    logger.info("\n--- ML Parameter Optimization (70% Win Rate Target) ---")
    if bot.ml_optimizer and bot.ml_optimizer.is_api_configured():
        optimized_params, predicted_win_rate = bot.optimize_parameters_ml()
        
        if optimized_params:
            logger.info(f"✓ ML Optimization Complete!")
            logger.info(f"  Current Win Rate: {bot.track_record['win_rate']:.1%}")
            logger.info(f"  Predicted Win Rate: {predicted_win_rate:.1%}")
            logger.info(f"  Target Win Rate: 70%")
            # ... display parameters ...
```

## Environment Variables

No new environment variables required. Uses existing:

- `HUGGINGFACE_API_KEY`: Required for ML optimization
- Existing bot parameters: Used as starting point for optimization

## Testing

Run the test suite:

```bash
# Test all features
python3 -m unittest test_better_sim_mimic -v

# Test specific features
python3 -m unittest test_better_sim_mimic.TestHistoricalSimulation -v
python3 -m unittest test_better_sim_mimic.TestPDTEnforcement -v
python3 -m unittest test_better_sim_mimic.TestMLParameterOptimization -v
```

## Troubleshooting

### Historical Simulation

**Issue**: "No historical data loaded for {symbol}"
- **Fix**: Call `load_historical_data()` before trading the symbol

**Issue**: Historical data returns None
- **Fix**: Ensure simulation date is within loaded data range

### PDT Enforcement

**Issue**: PDT blocking trades in paper mode
- **Expected Behavior**: This is intentional for realistic simulation
- **Solution**: Increase capital to ≥ $25k or avoid day trading

### ML Optimization

**Issue**: "HuggingFace API not configured"
- **Fix**: Set `HUGGINGFACE_API_KEY` in `.env` file

**Issue**: ML optimization returns no suggestions
- **Fix**: Ensure backtest results have required fields: `win_rate`, `roi`, `sharpe_ratio`, `max_drawdown`

**Issue**: API timeout
- **Fix**: HuggingFace API may be busy. Retry after a few minutes.

## Migration Guide

### From Old PDT Behavior

**Before (Paper mode had unlimited day trades):**
```python
# This worked in old version
bot = TradingBot(total_capital=1000.0)
for i in range(10):  # 10 day trades, no problem
    bot.execute_trade('AAPL', 'BUY', 150.0)
    bot.execute_trade('AAPL', 'SELL', 155.0)
```

**After (PDT enforced):**
```python
# Need capital ≥ $25k or space out trades
bot = TradingBot(total_capital=30000.0)  # Option 1: High capital
# OR
bot = TradingBot(total_capital=1000.0)  # Option 2: Low capital
# Only do 3 day trades, wait until next day for more
```

### From Random Simulation to Historical

**Before:**
```python
bot = TradingBot(total_capital=10000.0)
price, volume = bot.get_stock_price('AAPL')  # Random or current price
```

**After (Historical):**
```python
bot = TradingBot(total_capital=10000.0)
bot.enable_historical_mode('2023-01-01', '2023-12-31')
bot.load_historical_data('AAPL', '2023-01-01', '2023-12-31')
price, volume = bot.get_stock_price('AAPL')  # Historical price
```

## Summary

These three features work together to provide:

1. **Deterministic Testing** via historical simulation
2. **Realistic Constraints** via PDT enforcement
3. **Optimized Performance** via ML parameter tuning

The goal: Build strategies that work in simulation **and** live trading, with a target 70% win rate.
