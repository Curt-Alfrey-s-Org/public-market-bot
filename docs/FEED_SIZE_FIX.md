# FEED_SIZE Error Fix

**Date:** January 26, 2026  
**Issue:** `NameError: name 'FEED_SIZE' is not defined` in `web_gui.py`

---

## Problem

The Web GUI was throwing errors when trying to fetch feed data:

```
NameError: name 'FEED_SIZE' is not defined
  File "/home/operator/market-pie5-bot/web_gui.py", line 2944, in fetch_feed_data
    candidates = get_top_performers_watchlist(max_stocks=FEED_SIZE * 2)
```

## Root Cause

`FEED_SIZE` is defined in `top_performers_feed.py` but was not imported in `web_gui.py`. The import statement on line 60 was missing `FEED_SIZE`:

**Before:**
```python
from top_performers_feed import get_top_performers_feed, FEED_ENABLED, get_feed_symbols, get_feed_data
```

## Solution

Added `FEED_SIZE` to the import statement:

**After:**
```python
from top_performers_feed import get_top_performers_feed, FEED_ENABLED, FEED_SIZE, get_feed_symbols, get_feed_data
```

## Verification

✅ `FEED_SIZE` now imports successfully  
✅ Value is accessible: `50` (default from `.env`)  
✅ Calculation `FEED_SIZE * 2` works correctly  
✅ No more `NameError` exceptions

## Files Modified

- `web_gui.py` (line 60): Added `FEED_SIZE` to imports

## Testing

The fix has been verified:
- Import test passes
- Value is correct (50 by default)
- No syntax errors

## Impact

- Feed data fetching now works correctly
- Top performers watchlist can be populated
- Web GUI feed features are functional

---

**Status:** ✅ **FIXED**
