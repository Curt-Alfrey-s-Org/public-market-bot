# Short Selling Guide for market-pie5-bot

## Overview

**Short selling** is now fully supported in market-pie5-bot (Phase 1 - MISSION.md requirement). The bot can open short positions (profit when prices fall) and manage both long and short positions simultaneously in a mixed portfolio.

## What is Short Selling?

Short selling is betting that a stock's price will decrease:

1. **SHORT (Open Short)**: Borrow and sell shares you don't own at current price
2. **Price drops**: Stock falls from $100 → $90 
3. **COVER (Close Short)**: Buy back shares at lower price to return them
4. **Profit**: Keep the difference ($100 - $90 = $10 profit per share)

**Risk Warning**: Unlike long positions (max loss = 100%), short positions have **unlimited loss potential** if the price rises significantly. The bot enforces strict risk management to mitigate this.

## How It Works in the Bot

### Intelligent Signal Conversion

The bot uses an elegant design where **strategies only return BUY/SELL/HOLD**, and the `_signal_to_action()` method automatically converts them to the appropriate action based on current positions:

```python
# Signal Conversion Logic (_signal_to_action in main.py line 7012):

BUY signal + no position       →  BUY (open long)
BUY signal + short position    →  COVER (close short, take profit)
BUY signal + long position     →  Skip (already long)

SELL signal + long position    →  SELL (close long)
SELL signal + no position      →  SHORT (open short, bet on decline)
SELL signal + short position   →  Skip (already short)

HOLD signal                    →  Skip (no action)
```

**Why This Design?**
- Strategies don't need to know about position state
- Bot automatically does the right thing based on context
- Short positions close naturally when bearish signal reverses to bullish
- Simple strategy logic, smart execution layer

### Example Workflow

1. **Strategy generates SELL signal** (bearish, expects price to drop)
2. **Bot has no position** in this stock
3. **_signal_to_action() returns 'SHORT'** (open short position)
4. **execute_trade_paper_mode('AAPL', 'SHORT', 150.0)** executes
5. **Position opened** with `side='short'`, entry_price=$150
6. **Price drops to $140** (profit accumulating)
7. **Strategy generates BUY signal** (bullish reversal)
8. **_signal_to_action() returns 'COVER'** (close profitable short)
9. **execute_trade_paper_mode('AAPL', 'COVER', 140.0)** executes
10. **P&L calculated**: ($150 - $140) × quantity = **+$10/share profit** ✓

## Configuration

### Environment Variables (.env)

```bash
# Paper Trading Mode (required for shorts in paper)
PAPER_TRADING_MODE=true

# Enable shorts in paper trading
ALLOW_SHORTS_IN_PAPER=true

# Enable shorts in live trading (use with extreme caution!)
SCHWAB_SHORT_SELLING_ENABLED=true

# Maximum number of simultaneous short positions
MAX_SHORT_POSITIONS=5

# Maximum short exposure as % of total capital (default: 25%)
MAX_SHORT_EXPOSURE_PCT=0.25
```

### Risk Management Settings

Short-specific limits are enforced by `can_open_short()` (line 3725 in main.py):

1. **Mode Check**:
   - Paper: `ALLOW_SHORTS_IN_PAPER` must be `true`
   - Live: `SCHWAB_SHORT_SELLING_ENABLED` must be `true`

2. **Position Limit**:
   - Max `MAX_SHORT_POSITIONS` shorts open simultaneously
   - Example: `MAX_SHORT_POSITIONS=5` → reject 6th short

3. **Exposure Limit**:
   - Total short value ≤ `MAX_SHORT_EXPOSURE_PCT` × capital
   - Example: $10,000 capital × 25% = $2,500 max short exposure
   - Prevents over-concentration in short bets

## Position Tracking

### Position Structure

Positions now include a `side` field:

```python
self.positions['AAPL'] = {
    'entry_price': 150.0,
    'quantity': 10.0,
    'side': 'short',        # 'long' or 'short'
    'high_price': None,     # Not tracked for shorts
    'low_price': 150.0,     # Tracks lowest price (for trailing stop)
    'stop_percent': 0.03,
    'entry_time': '2026-02-02T10:30:00',
    # ... other fields
}
```

### Long vs Short Tracking

| Field | Long Position | Short Position |
|-------|---------------|----------------|
| `side` | `'long'` | `'short'` |
| `high_price` | Tracked (for trailing stop up) | `None` |
| `low_price` | `None` | Tracked (for trailing stop down) |
| P&L Formula | `(exit - entry) × qty` | `(entry - exit) × qty` |

## P&L Calculations

