# Comprehensive Self-Test Framework

A modular, extensible test framework for validating backend APIs, frontend data points, and visual aspects of the bot.

## Features

- **Modular Architecture**: Easy to add/remove test modules
- **Plugin System**: Extensible for different bot types
- **Comprehensive Coverage**: Tests backend, frontend, and integration
- **Detailed Reporting**: JSON reports with pass/fail statistics
- **Reusable**: Designed to work with any bot structure

## Quick Start

### Run All Tests

```bash
python3 tests/runner.py
```

### Run with Custom URLs

```bash
python3 tests/runner.py --api-url http://localhost:8000 --frontend-url http://localhost:5173
```

### Generate Report

```bash
python3 tests/runner.py --output test_report.json
```

## Test Modules

### Backend Tests

1. **API Endpoints Test** (`tests/backend/test_api_endpoints.py`)
   - Tests all API endpoints
   - Validates response structure
   - Tests filters and parameters
   - Checks CORS configuration

2. **Bot Integration Test** (`tests/backend/test_bot_integration.py`)
   - Tests bot instance availability
   - Validates data consistency
   - Tests trade/message/log structures
   - Validates calculations

### Frontend Tests

3. **GUI Data Points Test** (`tests/frontend/test_gui_data_points.py`)
   - Tests all data points displayed in GUI
   - Validates dashboard stats
   - Tests trades/messages/logs data
   - Validates refresh rates

4. **GUI Visual Test** (`tests/frontend/test_gui_visual.py`)
   - Tests frontend accessibility
   - Validates API proxy configuration
   - Tests CORS setup
   - Validates response times

## Plugin System

### Creating a Plugin

Create a new test module in `tests/plugins/`:

```python
from tests.framework.base_test import BaseTestModule, TestResult, TestStatus

class MyCustomTest(BaseTestModule):
    """My custom test module"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("My Custom Test", api_base_url)
    
    def test_something(self) -> TestResult:
        """Test something specific"""
        def _test():
            response = self.api_request("GET", "/api/custom/endpoint")
            self.assert_status(response, 200)
            return True
        
        return self.run_test("Test Something", _test)
    
    def run(self):
        """Run all tests"""
        self.log("Starting custom tests...")
        self.test_something()
        return self.results
```

The plugin will be automatically discovered and loaded.

### Plugin for Federal Contracts Bot

Example structure for a contracts bot plugin:

```python
from tests.framework.base_test import BaseTestModule, TestResult

class ContractsBotTest(BaseTestModule):
    """Tests for federal contracts bot"""
    
    def test_contract_search(self) -> TestResult:
        """Test contract search endpoint"""
        def _test():
            response = self.api_request("GET", "/api/contracts/search", params={"keyword": "IT"})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            assert "contracts" in data
            return True
        
        return self.run_test("Contract Search", _test)
    
    def test_proposal_generation(self) -> TestResult:
        """Test proposal generation"""
        def _test():
            response = self.api_request("POST", "/api/proposals/generate", json={
                "contract_id": "123",
                "template": "standard"
            })
            self.assert_status(response, 200)
            return True
        
        return self.run_test("Proposal Generation", _test)
    
    def run(self):
        """Run all contract bot tests"""
        self.test_contract_search()
        self.test_proposal_generation()
        return self.results
```

## Test Structure

### Base Test Module

All test modules inherit from `BaseTestModule` which provides:

- `api_request()` - Make HTTP requests
- `assert_status()` - Assert HTTP status codes
- `assert_json()` - Assert valid JSON response
- `assert_field_exists()` - Assert field presence
- `assert_field_type()` - Assert field type
- `run_test()` - Run and record test results
- `log()` - Log messages with timestamps

### Test Results

Each test returns a `TestResult` with:
- `name` - Test name
- `status` - PASS, FAIL, SKIP, or WARN
- `message` - Result message
- `duration` - Test duration
- `data` - Additional test data
- `timestamp` - When test ran

## Report Format

Test reports are generated as JSON with:

```json
{
  "summary": {
    "total": 50,
    "passed": 45,
    "failed": 2,
    "warnings": 3,
    "success_rate": 90.0,
    "duration": 12.34
  },
  "modules": [...],
  "results": [...]
}
```

## Extending for Different Bots

### For Federal Contracts Bot

1. Create plugin in `tests/plugins/contracts_bot_test.py`
2. Test contract-specific endpoints:
   - `/api/contracts/search`
   - `/api/contracts/{id}`
   - `/api/proposals/generate`
   - `/api/proposals/{id}`
   - `/api/contracts/{id}/manage`
3. Test contract-specific data points:
   - Contract details
   - Proposal templates
   - Lifecycle status
   - Document management

### For Any Bot Type

1. Identify bot-specific endpoints
2. Create test module in `tests/plugins/`
3. Test data structures
4. Test business logic
5. Test integration points

## Best Practices

1. **Test Structure**: Follow the existing test module pattern
2. **Error Handling**: Use try/except in test functions
3. **Assertions**: Use provided assertion methods
4. **Logging**: Use `self.log()` for important messages
5. **Documentation**: Document what each test validates

## Running in CI/CD

```bash
# Run tests and fail on any failure
python3 tests/runner.py --output test_report.json
if [ $? -ne 0 ]; then
    echo "Tests failed!"
    exit 1
fi
```

## Future Enhancements

- [ ] Browser automation for visual tests (Selenium/Playwright)
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Security testing
- [ ] Accessibility testing
- [ ] Mobile responsiveness testing
