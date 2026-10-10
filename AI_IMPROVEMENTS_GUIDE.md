# AI-Recommended Trading Parameter Improvements

> **⚠️ ARCHITECTURE UPDATE (2026).** Parameter suggestions no longer come from an
> LLM. **`ml_param_optimizer.py`** uses **backtest heuristics** (win rate,
> drawdown, Sharpe → bounded param nudges). The LLM may **explain** changes via
> `GET /api/ai/optimization-suggestions?explain=true` but never chooses values.
> Historical sections below describe an **earlier HuggingFace/LLM experiment**;
> see [docs/ML_AND_AI_ARCHITECTURE.md](docs/ML_AND_AI_ARCHITECTURE.md).

## Overview

This document describes trading parameter improvements. **Current production path:**
heuristic optimizer + optional operator review (`BOT_ENABLE_AI_AUTO_TWEAK=false` by default).

## Performance Analysis

The AI analysis identified the following issues with the bot's trading strategy:

- **Win Rate**: 10% (very low)
- **Total P&L**: -$3.36 (-0.03% of starting capital)
- **Total Trades**: 10
- **Problem**: Bot was taking on too much risk with poor results

## AI Recommendations

The AI model (`app-chat` alias on the ALFa AI brain / LiteLLM) analyzed the trading history and recommended the following parameter adjustments:

```json
{
  "trading_frequency": 2,
  "max_consecutive_losses": 3,
  "stop_loss_percent": 0.06,
  "trailing_stop_percent": 0.03,
  "risk_threshold": 0.02,
  "position_sizing": 0.01
}
```

## Implemented Changes

### 1. Risk Threshold (BOT_RISK_THRESHOLD)
- **Old Value**: 0.07 (7%)
- **New Value**: 0.02 (2%)
- **Impact**: Reduces maximum risk exposure per trade from 7% to 2% of total capital
- **Benefit**: Dramatically limits potential losses on any single trade

### 2. Trailing Stop (BOT_TRAILING_STOP_PERCENT)
- **Old Value**: 0.05 (5%)
- **New Value**: 0.03 (3%)
- **Impact**: Positions are exited when price drops 3% from high instead of 5%
- **Benefit**: Locks in profits earlier and reduces drawdown from winning positions

### 3. Position Size (BOT_POSITION_SIZE)
- **Old Value**: 0.05 (5%)
- **New Value**: 0.01 (1%)
- **Impact**: Each position is now 1% of capital instead of 5%
- **Benefit**: Smaller positions reduce the magnitude of losses

### 4. Stop Loss (BOT_STOP_LOSS_PERCENT)
- **Old Value**: 0.05 (5%)
- **New Value**: 0.06 (6%)
- **Impact**: Maximum loss per trade is 6% instead of 5%
- **Benefit**: Provides slightly more room for price movement while still limiting losses

### 5. Trading Frequency (TRADING_FREQUENCY)
- **Old Value**: Random delay between 1-5 seconds
- **New Value**: Fixed 2 second delay
- **Impact**: More predictable trade execution timing
- **Benefit**: Reduces overtrading and provides consistent execution

### 6. Max Consecutive Losses (BOT_MAX_CONSECUTIVE_LOSSES)
- **Old Value**: 3
- **New Value**: 3
- **Impact**: No change
- **Note**: Already at optimal value per AI recommendation

## Configuration Examples

### Environment Variables (.env file)

```bash
# More conservative risk settings (AI recommended)
BOT_RISK_THRESHOLD=0.02
BOT_TRAILING_STOP_PERCENT=0.03
BOT_POSITION_SIZE=0.01
BOT_STOP_LOSS_PERCENT=0.06
TRADING_FREQUENCY=2
```

### Example Risk Calculation

With a $10,000 trading account:

**Old Settings:**
- Risk per trade: 7% × $10,000 = $700
- Position size: 5% × $10,000 = $500

**New Settings:**
- Risk per trade: 2% × $10,000 = $200
- Position size: 1% × $10,000 = $100

**Result**: 72% reduction in risk exposure per trade!

## Expected Impact

The AI analysis suggests these changes will:

