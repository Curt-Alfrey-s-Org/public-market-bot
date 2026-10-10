# BOT_ENABLE_AI_AUTO_TWEAK NameError Fix

## Issue Summary

The web GUI (`web_gui.py`) was failing to start with the following error:

```
NameError: name 'BOT_ENABLE_AI_AUTO_TWEAK' is not defined
```

This error occurred at line 2474 during module initialization when the layout was being constructed.

## Root Cause

The issue was caused by using a module-level variable (`BOT_ENABLE_AI_AUTO_TWEAK`) directly in the layout definition before Python had executed the line that defined it. Even though the variable was defined at line 187, the layout construction code at line 2474 was trying to reference it during the same module initialization phase, before all top-level code had executed.

### Why This Happened

In Python, when a module is imported:
1. The interpreter reads the entire file
2. It starts executing code from top to bottom
3. When it encounters `app.layout = html.Div(...)`, it evaluates the entire expression
4. During that evaluation, any references to variables must already be defined

The problematic code was:
```python
# Line 187
BOT_ENABLE_AI_AUTO_TWEAK = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'

# Lines 738-2475 - Layout definition
app.layout = html.Div([
    # ... many lines ...
    html.Div([
        # ...
    ], style={'display': 'block' if BOT_ENABLE_AI_AUTO_TWEAK else 'none'}),  # ❌ Error here!
])
```

## Solution

The fix changes the layout code to use `os.getenv()` directly instead of referencing the variable:

```python
# Before (caused NameError)
], style={'display': 'block' if BOT_ENABLE_AI_AUTO_TWEAK else 'none'}),

# After (fixed)
], style={'display': 'block' if os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true' else 'none'}),
```

This works because `os.getenv()` is a function call that executes immediately, without needing to reference a not-yet-defined variable.

## Current Status

✅ **FIXED** - The fix was implemented in PR #281 and is present in the current codebase.

- Line 187: Variable is defined for use in callbacks (runtime code)
- Line 2475: Layout uses `os.getenv()` directly (module load time)
- Line 2987: Callbacks use the variable directly (runtime code - this is OK)

## Verification

Three test suites validate the fix:

1. **test_fix_bot_enable_ai.py** - Validates the fix pattern
2. **test_web_gui_bot_enable_ai.py** - Tests variable definition and usage
3. **test_bot_enable_ai_complete.py** - Comprehensive test suite

All tests pass:
```bash
python3 -m unittest test_fix_bot_enable_ai -v            # 3 tests pass
python3 -m unittest test_web_gui_bot_enable_ai -v        # 4 tests pass
python3 -m unittest test_bot_enable_ai_complete -v       # 6 tests pass
```

## Best Practices to Prevent Similar Issues

### 1. Use Environment Variables Directly in Layouts

When building Dash layouts (or any code that runs during module initialization), use `os.getenv()` directly:

```python
# ✅ GOOD - Direct environment variable read
html.Div(
    style={'display': 'block' if os.getenv('MY_VAR', 'false') == 'true' else 'none'}
)

# ❌ BAD - References module-level variable during module init
html.Div(
    style={'display': 'block' if MY_VAR else 'none'}
)
```

### 2. Module-Level Variables for Runtime Code

Module-level variables can be used in:
- Callback functions (they run at runtime)
- Regular functions called after module initialization
- Any code that executes after the module is fully loaded

```python
# Module level - OK for callbacks
BOT_ENABLE_AI = os.getenv('BOT_ENABLE_AI_AUTO_TWEAK', 'false').lower() == 'true'

@app.callback(...)
def my_callback():
    if BOT_ENABLE_AI:  # ✅ This is fine - runs at runtime
        return "Enabled"
```

### 3. Lazy Initialization Pattern

For complex configuration, consider lazy initialization:

```python
_config_cache = {}

def get_config(key, default=None):
    """Lazy config loading - evaluates on first access"""
    if key not in _config_cache:
        _config_cache[key] = os.getenv(key, default)
    return _config_cache[key]

# Use in layout
html.Div(
    style={'display': 'block' if get_config('MY_VAR', 'false') == 'true' else 'none'}
)
```

## Related Files

- `web_gui.py` - Main web GUI file with the fix
- `.env.example` - Documents `BOT_ENABLE_AI_AUTO_TWEAK=false`
- `test_fix_bot_enable_ai.py` - Original fix test
- `test_web_gui_bot_enable_ai.py` - Variable definition test
- `test_bot_enable_ai_complete.py` - Comprehensive test suite

## Environment Variable

The `BOT_ENABLE_AI_AUTO_TWEAK` environment variable controls the AI auto-tweak feature:

```bash
# In .env file
BOT_ENABLE_AI_AUTO_TWEAK=false  # Default: disabled (BETA feature)
BOT_ENABLE_AI_AUTO_TWEAK=true   # Enable AI strategy auto-tuning
```

**Note**: This is a BETA feature. When enabled, the bot can use AI to automatically suggest and apply strategy optimizations.

## References

- PR #281: Fix NameError: BOT_ENABLE_AI_AUTO_TWEAK undefined in layout initialization
- [Python Module Initialization](https://docs.python.org/
- [Dash Layout Best Practices](https://dash.plotly.com/layout)
