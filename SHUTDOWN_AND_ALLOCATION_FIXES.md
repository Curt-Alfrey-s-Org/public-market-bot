# Shutdown Buttons and Allocation Stat Fixes

## Changes Implemented

### 1. Simplified Shutdown Buttons ✅

**Before:**
- "Shutdown Bot" (orange) - Only stops bot, keeps API/GUI running
- "Shutdown Server" (red) - Stops bot AND closes API server

**After:**
- "Shutdown" (red) - Single button that shuts down bot AND API server
- Removed "Shutdown Bot" button entirely

**Reasoning:**
- Most users want complete shutdown when clicking "Shutdown"
- If they just want to stop trading, they use "Stop" button
- Simpler UI = better UX
- Less confusion about which button to use

**Implementation:**
- Removed `shutdownMutation` (bot-only shutdown)
- Kept only `shutdownServerMutation` (complete shutdown)
- Renamed button from "Shutdown Server" to "Shutdown"
- Simplified confirmation dialog

### 2. Changed Allocation to Available Capital ✅

**Before:**
- Stat showed "Allocation" with `bot.current_allocation` (unclear meaning)
- Could mean: allocated to positions, available, or per-trade amount

**After:**
- Stat shows "Available Capital" with settled funds only
- Uses `bot.get_settled_capital()` which accounts for T+1 settlement
- Shows money actually available for new trades

**T+1 Settlement Tracking:**
- The bot already tracks `unsettled_funds` with settlement dates
- `get_settled_capital()` calculates: `total_capital - unsettled_funds`
- Returns 0.0 if all capital is unsettled (T+1 pending)
- Automatically cleans up funds after settlement date passes

**Implementation:**
```python
# In api/routes/stats.py
if hasattr(bot, 'get_settled_capital'):
    available_capital = bot.get_settled_capital()
else:
    # Fallback calculation
    total_capital = getattr(bot, 'capital', 0.0)
    allocated_capital = getattr(bot, 'current_allocation', 0.0)
    unsettled_funds = getattr(bot, 'unsettled_funds', [])
    total_unsettled = sum(fund.get('amount', 0) for fund in unsettled_funds)
    available_capital = max(0.0, total_capital - allocated_capital - total_unsettled)

allocation = available_capital  # Return as allocation field
```

**Frontend:**
- Changed title from "Allocation" to "Available Capital"
- Changed icon from 📊 to 💵 (money icon)
- Value shows settled funds available for trading

## Benefits

### Shutdown Simplification
- ✅ Clearer user experience - one shutdown button
- ✅ Less confusion - no need to choose between two shutdown options
- ✅ Simpler code - removed unnecessary bot-only shutdown endpoint usage
- ✅ Consistent behavior - shutdown always means complete shutdown

### Available Capital Display
- ✅ More actionable - shows money ready for new trades
- ✅ Accounts for T+1 settlement - only shows settled funds
- ✅ Accurate - reflects real trading constraints
- ✅ Better UX - users see what they can actually use

## Technical Details

### T+1 Settlement Logic

The bot tracks settlement using:
- `unsettled_funds`: List of funds with settlement dates
- `get_settled_capital()`: Returns available capital after settlement
- `_clean_settled_funds()`: Removes funds after settlement date passes
- `_add_unsettled_funds()`: Adds funds when trades execute

**Settlement Rules:**
- T+1 = 1 business day after trade execution
- Weekends excluded from settlement calculation
- Funds become available after settlement date passes
- Available capital = Total capital - Unsettled funds - Allocated capital

### Files Modified

1. **`frontend/src/components/BotControls.tsx`**
   - Removed `shutdownMutation` and `showShutdownBotDialog`
   - Simplified to single shutdown button
   - Updated confirmation dialog

2. **`api/routes/stats.py`**
   - Changed allocation calculation to use `get_settled_capital()`
   - Added fallback for bots without settlement tracking
   - Returns available capital instead of allocated capital

3. **`frontend/src/components/StatsOverview.tsx`**
   - Changed stat title from "Allocation" to "Available Capital"
   - Changed icon from 📊 to 💵

## User Experience

### Before
- User sees "Allocation: $500" (unclear what this means)
- Two shutdown buttons (confusing which to use)
- No visibility into settlement status

### After
- User sees "Available Capital: $500" (clear - money ready for trades)
- Single "Shutdown" button (clear action)
- Automatically accounts for T+1 settlement (accurate)

## Future Enhancements

Potential improvements:
- Show breakdown: "Available: $500, Unsettled: $200 (settles tomorrow)"
- Add tooltip explaining T+1 settlement
- Show next settlement date and amount
- Visual indicator when funds are unsettled
