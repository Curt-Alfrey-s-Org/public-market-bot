# Quick Start Guide

## Running Tests

### Basic Usage

```bash
# Run all tests
python3 tests/runner.py

# Run with custom API URL
python3 tests/runner.py --api-url http://localhost:8000

# Save report to file
python3 tests/runner.py --output my_test_report.json
```

### Prerequisites

1. **API Server Running**: The API must be running on the configured port. **If the API is not running, most self-tests will fail** (e.g. "Cannot connect to API"). Start the API first:
   ```bash
   ./start_api.sh
   # or
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```
   The **Run Test** button in the GUI uses the same suite; the API is already up when you use it.

2. **Frontend (Optional)**: For full GUI tests, frontend should be running
   ```bash
   cd frontend && npm run dev
   ```

3. **Python Dependencies**: Install required packages
   ```bash
   pip install requests
   ```

## What Gets Tested

### Backend Tests
- ✅ All API endpoints (health, bot, stats, trades, messages, logs, system)
- ✅ Response structure validation
- ✅ Filter and parameter handling
- ✅ CORS configuration
- ✅ Bot integration and data consistency

### Frontend Tests
- ✅ All GUI data points (dashboard, trades, messages, logs)
- ✅ Data format consistency
- ✅ Refresh rates
- ✅ Error handling
- ✅ Frontend accessibility

## Example Output

```
================================================================================
COMPREHENSIVE SELF-TEST SUITE
================================================================================
API URL: http://localhost:8000
Frontend URL: http://localhost:5173
Started: 2026-01-26 22:00:00
================================================================================

================================================================================
Running: API Endpoints
================================================================================
[2026-01-26 22:00:01] [INFO] [API Endpoints] Starting API endpoints tests...
[2026-01-26 22:00:01] [INFO] [API Endpoints] Completed 13 tests

Module Summary: API Endpoints
  Total: 13
  Passed: 13 (100.0%)
  Failed: 0
  Warnings: 0
  Duration: 2.34s

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 50
Passed: 48 (96.0%)
Failed: 0
Warnings: 2
Skipped: 0
Duration: 12.45s
================================================================================

Full report saved to: test_report_20260126_220012.json
```

## Creating Custom Tests

### For Your Bot

1. Create a new file in `tests/plugins/your_bot_test.py`
2. Inherit from `BaseTestModule`
3. Implement your test methods
4. The framework will automatically discover and run it

Example:
```python
from tests.framework.base_test import BaseTestModule

class YourBotTest(BaseTestModule):
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("Your Bot Name", api_base_url)
    
    def test_your_endpoint(self):
        def _test():
            response = self.api_request("GET", "/api/your/endpoint")
            self.assert_status(response, 200)
            return True
        return self.run_test("Your Endpoint", _test)
    
    def run(self):
        self.test_your_endpoint()
        return self.results
```

## Troubleshooting

### API Not Responding
```
✗ API is not responding (connection refused)
```
**Fix**: Start the API server first

### Import Errors
```
ModuleNotFoundError: No module named 'tests'
```
**Fix**: Run from project root directory

### Tests Failing
Check the detailed report JSON file for specific error messages and stack traces.

## Next Steps

- Read `tests/README.md` for full documentation
- Check `tests/plugins/example_contracts_bot.py` for plugin examples
- Customize tests for your specific bot requirements
