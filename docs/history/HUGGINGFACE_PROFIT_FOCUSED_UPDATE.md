> **⚠️ DEPRECATED / HISTORICAL.** HuggingFace has been fully removed from market-pie5-bot. AI inference now uses the ALFa AI brain (LiteLLM) on ``. This document is retained for historical context only. See [docs/ALFA_AI_HOW_TO_USE.md](docs/ALFA_AI_HOW_TO_USE.md) and [docs/ENV_VARS.md](docs/ENV_VARS.md) for the current approach.

# HuggingFace ML Optimizer - Profit-Focused Update

## Summary

Modified `ml_param_optimizer.py` to support **profit-focused optimization** instead of just win-rate optimization. HuggingFace now aligns with your profit goals.

## Changes Made

### 1. ✅ Added Profit Factor Support

**File:** `ml_param_optimizer.py`

**New Initialization:**
```python
# Old (win-rate only):
MLParameterOptimizer(target_win_rate=0.70)

# New (profit-focused):
MLParameterOptimizer(target_metric='profit_factor', target_value=1.5)

# Still supports win-rate:
MLParameterOptimizer(target_metric='win_rate', target_value=0.70)
```

**Backward Compatible:**
- Old code using `target_win_rate` still works
- Automatically converts to new format

### 2. ✅ Updated Analysis to Include Profit Factor

**File:** `ml_param_optimizer.py` → `_analyze_backtest_results()`

**Added:**
- Calculates `avg_profit_factor` from backtest results
- Extracts profit_factor from trades if available
- Includes `profit_factor_std` for variance tracking

### 3. ✅ Profit-Focused Optimization Prompt

**File:** `ml_param_optimizer.py` → `_build_optimization_prompt()`

**New Prompt Focus:**
- Explains profit factor concept (PF = Gross Profit / Gross Loss)
- Emphasizes: "3 big wins (10-15%) + 7 small losses > 10 wins of 1% each"
- Suggests higher take profit targets (10-15%) for bigger wins
- Focuses on risk/reward ratio (2:1 or better)
- Prioritizes profit maximization over win rate

**Example Prompt Excerpt:**
```
Key Insight: A strategy with 3 big wins (10-15% each) and 7 small losses 
(3-5% each) can have PF > 2.0 even with only 30% win rate. This is better 
than 10 wins of 1% each (PF ≈ 1.0, 100% win rate but low profit).

Focus on:
1. Increasing take profit targets (10-15%) to capture bigger wins
2. Tightening stop losses (3-5%) to limit losses
3. Optimizing risk/reward ratio (aim for 2:1 or better)
```

### 4. ✅ Updated Return Values

**File:** `ml_param_optimizer.py` → `optimize_parameters()`

**Changed:**
- Returns `predicted_profit_factor` when `target_metric='profit_factor'`
- Falls back to `predicted_win_rate` if profit_factor not provided
- Logs appropriate metric based on target

### 5. ✅ Updated Result Saving

**File:** `ml_param_optimizer.py` → `save_optimization_result()`

**Enhanced:**
- Saves `target_metric` and `target_value`
- Saves `predicted_profit_factor` when applicable
- Maintains backward compatibility with `target_win_rate`

### 6. ✅ Updated Main Bot Integration

**File:** `main.py` → `TradingBot.__init__()` and `optimize_parameters_ml()`

**Changes:**
- Properly initializes with `target_metric='profit_factor'` when configured
- Logs profit factor instead of win rate when profit-focused
- Handles both metrics in optimization results

## Configuration

### Enable Profit-Focused Optimization

**In `.env`:**
```bash
# ML Optimization (profit-focused)
ENABLE_REALTIME_ML_OPTIMIZATION=true
ML_OPTIMIZATION_TARGET=profit_factor  # Change from win_rate
ML_OPTIMIZATION_TARGET_VALUE=1.5     # PF > 1.5 means profitable
```

### Keep Win-Rate Optimization (Default)

**In `.env`:**
```bash
# ML Optimization (win-rate focused)
ENABLE_REALTIME_ML_OPTIMIZATION=true
ML_OPTIMIZATION_TARGET=win_rate       # Default
ML_OPTIMIZATION_TARGET_VALUE=0.70     # 70% win rate
```

## How It Works

### Profit-Focused Mode:

1. **Analyzes Performance:**
   - Calculates current profit factor
   - Tracks gross profit vs gross loss
   - Measures risk/reward ratios

2. **Suggests Parameters:**
   - Higher take profit targets (10-15% instead of 5-10%)
   - Tighter stop losses (3-5% to limit losses)
   - Optimized risk/reward (2:1 or better)
   - Focus on profit per trade, not win rate

3. **Example Suggestions:**
   - "Increase BOT_TAKE_PROFIT_PERCENT to 0.12 (12%) to capture bigger wins"
   - "Tighten BOT_STOP_LOSS_PERCENT to 0.04 (4%) to limit losses"
   - "Aim for 2:1 risk/reward ratio"

### Win-Rate Focused Mode (Original):

1. **Analyzes Performance:**
   - Calculates current win rate
   - Tracks consistency
   - Measures drawdown

2. **Suggests Parameters:**
   - Lower take profit targets (5-8% for more wins)
   - Moderate stop losses
   - Focus on win rate consistency

## Expected Behavior

### Before (Win-Rate Focused):
- HuggingFace suggests: "Take profits at 5% to get 70% win rate"
- Result: Many small wins, low total profit
- Conflict: Fights with dynamic exit targets (10-15%)

### After (Profit-Focused):
- HuggingFace suggests: "Take profits at 12-15% for bigger wins"
- Result: Fewer but bigger wins, higher total profit
- Alignment: Works with dynamic exit targets

## Integration with Dynamic Exits

**Synergy:**
- **HuggingFace:** Suggests parameter ranges (e.g., "use 10-15% take profit")
- **Dynamic Exits:** Adjusts within those ranges based on context (monthly target, T+1, momentum)
- **Result:** Both systems work together for maximum profit

**Example:**
1. HuggingFace suggests: "BOT_TAKE_PROFIT_PERCENT = 0.12 (12%)"
2. Dynamic exit sees: Behind monthly target, capital tied up
3. Dynamic exit adjusts: Uses 15% target for this trade
4. Both aligned: Maximize profit, not just win rate

## Testing

**Syntax Check:** ✅ Passed
**Backward Compatibility:** ✅ Maintained
**Integration:** ✅ Complete

## Next Steps

1. **Test in Paper Trading:**
   - Set `ML_OPTIMIZATION_TARGET=profit_factor`
   - Run for 20+ trades
   - Check if suggestions focus on profit, not win rate

2. **Monitor Suggestions:**
   - Watch for higher take profit targets (10-15%)
   - Verify focus on risk/reward ratios
   - Confirm profit factor improvements

3. **Compare Results:**
   - Run with `profit_factor` target
   - Run with `win_rate` target
   - Compare total profit and profit factor

## Files Modified

1. `ml_param_optimizer.py` - Core profit-focused implementation
2. `main.py` - Integration with profit-focused mode

## Summary

✅ **HuggingFace now optimizes for profit, not just win rate**
✅ **Aligned with your profit-focused goals**
✅ **Works synergistically with dynamic exit targets**
✅ **Backward compatible with existing win-rate optimization**

The bot is now fully profit-focused from top to bottom! 🎯