### Long Position (Traditional)
```
Entry: $100, Exit: $110, Quantity: 10 shares
P&L = (110 - 100) × 10 = +$100 profit (10%)
```

### Short Position (Inverse)
```
Entry (SHORT): $100, Exit (COVER): $90, Quantity: 10 shares  
P&L = (100 - 90) × 10 = +$100 profit (10%)

Entry (SHORT): $100, Exit (COVER): $110, Quantity: 10 shares
P&L = (100 - 110) × 10 = -$100 loss (10%)
```

Implementation in `close_position()` (line 5748-5791):

```python
def close_position(self, symbol: str, exit_price: float, exit_reason: str = 'unknown'):
    position = self.positions[symbol]
    entry_price = position['entry_price']
    quantity = position['quantity']
    side = position.get('side', 'long')
    
    if side == 'short':
        # Inverse P&L: profit when exit < entry
        pnl = (entry_price - exit_price) * quantity
        pnl_percent = ((entry_price - exit_price) / entry_price) * 100
    else:
        # Normal P&L: profit when exit > entry
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
    
    return {
        'pnl': pnl,
        'pnl_percent': pnl_percent,
        'is_win': pnl > 0,
        'side': side,
        # ... other fields
    }
```

## Trailing Stops for Shorts

Shorts use **inverted trailing stop logic**:

### Long Trailing Stop
- Track `high_price` (highest price since entry)
- Trigger if `current_price < high_price × (1 - stop_percent)`
- Protects profit as price rises

### Short Trailing Stop  
- Track `low_price` (lowest price since entry)
- Trigger if `current_price > low_price × (1 + stop_percent)`
- Protects profit as price falls

Example:
```
SHORT entry: $100 (low_price = $100)
Price drops to $90 (low_price = $90, profit!)
Price rises to $93.60 = $90 × 1.04
Stop triggers (4% > 3% stop) → COVER at $93.60
Realized profit: ($100 - $93.60) × qty
```

## Live Trading Considerations

### Schwab API Integration

The bot maps actions to Schwab API instructions (line 591-595):

```python
SCHWAB_INSTRUCTION_MAP = {
    'BUY': 'BUY',              # Open long or close short
    'SELL': 'SELL',            # Close long
    'SHORT': 'SELL_SHORT',     # Open short (Schwab specific)
    'COVER': 'BUY_TO_COVER',   # Close short (Schwab specific)
}
```

### PDT Rules

Pattern Day Trading rules apply to shorts:
- **SHORT** = opens position (counts as day trade if closed same day)
- **COVER** = closes position (completes day trade)
- Swing trading approach (hold 1+ days) avoids PDT restrictions

### Margin Requirements

Real brokers require margin for shorts:
- Typical: 150% of short value as collateral
- Example: SHORT $10,000 → need $15,000 buying power
- Bot enforces `MAX_SHORT_EXPOSURE_PCT` to stay within limits

## Testing

Comprehensive test suite in `test_short_selling.py`:

```bash
# Run short selling tests
python test_short_selling.py -v

# Test categories:
# 1. TestShortSellingConstants - Validate action lists
# 2. TestPositionSideAndPnL - Long vs short P&L
# 3. TestExecuteTradePaperShortCover - Execution logic
# 4. TestTrailingStopShort - Inverse trailing stops
# 5. TestCanOpenShort - Risk management limits
```

## Best Practices

### DO:
✅ Use shorts for genuinely bearish plays (strong SELL signals)  
✅ Keep `MAX_SHORT_EXPOSURE_PCT` ≤ 30% of capital  
✅ Set tight trailing stops (shorts can move against you fast)  
✅ Test in paper mode first (`ALLOW_SHORTS_IN_PAPER=true`)  
✅ Monitor short exposure in GUI/logs  
✅ Close shorts when BUY signal appears (bot does this automatically)  

### DON'T:
❌ Don't short in live mode until thoroughly tested  
❌ Don't ignore `MAX_SHORT_POSITIONS` limit  
❌ Don't short without stop losses  
❌ Don't short meme stocks (unlimited risk if squeeze)  
❌ Don't keep shorts open through earnings (high volatility)  
❌ Don't short more than 25-30% of portfolio  

## Troubleshooting

### "Short selling disabled in paper mode"
**Solution**: Set `ALLOW_SHORTS_IN_PAPER=true` in .env

### "Maximum short positions (5) reached"
**Solution**: Increase `MAX_SHORT_POSITIONS` or close existing shorts

### "Short exposure would exceed 25% of capital"
**Solution**: Reduce position size or increase `MAX_SHORT_EXPOSURE_PCT`

