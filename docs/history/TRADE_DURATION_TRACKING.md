# Trade Duration Tracking & Stale Position Detection

## Overview

Enhanced trade recording system to track **trade duration** and detect **stale positions** (trades held open for too long without closure).

**Key Changes:**
- ✅ Added `entry_time` and `exit_time` fields to all trade records
- ✅ Added stale position detection (>48 hours)
- ✅ Added logging for extended holds (>24 hours)
- ✅ New method: `detect_stale_positions()` for API querying

## What Gets Tracked

### Entry Trades (BUY / SHORT)
```python
trade_record = {
    'timestamp': '2026-02-01T21:31:00.123456',
    'symbol': 'AAPL',
    'action': 'BUY',
    'entry_price': 150.25,
    'entry_time': '2026-02-01T21:31:00.123456',  # ← NEW
    'quantity': 10,
    'price': 150.25,
    'mode': 'pure_simulation'
}
```

### Exit Trades (SELL / COVER)
```python
trade_record = {
    'timestamp': '2026-02-01T23:45:00.123456',
    'symbol': 'AAPL',
    'action': 'SELL',
    'entry_price': 150.25,
    'entry_time': '2026-02-01T21:31:00.123456',  # ← For reference
    'exit_time': '2026-02-01T23:45:00.123456',    # ← NEW
    'exit_price': 151.50,
    'pnl': 12.50,
    'pnl_percent': 0.83,
    'hold_duration_hours': 2.23,                # ← Enhanced tracking
    'is_win': True,
    'mode': 'pure_simulation'
}
```

## Automatic Logging

### Extended Hold Detection
Positions held **>24 hours** log at INFO level:
```
2026-02-01 14:30:00 - __main__ - INFO - [EXTENDED_HOLD] TSLA: held for 30.5 hours
```

### Stale Position Warning
Positions held **>48 hours** log at WARNING level:
```
2026-02-01 14:30:00 - __main__ - WARNING - [STALE_POSITION] MSFT: held for 72.3 hours (>48h threshold)
```

## New API Method

### `detect_stale_positions(stale_threshold_hours=48.0)`

Identify all currently open positions held beyond threshold:

```python
# In bot or via API
stale = bot.detect_stale_positions(stale_threshold_hours=48.0)

# Returns:
{
    'MSFT': {
        'hold_duration_hours': 72.5,
        'entry_price': 425.30,
        'entry_time': '2026-01-30T14:20:00.123456',
        'current_price': 428.75,
        'current_pnl_percent': 0.81,
        'side': 'long',
        'quantity': 5
    },
    'GOOGL': {
        'hold_duration_hours': 60.2,
        'entry_price': 180.50,
        'entry_time': '2026-01-31T08:15:00.123456',
        'current_price': 179.20,
        'current_pnl_percent': -0.72,
        'side': 'long',
        'quantity': 8
    }
}
```

## Benefits

| Benefit | Impact |
|---------|--------|
| **Capital Efficiency** | Identify positions that aren't moving/generating returns; free up capital for better opportunities |
| **Risk Management** | Detect positions held past intended exit windows; close stale trades before loss amplifies |
| **Trend Detection** | Distinguish healthy holds from mean-reversion/choppy positions |
| **Trade Analytics** | Measure hold times vs. P&L to identify optimal holding periods |
| **Automated Cleanup** | Flag positions for manual review or automatic closure at end-of-day |

## Implementation Details

### Trade Record Enhancement
- **`entry_time`**: Set when BUY/SHORT executed (defaults to `datetime.now()` if not provided)
- **`exit_time`**: Set when SELL/COVER executed (defaults to `datetime.now()`)
- **`hold_duration_hours`**: Calculated as `(exit_time - entry_time) / 3600`

### Thresholds
- **Extended Hold**: >24 hours → INFO log
- **Stale Position**: >48 hours → WARNING log + flagged for review

### Database Persistence
Trade records are persisted to SQLite (`logs/trading_logs.db`) via `LogManager` with full duration metadata.

## Usage Examples

### Check for Stale Positions
```python
# In TradingBot monitoring loop
stale_positions = self.detect_stale_positions(stale_threshold_hours=48.0)
if stale_positions:
    for symbol, data in stale_positions.items():
        print(f"{symbol}: held {data['hold_duration_hours']:.1f}h, "
              f"P&L: {data['current_pnl_percent']:.2f}%")
```

### Monitor Hold Duration Distribution
```python
# Analyze average hold times from trade history
total_hold_hours = sum(
    trade.get('hold_duration_hours', 0) 
    for trade in bot.trade_history 
    if trade['action'] in ('SELL', 'COVER')
)
avg_hold = total_hold_hours / len([t for t in bot.trade_history if t['action'] in ('SELL', 'COVER')])
print(f"Average hold time: {avg_hold:.1f} hours")
```

### Set Custom Threshold
```python
# Alert on positions >12 hours old (day traders)
half_day_stale = bot.detect_stale_positions(stale_threshold_hours=12.0)
```

## Log Output Examples

### New Trade Entry
```
2026-02-01 15:30:45,123 - __main__ - DEBUG - [TRADE_RECORDED] BUY AAPL: entry_price=150.25, entry_time=2026-02-01T15:30:45.123Z
```

### Trade Closure (Quick)
```
2026-02-01 15:45:30,456 - __main__ - DEBUG - [TRADE_RECORDED] SELL AAPL: exit_time=2026-02-01T15:45:30.456Z
```

### Extended Hold Alert
```
2026-02-01 22:15:00,000 - __main__ - INFO - [EXTENDED_HOLD] TSLA: held for 24.5 hours
```

### Stale Position Alert
```
2026-02-01 14:30:00,000 - __main__ - WARNING - [STALE_POSITION] MSFT: held for 72.3 hours (>48h threshold) (side=long, pnl=2.50%, entry=$425.30, current=$436.00)
```

## Database Schema

Trade records stored with extended fields:

```sql
-- logs/trading_logs.db schema
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    symbol TEXT,
    action TEXT,
    quantity REAL,
    price REAL,
    entry_price REAL,
    exit_price REAL,
    entry_time TEXT,        -- ← NEW: ISO format timestamp
    exit_time TEXT,         -- ← NEW: ISO format timestamp  
    pnl REAL,
    pnl_percent REAL,
    is_win INTEGER,
    mode TEXT,
    hold_duration_hours REAL,  -- ← Enhanced
    exit_reason TEXT,
    volatility REAL,
    volume INTEGER,
    metadata TEXT
);
```

## Deployment Status

✅ **Deployed to operator (2026-02-01 21:48)**
- Updated: `main.py` (388 KB)
- Changes: 
  - Enhanced `record_trade()` method (+18 parameters tracking)
  - New `detect_stale_positions()` method (+60 lines)
  - Stale detection logging integrated into close operations

✅ **Syntax Verified**: No compilation errors

## Next Steps

1. **Monitor Bot Output**: Watch logs for `[EXTENDED_HOLD]` and `[STALE_POSITION]` messages
2. **API Integration**: Add `/api/stale-positions` endpoint to query stale trades
3. **Automated Actions**: Add end-of-day cleanup to auto-close stale positions if desired
4. **Analytics Dashboard**: Track hold time distribution and correlate with win rate

## References

- Trade recording: `main.py:record_trade()` (lines ~2940-3030)
- Stale detection: `main.py:detect_stale_positions()` (lines ~5601-5655)
- Position closure: `main.py:close_position()` (lines ~5449-5500)
- Phase 1 integration: Deployed with earnings awareness and sector diversification
