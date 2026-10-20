# Self-Test System Verification Guide

## How to Verify the Self-Test System is Working

### Quick Verification

Run the verification script:
```bash
python3 verify_selftest_system.py
```

This will test:
1. ✅ Startup test module functionality
2. ✅ API health endpoint
3. ✅ Startup event registration
4. ✅ Frontend API client compatibility
5. ✅ Test result consistency

### Framework Component Test

Test the framework itself (works even if API isn't running):
```bash
python3 tests/test_framework_verification.py
```

This verifies:
- ✅ All framework components import correctly
- ✅ Test modules can be instantiated
- ✅ Test execution works
- ✅ API integration code is correct

## What to Look For

### ✅ Framework Working Correctly

**Signs the framework is working:**
1. **Startup test module executes** - No import errors, tests run
2. **Test results structure** - Returns dict with total, passed, failed, results
3. **API endpoint exists** - `/api/system/health` endpoint available
4. **Startup event registered** - API has startup event handler
5. **Frontend can query** - System health endpoint returns JSON

**Example of working framework:**
```
✓ Startup test module imports successfully
✓ StartupTest class instantiates
✓ Tests execute without errors
  Results: 5/5 passed (when API is running)
  Results: 0/5 passed (when API is not running - expected)
```

### ⚠️ Framework Issues

**Signs of framework problems:**
1. **Import errors** - Can't import test modules
2. **Attribute errors** - Missing methods or classes
3. **Type errors** - Wrong data structures
4. **Execution errors** - Tests crash instead of returning results

## Expected Behavior

### When API is Running

```
✓ API is accessible
✓ Startup tests run successfully
✓ 5/5 tests pass (or fewer if endpoints have issues)
✓ System health endpoint returns test results
✓ Frontend shows green PASS light
```

### When API is NOT Running

```
⚠ API is not accessible
✓ Framework still works (tests execute)
✗ 0/5 tests pass (expected - can't connect to API)
⚠ System health endpoint unavailable
⚠ Frontend shows yellow ... or red FAIL
```

**This is CORRECT behavior** - the framework is working, it's just detecting that the API isn't accessible.

## Verification Checklist

- [ ] Framework components import without errors
- [ ] StartupTest class can be instantiated
- [ ] Tests can execute (even if they fail due to API)
- [ ] Test results have correct structure
- [ ] API startup event is registered
- [ ] System health endpoint exists
- [ ] Frontend can query system health
- [ ] Status lights appear in GUI sidebar

## Testing the Tests

### Test 1: Direct Module Test
```bash
python3 tests/startup_test.py
```
**Expected:** Tests execute, show results (may fail if API not running)

### Test 2: Framework Verification
```bash
python3 tests/test_framework_verification.py
```
**Expected:** All components verify successfully

### Test 3: Full System Test
```bash
python3 verify_selftest_system.py
```
**Expected:** Framework works, API-dependent tests may fail if API not running

### Test 4: API Endpoint Test
```bash
curl http://localhost:8000/api/system/health | jq '.self_test'
```
**Expected:** Returns self-test results (if API is running)

## Interpreting Results

### Framework Status: ✅ WORKING
- All components import
- Tests execute
- Results structure correct
- API integration code present

### API Status: ⚠️ NOT ACCESSIBLE
- Tests fail with connection errors
- This is **expected** if API isn't running
- Framework is still working correctly

### Conclusion

**If framework verification passes, the self-test system is working correctly.**

Test failures due to API unavailability are **expected** and indicate the framework is correctly detecting issues.

## Next Steps

1. **Resolve API permission issue** to get API running
2. **Once API runs**, tests will pass
3. **Status lights** will show green in GUI
4. **Startup tests** will run automatically when API starts
