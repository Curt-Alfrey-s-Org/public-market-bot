# Backend-GUI Integration Guide

## Overview

This document describes the complete integration between the FastAPI backend and React frontend for controlling the trading bot.

## Architecture

### Components

1. **API Backend (`api/`)**
   - `api/main.py` - FastAPI application
   - `api/bot_manager.py` - Bot lifecycle management
   - `api/routes/bot.py` - Bot control endpoints
   - `api/utils.py` - Bot instance management

2. **Frontend (`frontend/`)**
   - `frontend/src/components/BotControls.tsx` - Bot control UI
   - `frontend/src/api/bot.ts` - API client functions
   - `frontend/src/api/client.ts` - Axios client with timeouts

3. **Trading Bot (`main.py`)**
   - `TradingBot` class - Core trading logic
   - Runs in continuous mode when started via API

## Bot Control Flow

### Starting the Bot

1. **Frontend:** User clicks "Start" button
2. **API:** `POST /api/bot/start` endpoint called
3. **Bot Manager:** `start_bot()` function:
   - Initializes `TradingBot` instance
   - Sets `bot.running = True`
   - Starts bot loop in background thread
   - Returns success response
4. **Frontend:** Updates UI to show "Running" status

### Stopping the Bot

1. **Frontend:** User clicks "Stop" button
2. **API:** `POST /api/bot/stop` endpoint called
3. **Bot Manager:** `stop_bot()` function:
   - Sets `bot.running = False`
   - Sets stop event to signal loop to exit
   - Bot loop exits gracefully
   - Bot instance remains alive
4. **Frontend:** Updates UI to show "Stopped" status

### Shutting Down the Bot

1. **Frontend:** User clicks "Shutdown" button (with confirmation)
2. **API:** `POST /api/bot/shutdown` endpoint called
3. **Bot Manager:** `shutdown_bot()` function:
   - Calls `stop_bot()` first
   - Waits for thread to finish
   - Cleans up bot instance
   - Returns success response
4. **Frontend:** Updates UI to show "Stopped" status

## API Endpoints

### `GET /api/bot/status`
Returns bot status:
```json
{
  "running": true,
  "mode": "yfinance"
}
```

### `POST /api/bot/start`
Starts the bot:
```json
{
  "message": "Bot started successfully",
  "status": "started",
  "running": true
}
```

### `POST /api/bot/stop`
Stops the bot (pauses trading):
```json
{
  "message": "Bot stopped successfully",
  "status": "stopped",
  "running": false
}
```

### `POST /api/bot/shutdown`
Shuts down the bot completely:
```json
{
  "message": "Bot shutdown complete",
  "status": "shutdown",
  "running": false
}
```

### `POST /api/bot/mode`
Sets bot trading mode:
```json
{
  "mode": "yfinance",
  "message": "Mode changed to yfinance",
  "status": "success",
  "bot_available": true
}
```

## Bot Manager Functions

### `initialize_bot_from_main()`
- Creates `TradingBot` instance
- Sets bot instance in API utils
- Returns bot instance

### `start_bot()`
- Initializes bot if needed
- Sets `bot.running = True`
- Starts background thread with `_run_bot_loop()`
- Returns success boolean

### `stop_bot()`
- Sets `bot.running = False`
- Sets stop event
- Returns success boolean

### `shutdown_bot()`
- Stops bot first
- Waits for thread to finish
- Cleans up bot instance
- Returns success boolean

### `is_bot_running()`
- Returns boolean indicating if bot is running

### `get_bot_status()`
- Returns comprehensive status dict

## Frontend Integration

### BotControls Component

Shows:
- Current mode
- Running/Stopped status indicator
- Start/Stop/Shutdown buttons

Features:
- Auto-refreshes status every 2 seconds
- Disables buttons during operations
- Shows loading states
- Confirmation dialog for shutdown

### API Client

- 5-second timeout on all requests
- Proper error handling for 503 (bot not available)
- Network error detection
- Automatic retry logic

## Continuous Trading Mode

The bot runs in continuous mode when started:
1. Loads symbols once at startup
2. Runs trading cycles indefinitely
3. Processes each symbol in priority order
4. Waits between trades (TRADING_FREQUENCY)
5. Starts next cycle after completing all symbols
6. Can be stopped/shutdown at any time

## State Management

### Bot Instance
- Stored in `api.utils.bot_instance`
- Set via `set_bot_instance()`
- Retrieved via `get_bot_instance()`

### Running State
- `bot.running` - Bot instance running flag
- `_bot_running` - Manager running flag
- `_bot_stop_event` - Threading event for graceful shutdown

## Error Handling

### Bot Not Available (503)
- When bot instance is None
- Endpoints return 503 or default values
- Frontend shows appropriate messages

### Connection Errors
- Frontend detects network errors
- Shows "Cannot connect to API" message
- Provides instructions to start API

### Bot Errors
- Logged to `/tmp/market-bot-api.log`
- Frontend shows error messages
- Bot can be restarted via API

## Testing

### Manual Testing

1. **Start Bot:**
   ```bash
   curl -X POST http://localhost:8000/api/bot/start
   ```

2. **Check Status:**
   ```bash
   curl http://localhost:8000/api/bot/status
   ```

3. **Stop Bot:**
   ```bash
   curl -X POST http://localhost:8000/api/bot/stop
   ```

4. **Shutdown Bot:**
   ```bash
   curl -X POST http://localhost:8000/api/bot/shutdown
   ```

### Integration Tests

Run the test suite:
```bash
python3 test_api_integration.py
```

## Troubleshooting

### Bot Won't Start
- Check API logs: `tail -f /tmp/market-bot-api.log`
- Verify bot can be imported: `python3 -c "from main import TradingBot"`
- Check for errors in bot initialization

### Bot Won't Stop
- Check if thread is alive: `ps aux | grep TradingBotThread`
- Force stop: Restart API server
- Check stop event is being set

### Status Not Updating
- Check API is running: `curl http://localhost:8000/api/health`
- Check bot instance is set: Look for "Bot instance initialized" in logs
- Verify frontend is polling: Check browser network tab

## Future Improvements

1. **WebSocket Updates:** Real-time status updates via WebSocket
2. **Graceful Shutdown:** Better handling of in-flight trades
3. **State Persistence:** Save bot state to database
4. **Multiple Instances:** Support for multiple bot instances
5. **Health Monitoring:** Better health checks and recovery

---

**Status:** ✅ **INTEGRATION COMPLETE** - Bot can be fully controlled from web GUI
