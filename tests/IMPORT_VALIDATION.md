# Import Validation Tests

## Overview

The self-test suite now includes comprehensive import validation tests that catch circular imports, missing modules, and other import-related errors **before** the API starts.

## What Gets Tested

### 1. **Circular Import Pattern Detection**
- Scans all route files for problematic import patterns
- Detects `from api.main import get_bot_instance` (should use `from api.utils import get_bot_instance`)
- Runs first (fastest check, no imports needed)

### 2. **Utils Module Import**
- Verifies `api.utils` can be imported
- Checks for required functions: `get_bot_instance`, `set_bot_instance`

### 3. **Route Module Imports**
- Tests that all route modules can be imported individually:
  - `api.routes.bot`
  - `api.routes.stats`
  - `api.routes.settings`
  - `api.routes.trades`
  - `api.routes.system`
  - `api.routes.messages`
  - `api.routes.ai`
  - `api.routes.tax`
  - `api.routes.logs`
- Verifies each has a `router` attribute

### 4. **Bot Manager Import**
- Tests that `api.bot_manager` can be imported

### 5. **API Main Import** (Most Critical)
- Tests that `api.main` can be imported without errors
- **Catches circular imports** - this is where the error we fixed would have been caught
- Verifies `app` object exists

### 6. **Critical Modules Initialization**
- Tests that all routes can be imported together (simulates what `api.main` does)
- Verifies `api.utils` can be used
- **Catches circular import errors** when importing all routes at once

## How It Works

The `ImportValidationTest` class runs these tests in order:
1. **Pattern Check** (fastest, no imports)
2. **Utils Import** (foundation)
3. **Route Imports** (individual)
4. **Bot Manager Import**
5. **API Main Import** (comprehensive)
6. **Critical Modules Initialization** (full integration)

## Integration

### In Test Runner
The import validation test runs **first** in the comprehensive test suite:
```python
# In tests/runner.py
self.register_module(ImportValidationTest(self.api_url))  # Runs first
self.register_module(APIEndpointsTest(self.api_url))
# ... other tests
```

### In Startup Test
The startup test now includes a "Module Imports" check that runs before API-dependent tests:
```python
# In tests/startup_test.py
tests = [
    ("Module Imports", self.test_imports),  # First - doesn't need API
    ("API Health", self.test_api_health),
    # ... other tests
]
```

## Example: Catching the Circular Import Error

The error we fixed would have been caught like this:

**Before Fix:**
```
[FAIL] API Main Import
Circular import detected: cannot import name 'get_bot_instance' from partially initialized module 'api.main'
```

**After Fix:**
```
[PASS] API Main Import
[PASS] Route Imports
[PASS] Critical Modules Initialization
```

## Running the Tests

### Standalone Import Tests
```bash
python3 -c "from tests.backend.test_imports import ImportValidationTest; t = ImportValidationTest(); results = t.run()"
```

### Via Test Runner
```bash
python3 tests/runner.py
```

### Via Startup Test
```bash
python3 tests/startup_test.py
```

## Benefits

1. **Early Detection**: Catches import errors before API starts
2. **No API Required**: Can run even if API server isn't running
3. **Fast**: Pattern checks run in milliseconds
4. **Comprehensive**: Tests individual imports and full integration
5. **Clear Errors**: Provides detailed error messages with tracebacks

## What Gets Caught

✅ Circular imports (like the one we just fixed)
✅ Missing modules
✅ Missing functions/attributes
✅ Import syntax errors
✅ Module initialization errors
✅ Problematic import patterns

## Status

✅ **Implemented and Working**
- All 6 import validation tests passing
- Integrated into test runner (runs first)
- Integrated into startup test
- Successfully catches circular import errors