1. **Reduce Risk**: Lower risk threshold (2% vs 7%) dramatically limits exposure
2. **Preserve Capital**: Smaller positions (1% vs 5%) reduce loss magnitude
3. **Lock in Gains**: Tighter trailing stop (3% vs 5%) captures profits earlier
4. **Cut Losses**: Slightly wider stop loss (6% vs 5%) with smaller positions results in smaller absolute losses
5. **Control Trading**: Fixed frequency (2s) prevents overtrading

## Validation

All changes have been validated through:

1. **Unit Tests**: 122 tests pass successfully
2. **Configuration Tests**: All parameter values verified
3. **Behavior Tests**: Bot behavior validated with new settings
4. **Code Review**: No issues found
5. **Security Scan**: No vulnerabilities detected

## Testing the Changes

To validate the changes in your environment:

```bash
# Run the AI improvements validation script
python3 test_ai_improvements.py

# Run the full test suite
python3 -m unittest discover -s . -p 'test_*.py'
```

## Migration Guide

If you have an existing `.env` file, update it with the new values:

```bash
# Backup your existing .env
cp .env .env.backup

# Update with new values from .env.example
# Or manually update these specific values:
BOT_RISK_THRESHOLD=0.02
BOT_TRAILING_STOP_PERCENT=0.03
BOT_POSITION_SIZE=0.01
BOT_STOP_LOSS_PERCENT=0.06
TRADING_FREQUENCY=2
```

## Monitoring

After implementing these changes, monitor:

1. **Win Rate**: May initially stay low or decrease, but losses should be smaller
2. **Average Loss**: Should decrease significantly (smaller positions)
3. **Maximum Drawdown**: Should decrease (lower risk threshold)
4. **Trade Frequency**: Should be more consistent (fixed 2s delay)
5. **Capital Preservation**: Total capital should decline more slowly during losing streaks

## Conclusion

These AI-recommended changes make the bot significantly more conservative and risk-averse. While the win rate may not immediately improve, the magnitude of losses should decrease substantially, leading to better overall capital preservation and long-term performance.

## Enhanced Trade Data for AI Analysis (v1.1+)

Starting in version 1.1, the bot now captures comprehensive trade data to enable more sophisticated AI analysis and recommendations. Every trade now includes:

### Data Fields Captured

1. **Core Trade Information**
   - Symbol, action (BUY/SELL), quantity, timestamp
   - Trading mode (sandbox, simulation, live)

2. **Entry/Exit Metrics**
   - Entry price: Price at position open
   - Exit price: Price at position close
   - Hold duration: Time held in hours

3. **Performance Metrics**
   - P&L (dollars): Absolute profit or loss
   - P&L percentage: Percentage return
   - Win/loss flag: Binary outcome

4. **Exit Conditions**
   - Exit reason: trailing_stop, target_reached, end_of_simulation, etc.
   - Volatility at exit: Market conditions
   - Volume: Trading activity

### Benefits for AI Analysis

With this enhanced data, AI models can now:

1. **Optimize Exit Strategies**
   - Analyze which exit reasons correlate with best outcomes
   - Identify optimal stop loss and take profit levels
   - Detect patterns in trailing stop effectiveness

2. **Improve Timing**
   - Study hold duration vs. profitability
   - Recommend ideal entry/exit timing
   - Identify overtrading or undertrading patterns

3. **Risk Management**
   - Correlate volatility with trade outcomes
   - Adjust position sizing based on market conditions
   - Optimize risk/reward ratios

4. **Market Conditions**
   - Factor in volume and volatility
   - Adapt strategies to different market regimes
   - Identify favorable trading conditions

### Viewing Enhanced Data

The web GUI now displays all this data in the Trade History tab:

```
Trade: AAPL ✅ Win
----------------------------------------
Action: BUY 10.00 shares
Entry: $150.00  |  Exit: $157.50
P&L: +$75.00 (+5.00%)
Exit: Trailing Stop  |  Hold: 2.5h
Vol: 1,500,000  |  Volatility: 3.24%
```

### AI Integration

Future AI models can access this data via:

```python
# Get comprehensive trade history
trades = bot.trade_history

# Each trade includes full metrics
for trade in trades:
    print(f"Entry: ${trade['entry_price']}")
    print(f"Exit: ${trade['exit_price']}")
    print(f"P&L: ${trade['pnl']} ({trade['pnl_percent']}%)")
    print(f"Exit Reason: {trade['exit_reason']}")
    print(f"Hold Duration: {trade['hold_duration']} hours")
```

This comprehensive data enables AI to generate much more actionable recommendations for improving trading performance.

