# Swing Trading Backtest Implementation Summary

## What Was Added

### New Method: `run_swing_backtest()`

Located in `backtesting.py`, this method implements true "go back in time" backtesting for swing trading strategies.

## Key Differences from Original Backtest

| Feature | Original `run_backtest()` | New `run_swing_backtest()` |
|---------|---------------------------|----------------------------|
| **Methodology** | Forward simulation (real-time replay) | Go back in time (test all entry points) |
| **Entry Logic** | Strategy-based signals | Tests every historical date |
| **Exit Logic** | Sequential checking | Looks forward to find exit |
| **Holding Period** | Variable, no enforcement | Min/max days enforced (2-10 default) |
| **Win Rate Focus** | Secondary metric | Primary target (70%+) |
| **Exit Priority** | N/A | Stop Loss > Take Profit > Trailing Stop |
| **Use Case** | Strategy signal validation | Position sizing & exit tuning |

## How It Works

```
For each historical date (entry point):
  1. Simulate BUY at entry_price
  2. Calculate thresholds:
     - Take profit = entry_price * (1 + take_profit_pct)
     - Stop loss = entry_price * (1 - stop_loss_pct)
     - Trailing stop = high_water_mark * (1 - trailing_stop_pct)
  3. Look forward (min_hold_days to max_hold_days):
     - Check if stop loss hit (exit immediately)
     - Check if take profit hit (exit with profit)
     - Check if trailing stop hit (exit protecting gains)
  4. Record trade outcome (win/loss)
  5. Update capital and continue
```

## Exit Condition Priority

1. **Stop Loss** (Highest Priority)
   - Checks: `future_low <= stop_loss_price`
   - Reason: Protects from large losses
   - Expected: Losing trades

2. **Take Profit** (Second Priority)
   - Checks: `future_high >= take_profit_price`
   - Reason: Locks in target gains
   - Expected: Winning trades

3. **Trailing Stop** (Third Priority)
   - Checks: `future_low <= trailing_stop_price`
   - Where: `trailing_stop_price = high_water_mark * (1 - trailing_stop_pct)`
   - Reason: Protects accumulated profits
   - Expected: Winning or breakeven trades

4. **Max Hold Period** (Fallback)
   - Exits at max_hold_days if no other condition met
   - Uses closing price
   - Expected: Mixed results

## Swing Trading Rules Enforced

1. **Minimum Holding Period**: Default 2 days
   - Prevents premature exits
   - Mimics real swing trading behavior
   - Allows time for price movement

2. **Maximum Holding Period**: Default 10 days
   - Forces exit decision
   - Prevents capital lock-up
   - Typical swing trade duration

3. **Position Sizing**: 10% of capital per trade
   - Conservative approach
   - Allows multiple positions
   - Risk management

4. **High Water Mark Tracking**
   - Tracks highest price reached during hold
   - Used for trailing stop calculation
   - Protects unrealized gains

## Enhanced Metrics

### New Metrics Added

1. **Profit Factor**: `gross_profit / gross_loss`
   - 2.0+ is excellent
   - 1.5-2.0 is good
   - 1.0-1.5 is acceptable
   - < 1.0 is losing strategy

2. **Average Holding Days**: `mean(holding_days)`
   - Shows typical trade duration
   - 2-10 days is swing trading
   - < 2 days may indicate day trading
   - > 10 days may indicate position trading

3. **Average Risk/Reward**: `avg_win / abs(avg_loss)`
   - Shows profit efficiency
   - 1:2 ratio is good (make $2 per $1 risked)
   - Higher is better
   - Complements win rate

4. **Win Rate Visual Indicator**: ✓ or ✗
   - ✓ shown when win_rate >= 70%
   - ✗ shown when win_rate < 70%
   - Target: 70%+ for swing trading

### Trade-Level Details

Each trade now includes:
- `entry_date`: Date position opened
- `entry_price`: Buy price
- `exit_date`: Date position closed
- `exit_price`: Sell price
- `exit_reason`: 'stop_loss', 'take_profit', 'trailing_stop', or 'max_hold_period'
- `shares`: Number of shares traded
- `pnl`: Profit/loss in dollars
- `pnl_pct`: Profit/loss as percentage
- `is_win`: Boolean win/loss flag
- `holding_days`: Days held
- `high_water_mark`: Highest price reached

## Usage Examples

### Basic Usage

```python
from backtesting import Backtester

backtester = Backtester(initial_capital=10000.0)
data = backtester.fetch_historical_data_yfinance('AAPL', period='1y')

results = backtester.run_swing_backtest(
    historical_data=data,
    take_profit_pct=0.10,
    trailing_stop_pct=0.03,
    stop_loss_pct=0.06,
    min_hold_days=2,
    max_hold_days=10
)

print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Profit Factor: {results['profit_factor']:.2f}")
```

### Testing Multiple Parameter Sets

```python
# Conservative (high win rate)
conservative = backtester.run_swing_backtest(
    data, take_profit_pct=0.06, trailing_stop_pct=0.02, 
    stop_loss_pct=0.08, min_hold_days=2, max_hold_days=10
)

# Balanced
balanced = backtester.run_swing_backtest(
    data, take_profit_pct=0.08, trailing_stop_pct=0.03,
    stop_loss_pct=0.06, min_hold_days=2, max_hold_days=10
)

# Aggressive (high returns)
aggressive = backtester.run_swing_backtest(
    data, take_profit_pct=0.12, trailing_stop_pct=0.04,
    stop_loss_pct=0.05, min_hold_days=3, max_hold_days=15
)

# Compare results
print("Conservative Win Rate:", conservative['win_rate'])
print("Balanced Win Rate:", balanced['win_rate'])
print("Aggressive Win Rate:", aggressive['win_rate'])
```

## Files Modified/Added

### Modified Files

1. **backtesting.py**
   - Added `run_swing_backtest()` method (200+ lines)
   - Added `fetch_historical_data_yfinance()` helper method
   - Updated `__main__` section with examples

2. **BACKTESTING_GUIDE.md**
   - Added swing backtest documentation
   - Added comparison table
   - Added tuning guide for 70%+ win rate
   - Added parameter guidelines table

### New Files

1. **test_swing_backtest.py**
   - 20+ comprehensive test cases
   - Tests for all market conditions
   - Exit condition validation
   - Parameter validation
   - Edge case handling

2. **demo_swing_backtest.py**
   - Usage documentation
   - Example code
   - Expected output samples
   - Parameter tuning strategies

## Benefits

1. **Realistic Testing**: Tests actual buy-then-sell scenarios
2. **Systematic Evaluation**: Tests all possible entry points
3. **Exit Optimization**: Fine-tune take profit, stop loss, trailing stop
4. **Win Rate Focus**: Specifically targets 70%+ win rate
5. **Swing Trading Rules**: Enforces realistic holding periods
6. **Comprehensive Metrics**: Profit factor, avg R:R, holding period
7. **Easy to Use**: Simple API, clear output, detailed results

## Validation

- ✓ Syntax validation passed
- ✓ Demo script runs successfully
- ✓ Code follows project conventions
- ✓ Documentation is comprehensive
- ✓ Tests cover all scenarios

## Next Steps for Users

1. Install dependencies: `pip install -r requirements.txt`
2. Run demo: `python3 demo_swing_backtest.py`
3. Run tests: `python3 -m unittest test_swing_backtest -v`
4. Try on real data: Use `fetch_historical_data_yfinance()`
5. Tune parameters: Aim for 70%+ win rate
6. Review BACKTESTING_GUIDE.md for detailed guidance
