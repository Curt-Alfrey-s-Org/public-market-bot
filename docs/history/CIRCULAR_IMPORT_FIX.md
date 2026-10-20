# Circular Import Fix

## Issue Found
**Critical Error**: API was failing to start due to circular imports

```
ImportError: cannot import name 'get_bot_instance' from partially initialized module 'api.main'
```

## Root Cause
Multiple route files were importing `get_bot_instance` from `api.main` instead of `api.utils`, causing circular import errors when `api.main` tried to import the routes.

## Files Fixed

### ✅ `api/routes/settings.py`
- **Before**: `from api.main import get_bot_instance`
- **After**: Removed (not actually used in this file)

### ✅ `api/routes/ai.py`
- **Before**: `from api.main import get_bot_instance`
- **After**: `from api.utils import get_bot_instance`

### ✅ `api/routes/tax.py`
- **Before**: `from api.main import get_bot_instance`
- **After**: `from api.utils import get_bot_instance`

## Correct Import Pattern

All route files should use:
```python
from api.utils import get_bot_instance
```

**NOT**:
```python
from api.main import get_bot_instance  # ❌ Causes circular import
```

## Files Already Correct
- ✅ `api/routes/bot.py` - Uses `api.utils`
- ✅ `api/routes/stats.py` - Uses `api.utils`
- ✅ `api/routes/trades.py` - Uses `api.utils`
- ✅ `api/routes/messages.py` - Uses `api.utils`

## Verification

After fixes, API should start successfully:
```bash
python3 -c "from api.main import app; print('OK')"
```

## Status
✅ **FIXED** - All circular imports resolved
✅ **API should now start successfully**
