# Copilot Debug Logging

## Overview

The Copilot Debug Logger provides detailed execution traces to help GitHub Copilot analyze bot behavior between runs. This feature captures key decision points, state changes, and performance metrics in structured JSONL (JSON Lines) format for easy parsing and analysis.

## Features

- **Session-based logging**: Each bot run creates a unique session with timestamped log file
- **Structured JSON output**: Easy to parse and analyze programmatically
- **Minimal performance impact**: Only logs when explicitly enabled via environment variable
- **Comprehensive event tracking**: Captures initialization, decisions, trades, errors, and state snapshots

## Configuration

### Enable Debug Logging

Add to your `.env` file:

```bash
COPILOT_DEBUG_MODE=true
```

To disable (default):

```bash
COPILOT_DEBUG_MODE=false
```

## Log File Location

Debug logs are stored in the `logs/` directory with the naming pattern:

```
logs/copilot_debug_YYYYMMDD_HHMMSS.jsonl
```

Example: `logs/copilot_debug_20260122_051105.jsonl`

## Log File Format

Each log file is in JSONL format (one JSON object per line). Each entry has:

- `event_type`: Type of event (session_start, bot_initialization, decision, etc.)
- `session_id`: Unique session identifier
- `timestamp`: ISO 8601 timestamp
- `event_id`: Sequential event counter within the session
- Additional fields specific to event type

### Event Types

#### 1. session_start
Logged when the bot starts:

```json
{
  "event_type": "session_start",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.277648",
  "event_id": 1,
  "environment": {
    "python_version": "3.12.3",
    "cwd": "/home/runner/work/market-pie5-bot/market-pie5-bot"
  }
}
```

#### 2. bot_initialization
Logged when TradingBot is initialized:

```json
{
  "event_type": "bot_initialization",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.277834",
  "event_id": 2,
  "config": {
    "total_capital": 10000.0,
    "starting_capital": 10000.0,
    "capital_floor": 1000.0,
    "risk_threshold": 0.02,
    "trailing_stop_percent": 0.03,
    "paper_trading_mode": true,
    "sandbox_mode": true,
    "api_enabled": "on"
  }
}
```

#### 3. decision
Logged when bot makes a decision:

```json
{
  "event_type": "decision",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.277924",
  "event_id": 3,
  "decision_type": "trade_signal",
  "context": {
    "symbol": "AAPL",
    "price": 150.0,
    "indicators": {"rsi": 65, "macd": 0.5}
  },
  "result": "BUY",
  "rationale": "RSI indicates oversold, MACD shows bullish momentum"
}
```

#### 4. trade_execution
Logged when a trade is executed:

```json
{
  "event_type": "trade_execution",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278013",
  "event_id": 4,
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10.0,
  "price": 150.25,
  "metadata": {
    "strategy": "momentum",
    "confidence": 0.85,
    "mode": "simulation"
  }
}
```

#### 5. strategy_selection
Logged when bot selects a trading strategy:

```json
{
  "event_type": "strategy_selection",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278100",
  "event_id": 5,
  "symbol": "AAPL",
  "strategies_evaluated": ["momentum", "mean_reversion", "breakout"],
  "selected_strategy": "momentum",
  "scores": {
    "momentum": 0.85,
    "mean_reversion": 0.65,
    "breakout": 0.70
  },
  "rationale": "Momentum strategy has highest confidence score"
}
```

#### 6. error
Logged when an error occurs:

```json
{
  "event_type": "error",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278200",
  "event_id": 6,
  "error_type": "API_ERROR",
  "error_message": "Failed to fetch price for AAPL",
  "context": {
    "symbol": "AAPL",
    "api": "yfinance"
  },
  "stack_trace": "Traceback..."
}
```

#### 7. state_snapshot
Logged to capture bot state at key moments:

```json
{
  "event_type": "state_snapshot",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278300",
  "event_id": 7,
  "state_type": "positions",
  "state_data": {
    "AAPL": {
      "quantity": 10,
      "entry_price": 150.0,
      "current_price": 152.0
    },
    "total_capital": 9850.0
  }
}
```

#### 8. performance_metric
Logged to track performance metrics:

```json
{
  "event_type": "performance_metric",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278400",
  "event_id": 8,
  "metric_name": "win_rate",
  "metric_value": 0.65,
  "context": {
    "total_trades": 20,
    "winning_trades": 13
  }
}
```

#### 9. api_call
Logged for external API calls:

```json
{
  "event_type": "api_call",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278500",
  "event_id": 9,
  "api_name": "schwab",
  "method": "get_quotes",
  "success": true,
  "duration_ms": 125.5,
  "response_summary": {
    "symbols": 5,
    "cached": 2
  }
}
```

