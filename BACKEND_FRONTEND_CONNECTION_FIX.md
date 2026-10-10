# Backend-Frontend Connection Issues - Fix Guide

## Problem Summary

The bot has been running but the frontend shows no activity. This indicates a disconnect between:
1. **Bot Process** - Running separately (via `main.py` directly)
2. **API Server** - Not accessible or not connected to bot instance
3. **Frontend** - Cannot reach API to display bot activity

## Root Causes

1. **API Not Listening**: API process exists but not bound to port 8000 (permission issue)
2. **Bot Started Separately**: Bot was started via `main.py` directly, not through API/bot_manager
3. **Separate Instances**: Bot and API have different bot instances, so API can't see bot's trades

## Solution

### Step 1: Fix API Connection

Run the fix script:
```bash
./fix_api_connection.sh
```

This will:
- Kill existing API processes
- Free port 8000
- Restart API properly
- Verify API is accessible

### Step 2: Start Bot Through API

**Important**: The bot MUST be started through the API, not directly via `main.py`.

**Option A: Via Web GUI**
1. Open http://localhost:5173
2. Click "Start Bot" button in the header

**Option B: Via API Endpoint**
```bash
curl -X POST http://localhost:8000/api/bot/start
```

### Step 3: Verify Connection

Run the diagnostic script:
```bash
python3 diagnose_bot_status.py
```

This will show:
- API health status
- Bot running status
- Recent trades count
- Current stats

## Why This Matters

When the bot is started through the API:
- ✅ Bot instance is shared between API and bot_manager
- ✅ API can access `bot.trade_history`, `bot.positions`, etc.
- ✅ Frontend can see real-time updates
- ✅ All trades are visible in the web GUI

When the bot is started separately:
- ❌ API has no access to the bot instance
- ❌ Frontend shows "Bot instance not available"
- ❌ No trades appear in the GUI
- ❌ Stats show zeros

## Monitoring Bot Activity

### Check if Bot is Trading

1. **Via Logs**:
   ```bash
   tail -f trading_bot.log | grep -E "(Trading Cycle|executed|BUY|SELL)"
   ```

2. **Via API**:
   ```bash
   curl http://localhost:8000/api/trades | jq '.total'
   curl http://localhost:8000/api/stats | jq '.total_trades'
   ```

3. **Via Web GUI**:
   - Dashboard → Stats Overview (shows total trades)
   - Trades page → Trade Log (shows all trades)

### Expected Behavior

When bot is running properly:
- Logs show "Trading Cycle #X" messages
- Logs show "Processing trade for SYMBOL..."
- API `/api/trades` returns trade history
- API `/api/stats` shows `total_trades > 0`
- Frontend displays trades and stats

## Troubleshooting

### API Not Responding

**Symptoms**: Frontend shows "Cannot connect to API server"

**Fix**:
```bash
./fix_api_connection.sh
```

### Bot Status Shows "Not Running"

**Symptoms**: Bot controls show bot as stopped

**Fix**:
1. Check if bot is actually running: `ps aux | grep TradingBot`
2. If running separately, stop it: `pkill -f "python.*main.py"`
3. Start via API: `curl -X POST http://localhost:8000/api/bot/start`

### No Trades Appearing

**Symptoms**: Bot is running but no trades in GUI

**Possible Causes**:
1. Bot waiting for market signals (normal behavior)
2. Bot paused due to T+1 settlement (check logs for "Trading Paused")
3. Bot not actually trading (check logs for "Trading Cycle" messages)

**Check**:
```bash
# Check if bot is in trading loop
tail -100 trading_bot.log | grep "Trading Cycle"

# Check for trading pauses
tail -100 trading_bot.log | grep -i "paused"
```

## Next Steps After Fix

1. **Monitor Logs**: `tail -f trading_bot.log`
2. **Check Web GUI**: http://localhost:5173
3. **Verify Trades**: Check Trades page for activity
4. **Check Stats**: Dashboard should show trade counts

## Files Modified

- `api/routes/trades.py` - Fixed import, returns empty trades instead of 503
- `frontend/src/pages/Trades.tsx` - Better error handling
- `fix_api_connection.sh` - Script to restart API properly
- `diagnose_bot_status.py` - Diagnostic tool