## Win Rate Auto-Tuning (v1.2+)

Starting in version 1.2, the bot includes automatic win rate optimization using ML parameter tuning. This feature automatically adjusts trading parameters when the win rate falls below the target.

### How It Works

1. **Target Win Rate**: Configurable via `WIN_RATE_TARGET` environment variable (default: 70%)
2. **Automatic Detection**: When actual win rate drops below target (and ≥10 trades executed)
3. **ML Optimization**: Triggers **backtest heuristic** parameter optimization (`ml_param_optimizer.py`) — not the LLM
4. **Parameter Adjustment**: Automatically applies optimized parameters when `auto_apply=True`

### Configuration

Add to your `.env` file:

```bash
# Win rate target for auto-tuning (default: 70%)
WIN_RATE_TARGET=0.70

# Optional: auto-apply heuristic params (default: false)
# BOT_ENABLE_AI_AUTO_TWEAK=false

# LLM only for optional explanation (?explain=true), not for param values
# LITELLM_ENABLED=true
```

### Triggering Conditions

Auto-tuning is triggered when ALL of the following are met:

1. Current win rate < `WIN_RATE_TARGET` (default: 70%)
2. Total trades executed ≥ 10 (minimum sample size)
3. `apply_ai_suggestions()` is called with `auto_apply=True` (or `BOT_ENABLE_AI_AUTO_TWEAK=true`)
4. Heuristic optimizer returns improved parameters (no LLM required)

### What Gets Optimized

The ML optimizer analyzes trade history and adjusts:

- **Risk Threshold**: Optimal risk per trade (1-5%)
- **Trailing Stop**: Dynamic stop loss percentage (2-10%)
- **Stop Loss**: Maximum loss per trade (3-8%)
- **Take Profit**: Target profit percentage (5-15%)
- **Allocation Sizes**: Min/max position sizes ($50-$1000)
- **Trading Frequency**: Time between trades (1-5 seconds)

### Example Usage

```python
from main import TradingBot

# Initialize bot
bot = TradingBot(total_capital=10000.0)

# ... execute trades ...

# Check win rate and trigger optimization
if bot.track_record['win_rate'] < 0.70:
    ai_response = bot.send_track_record_to_ai()
    
    # Auto-apply ML-optimized parameters
    bot.apply_ai_suggestions(ai_response, auto_apply=True)
    
    # Or review suggestions before applying
    bot.apply_ai_suggestions(ai_response, auto_apply=False)
```

### Monitoring

After auto-tuning is triggered, monitor:

1. **Predicted Win Rate**: ML model's prediction for new parameters
2. **Parameter Changes**: Which parameters were adjusted and by how much
3. **Alert Notifications**: Bot sends alerts when auto-tuning is applied
4. **Actual Performance**: Track if win rate improves over next 10-20 trades

### Benefits

- **Adaptive Strategy**: Bot learns from its own performance
- **Data-Driven Optimization**: Uses ML to find optimal parameters
- **Automatic Adjustment**: No manual parameter tuning needed
- **Risk-Managed**: Parameters stay within safe bounds (validated ranges)
- **Continuous Improvement**: Re-optimizes as more trade data is collected

### Logging

Auto-tuning logs are prefixed with `[WIN RATE AUTO-TUNE]`:

```
[WIN RATE AUTO-TUNE] Current win rate 55.0% is below target 70.0%
[WIN RATE AUTO-TUNE] Triggering ML parameter optimization...
[WIN RATE AUTO-TUNE] ML optimization suggests 72.0% win rate
[WIN RATE AUTO-TUNE] Applied 1 ML-optimized parameters
```

### Testing

Run the test suite to verify auto-tuning functionality:

```bash
python3 test_win_rate_auto_tuning.py
```

This will validate:
- WIN_RATE_TARGET constant is set correctly
- Win rate check triggers ML optimization
- Minimum trade requirement (10 trades)
- Parameter application when auto_apply=True
- Logging and alert notifications

## References

- AI Model: `app-chat` alias via the ALFa AI brain (LiteLLM)
- Analysis Date: 2026-01-16
- Implementation PR: [Link to PR]
- Win Rate Auto-Tuning: 2026-01-21

---

**Note**: These are default values. You can adjust them in your `.env` file to find the optimal balance for your trading strategy and risk tolerance.