#### 10. session_end
Logged when bot execution completes:

```json
{
  "event_type": "session_end",
  "session_id": "20260122_051105",
  "timestamp": "2026-01-22T05:11:05.278600",
  "event_id": 10,
  "summary": {
    "total_trades": 10,
    "winning_trades": 7,
    "losing_trades": 3,
    "win_rate": 0.70,
    "starting_capital": 10000.0,
    "final_capital": 10500.0,
    "total_pnl": 500.0,
    "total_pnl_percent": 5.0
  }
}
```

## Analyzing Logs

### Command Line Tools

**View entire log file:**
```bash
cat logs/copilot_debug_20260122_051105.jsonl
```

**Pretty print with jq:**
```bash
cat logs/copilot_debug_20260122_051105.jsonl | jq '.'
```

**Filter specific event types:**
```bash
# Show only trade executions
cat logs/copilot_debug_*.jsonl | jq 'select(.event_type == "trade_execution")'

# Show only errors
cat logs/copilot_debug_*.jsonl | jq 'select(.event_type == "error")'

# Show session summaries
cat logs/copilot_debug_*.jsonl | jq 'select(.event_type == "session_end")'
```

**Count events by type:**
```bash
cat logs/copilot_debug_*.jsonl | jq -r '.event_type' | sort | uniq -c
```

### Python Analysis

```python
import json
from pathlib import Path

# Load all events from a log file
log_file = Path("logs/copilot_debug_20260122_051105.jsonl")
events = []

with open(log_file, 'r') as f:
    for line in f:
        events.append(json.loads(line))

# Analyze trades
trades = [e for e in events if e['event_type'] == 'trade_execution']
print(f"Total trades: {len(trades)}")

# Analyze decisions
decisions = [e for e in events if e['event_type'] == 'decision']
for d in decisions:
    print(f"Decision: {d['decision_type']} -> {d['result']}")

# Get session summary
session_end_events = [e for e in events if e['event_type'] == 'session_end']
if session_end_events:
    session_end = session_end_events[0]
    print(f"Win rate: {session_end['summary']['win_rate']:.1%}")
else:
    print("No session_end event found; win rate summary is unavailable.")
```

## Use Cases

### For GitHub Copilot

When working with GitHub Copilot on this repository, enable debug logging to help it understand:

1. **Why trades were made**: Decision context and rationale
2. **How strategies performed**: Strategy selection and scores
3. **What errors occurred**: Error types and contexts
4. **Bot state over time**: State snapshots at key moments
5. **Performance metrics**: Win rates, P&L, and other KPIs

### For Developers

Debug logs are useful for:

- **Debugging issues**: Trace exact sequence of events leading to errors
- **Performance analysis**: Identify bottlenecks via API call durations
- **Strategy evaluation**: Compare strategy selection across sessions
- **Backtesting validation**: Verify bot behavior matches expectations
- **Parameter tuning**: See impact of configuration changes

## Performance Considerations

- **Minimal overhead**: Logging uses synchronous writes with minimal performance impact
- **Controlled by environment**: Disabled by default, no logs created when off
- **Automatic session management**: One file per session, easy to manage
- **No retention policy**: Old logs are not automatically deleted

## Best Practices

1. **Enable only when needed**: Keep `COPILOT_DEBUG_MODE=false` in production
2. **Review logs regularly**: Check for errors and unexpected patterns
3. **Clean old logs**: Periodically delete old debug logs to save space
4. **Use with Copilot**: Enable when asking Copilot to analyze bot behavior
5. **Combine with other logs**: Cross-reference with `trading_bot.log` for full picture

## Troubleshooting

**Debug logs not created:**
- Check that `COPILOT_DEBUG_MODE=true` in `.env`
- Verify `logs/` directory exists and is writable
- Check for import errors in bot startup logs

**Large log files:**
- Debug logs can grow large for long-running sessions
- Consider disabling if not actively analyzing
- Use log rotation for continuous operation

**Missing events:**
- Some events only logged in specific code paths
- Enable `WEB_GUI_DEBUG=true` for additional web GUI events
- Check that feature is enabled (e.g., ML optimizer for strategy selection)

## Related Files

- `copilot_debug_logger.py` - Debug logger implementation
- `test_copilot_debug_logger.py` - Test suite
- `log_manager.py` - General purpose logging for trades and backtests
- `main.py` - TradingBot integration

## See Also

- [Log Manager Documentation](./log_manager.py)
- [User Guide](./USER_GUIDE.md)
- [Troubleshooting Guide](./README.md#troubleshooting)
