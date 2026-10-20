# Manual Trade Approval Mode - Implementation Summary

## Overview
Manual Trade Approval Mode allows users to review and approve/reject trades before execution. This feature helps users:
- Learn how the bot makes trading decisions
- Build trust before going fully automatic
- See exactly what the bot would do in auto mode vs manual mode
- Review comprehensive trade reasoning before committing capital

## Configuration

### Environment Variable
Add to `.env`:
```bash
MANUAL_TRADE_APPROVAL_MODE=true
```

When enabled:
- Bot identifies trades and creates pending trade requests instead of executing immediately
- Shows full trade details, reasoning, and auto-mode decision
- User approves/rejects each trade via GUI
- Trades only execute after approval

## Backend Implementation

### Core Methods Added to TradingBot

1. **`get_capital_schedule()`** - Returns capital availability schedule (T+1 settlements)
2. **`get_current_month_return_pct()`** - Calculates current month's return percentage
3. **`get_days_remaining_in_month()`** - Days remaining in current month
4. **`calculate_dynamic_exit_target()`** - Dynamic profit target based on context
5. **`collect_trade_reasoning()`** - Comprehensive trade reasoning collection
6. **`create_pending_trade()`** - Creates pending trade request
7. **`approve_pending_trade()`** - Approves and executes pending trade
8. **`reject_pending_trade()`** - Rejects pending trade
9. **`get_pending_trades()`** - Returns all pending trades

### Trade Reasoning Includes:
- **Strategy Signals**: Combined and individual strategy signals with confidence
- **ML Filter Results**: ML confidence and win probability
- **Portfolio Optimization**: Optimal allocation recommendations
- **Risk Analysis**: Potential loss, risk limits, risk assessment
- **Market Conditions**: Volatility, volume, liquidity assessment
- **Capital Status**: Available capital, settlement schedule
- **Monthly Progress**: Current return vs target, days remaining
- **Auto Mode Decision**: What bot would do in auto mode (EXECUTE/REJECT) with reasons

### Modified Methods

**`execute_trade()`** - Now checks `MANUAL_TRADE_APPROVAL_MODE`:
- If enabled: Creates pending trade instead of executing
- Returns `{'status': 'pending_approval', 'trade_id': ...}`
- If disabled: Executes normally

## API Endpoints

### GET `/api/pending-trades`
Returns all pending trades awaiting approval.

**Response:**
```json
{
  "pending_trades": [
    {
      "trade_id": "pending_1_20250127_153045",
      "symbol": "AAPL",
      "action": "BUY",
      "price": 150.25,
      "quantity": 66.44,
      "allocation": 10000.0,
      "reasoning": { ... },
      "auto_mode_details": {
        "would_execute": true,
        "decision": "EXECUTE",
        "reasons": ["All checks passed - would execute"]
      },
      "timestamp": "2025-01-27T15:30:45",
      "expires_at": "2025-01-27T15:35:45",
      "status": "pending"
    }
  ],
  "total": 1
}
```

### POST `/api/pending-trades/approve`
Approves a pending trade and executes it.

**Request:**
```json
{
  "trade_id": "pending_1_20250127_153045"
}
```

**Response:**
```json
{
  "status": "success",
  "order_id": "...",
  "approved_by": "user",
  "pending_trade_id": "pending_1_20250127_153045"
}
```

### POST `/api/pending-trades/reject`
Rejects a pending trade.

**Request:**
```json
{
  "trade_id": "pending_1_20250127_153045",
  "reason": "Optional rejection reason"
}
```

**Response:**
```json
{
  "status": "rejected",
  "trade_id": "pending_1_20250127_153045",
  "message": "Trade rejected by user"
}
```

## Pending Trade Lifecycle

1. **Created**: Bot identifies trade → `create_pending_trade()` → Status: `pending`
2. **Expires**: After 5 minutes (300 seconds) → Status: `expired` (auto-removed)
3. **Approved**: User approves → `approve_pending_trade()` → Trade executes → Removed from pending
4. **Rejected**: User rejects → `reject_pending_trade()` → Removed from pending

## Frontend Integration (TODO)

The frontend component should:
1. Poll `/api/pending-trades` to get pending trades
2. Display trade details with reasoning breakdown
3. Show auto-mode decision and comparison
4. Provide approve/reject buttons
5. Show expiration countdown
6. Display alerts when new pending trades are created

## Usage Example

1. Set `MANUAL_TRADE_APPROVAL_MODE=true` in `.env`
2. Start bot - it will create pending trades instead of executing
3. View pending trades in GUI
4. Review reasoning and auto-mode decision
5. Approve or reject each trade
6. Approved trades execute immediately
7. Rejected trades are logged and removed

## Benefits

- **Transparency**: See exactly why bot wants to make each trade
- **Control**: Final decision remains with user
- **Learning**: Understand bot's decision-making process
- **Safety**: Review before committing capital
- **Trust Building**: Gradual transition from manual to automatic
