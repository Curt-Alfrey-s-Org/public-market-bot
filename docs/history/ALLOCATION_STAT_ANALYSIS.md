# Allocation Stat Analysis

## Current Implementation

### What is Displayed

In `StatsOverview.tsx`:
```typescript
<StatCard
  title="Allocation"
  value={`$${stats.allocation.toFixed(2)}`}
  icon="📊"
/>
```

### What Does `allocation` Represent?

From `api/routes/stats.py`:
```python
# Get allocation (current allocation)
allocation = getattr(bot, 'current_allocation', 0.0)
```

This gets `current_allocation` from the bot instance.

## Question: Is This "Amount Available"?

### Current Interpretation (Unclear)

The code gets `bot.current_allocation`, but it's not clear if this means:
1. **Amount currently allocated** (money in open positions)
2. **Amount available** (unallocated capital ready for trading)
3. **Per-trade allocation** (how much to allocate per trade)

### What Should It Be?

Based on the context and typical trading bot terminology:

**Most Likely Meaning:**
- `current_allocation` probably means **amount currently allocated to open positions**
- NOT the amount available

**What Users Probably Want to See:**
- **Available Capital**: Total capital minus allocated capital
- **Allocated Capital**: Money currently in open positions
- **Per-Trade Allocation**: How much to allocate per trade (from settings)

## Recommendation

### Option 1: Show "Available Capital" (Recommended)
Change the stat to show unallocated capital:
```python
total_capital = getattr(bot, 'capital', 0.0)
allocated_capital = getattr(bot, 'current_allocation', 0.0)  # Money in positions
available_capital = total_capital - allocated_capital
```

**Display:**
- Title: "Available Capital"
- Value: `$X,XXX.XX` (unallocated money ready for trading)

### Option 2: Show "Allocated Capital"
Keep current but clarify:
- Title: "Allocated Capital" or "In Positions"
- Value: `$X,XXX.XX` (money currently in open positions)

### Option 3: Show Both
Add two stats:
- "Available Capital": Unallocated money
- "Allocated Capital": Money in positions

### Option 4: Show "Per-Trade Allocation"
Show the allocation amount from settings:
- Title: "Per-Trade Allocation"
- Value: `$X,XXX.XX` (from `BOT_MIN_ALLOCATION` or `BOT_MAX_ALLOCATION`)

## Suggested Solution

**Recommendation: Option 1 - Show "Available Capital"**

**Reasoning:**
1. Users care most about how much money is available for new trades
2. "Available" is more actionable than "allocated"
3. Can see allocated capital by looking at open positions
4. Matches user mental model: "How much can I trade with?"

**Implementation:**
```python
# In api/routes/stats.py
total_capital = getattr(bot, 'capital', 0.0)
allocated_capital = getattr(bot, 'current_allocation', 0.0)  # Money in positions
available_capital = total_capital - allocated_capital

# Return available_capital as allocation
allocation = available_capital
```

**Display:**
- Title: "Available Capital"
- Icon: 💵 (money icon)
- Value: `$X,XXX.XX`

## Alternative: Clarify Current Implementation

If `current_allocation` already means "available", then just:
- Change title to "Available Capital" for clarity
- Add tooltip explaining what it means