### "No short position to COVER"
**Cause**: Trying to COVER without existing short  
**Solution**: Check position state with `GET /api/positions`

### Short not opening despite SELL signal
**Possible causes**:
1. Already have short position (signal ignored)
2. Earnings filter blocked it
3. Risk limits exceeded
4. Position limit reached

Check logs for: `[SHORT CHECK FAILED - TRADE SKIPPED]`

## Code Architecture

### Key Files and Functions

**main.py:**
- `_signal_to_action()` (line 7012) - Signal → action conversion
- `execute_trade_paper_mode()` (line 3959) - Paper execution
- `execute_trade_live_mode()` (line 4589) - Live execution  
- `open_position()` (line 5717) - Position tracking with side
- `close_position()` (line 5748) - P&L calculation with side logic
- `can_open_short()` (line 3725) - Short risk checks
- `check_trailing_stop()` (line 5839) - Trailing stop (side-aware)

**Constants (line 591-608):**
- `VALID_ACTIONS = ['BUY', 'SELL', 'SHORT', 'COVER']`
- `ACTIONS_OPEN_POSITION = ('BUY', 'SHORT')`
- `ACTIONS_CLOSE_POSITION = ('SELL', 'COVER')`
- `ALLOW_SHORTS_IN_PAPER` (default: true)
- `SCHWAB_SHORT_SELLING_ENABLED` (default: true)
- `MAX_SHORT_POSITIONS` (default: BOT_MAX_OPEN_POSITIONS)
- `MAX_SHORT_EXPOSURE_PCT` (default: 0.25)

### Execution Flow

```
Strategy.generate_signal('SELL')
    ↓
_signal_to_action('TEST', 'SELL')  # Checks position state
    ↓
Returns 'SHORT' (no long position)
    ↓
execute_trade('TEST', 'SHORT', 100.0)
    ↓
can_open_short() - risk checks
    ↓
execute_trade_paper_mode('SHORT', ...)
    ↓
open_position(..., side='short')
    ↓
Position tracked with side='short'
    ↓
[Price drops to 90.0]
    ↓
Strategy.generate_signal('BUY')  # Reversal
    ↓
_signal_to_action('TEST', 'BUY')  # Has short position
    ↓
Returns 'COVER'
    ↓
execute_trade('TEST', 'COVER', 90.0)
    ↓
close_position('TEST', 90.0)  # Inverse P&L
    ↓
P&L = (100 - 90) × qty = +profit ✓
```

## Advanced: Mixed Long/Short Portfolio

Bot can hold longs and shorts simultaneously:

```python
# Example portfolio state:
positions = {
    'AAPL': {'side': 'long', 'entry_price': 150.0, ...},
    'TSLA': {'side': 'short', 'entry_price': 200.0, ...},
    'MSFT': {'side': 'long', 'entry_price': 350.0, ...},
}

# Portfolio exposure:
Long exposure:  $150 × 10 + $350 × 5 = $3,250
Short exposure: $200 × 8 = $1,600
Net exposure:   $3,250 - $1,600 = $1,650 (net long)
```

This allows hedging strategies and market-neutral approaches.

## Summary

Short selling is **production-ready** in market-pie5-bot:

- ✅ Full execution support (SHORT/COVER actions)
- ✅ Automatic signal conversion (_signal_to_action)
- ✅ Inverse P&L calculations
- ✅ Position side tracking
- ✅ Short-specific risk management
- ✅ Trailing stops (inverted for shorts)
- ✅ Schwab API integration (SELL_SHORT, BUY_TO_COVER)
- ✅ Comprehensive test suite
- ✅ Environment variable configuration

**No code changes required to start using shorts** - just enable in .env:

```bash
ALLOW_SHORTS_IN_PAPER=true
MAX_SHORT_POSITIONS=5
MAX_SHORT_EXPOSURE_PCT=0.25
```

The bot will automatically SHORT on SELL signals when flat and COVER on BUY signals when short!

## References

- **MISSION.md**: Phase 1 goal - "trade stocks (buy + short)"
- **main.py lines 591-608**: Short selling constants
- **main.py line 7012**: _signal_to_action() implementation
- **main.py line 3725**: can_open_short() risk checks
- **main.py line 5748**: close_position() with inverse P&L
- **test_short_selling.py**: 20+ test cases validating functionality
- **.env.example lines 255-261**: Configuration documentation

---

**Disclaimer**: Short selling involves significant risk. Losses can exceed 100% of the initial investment. Only use in paper mode until you fully understand the risks. Not financial advice.
