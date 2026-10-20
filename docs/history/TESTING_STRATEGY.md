# Testing Strategy Overview

This project uses a dual testing approach to provide comprehensive coverage while maintaining flexibility.

## Two Testing Frameworks

### 1. Root-Level Tests (`test_*.py` in project root)

**Framework**: Python's `unittest` module  
**Purpose**: Unit and integration tests for individual modules  
**Location**: Project root directory (145+ test files)  
**Running**: 
```bash
# Run all root tests
python3 run_unittest.py

# Run specific test
python3 test_trading_bot.py

# Run with pytest
pytest test_*.py -v
```

**Examples**:
- `test_indicators.py` - Technical indicator calculations
- `test_strategies_comprehensive.py` - Trading strategy signals
- `test_risk_management_comprehensive.py` - Position sizing and risk
- `test_trading_bot.py` - Main bot functionality

**When to use**:
- Testing individual functions/methods
- Module-specific tests
- Unit tests that don't require external services
- Quick iteration during development

### 2. Structured Test Framework (`tests/` directory)

**Framework**: Custom test framework with `BaseTestModule`  
**Purpose**: Integration, E2E, and system-level testing  
**Location**: `tests/` directory with subdirectories  
**Running**:
```bash
# Run structured tests
python3 tests/runner.py

# Run with specific options
python3 tests/runner.py --api-url http://localhost:8000
```

**Structure**:
```
tests/
├── framework/           # Base test classes and utilities
│   ├── base_test.py    # BaseTestModule class
│   └── plugin_loader.py # Plugin system
├── backend/            # Backend/API tests
│   ├── test_imports.py
│   ├── test_api_endpoints.py
│   ├── test_bot_integration.py
│   ├── test_error_patterns.py
│   ├── test_e2e_critical_path.py
│   └── test_yfinance_mode.py
├── frontend/           # Frontend/GUI tests
│   ├── test_gui_data_points.py
│   ├── test_gui_visual.py
│   └── test_gui_interactions.py
└── plugins/            # Extensible plugin tests
    └── example_contracts_bot.py
```

**When to use**:
- Testing API endpoints
- Testing frontend data flow
- Integration between components
- E2E workflows
- Cross-module functionality

## Comprehensive Test Runner

### `run_comprehensive_tests.py`

This unified runner orchestrates tests from both frameworks in the correct order:

```bash
# Run all tests in proper order
python3 run_comprehensive_tests.py

# Run specific category
python3 run_comprehensive_tests.py -c unit
python3 run_comprehensive_tests.py -c integration
python3 run_comprehensive_tests.py -c api

# Stop on first failure
python3 run_comprehensive_tests.py -s
```

**Test Execution Order**:
1. **imports** - Verify all modules import correctly (REQUIRED)
2. **unit** - Test individual module functions (REQUIRED)
3. **integration** - Test module interactions (REQUIRED)
4. **api** - Test API endpoints (optional - requires API server)
5. **e2e** - Test complete workflows (optional)
6. **gui** - Test GUI functionality (optional)

**Benefits**:
- Consistent test environment
- Proper dependency order
- Clear pass/fail reporting
- Category-based execution
- Stop-on-failure for faster debugging

## Test Coverage by Module

### Core Module Tests (Root Level)

| Module | Test File | Test Count | Coverage |
|--------|-----------|------------|----------|
| indicators.py | test_indicators.py | 20+ | RSI, MACD, SMA, EMA, Bollinger, ATR, edge cases |
| strategies.py | test_strategies_comprehensive.py | 32+ | All strategies, signal generation, crossovers |
| risk_management.py | test_risk_management_comprehensive.py | 25+ | Position sizing, risk/reward, edge cases |
| main.py | test_trading_bot.py | 50+ | Bot lifecycle, trading logic, PDT compliance |
| portfolio_optimizer.py | test_portfolio_optimizer.py | 15+ | MPT, asset allocation, optimization |
| sentiment_analyzer.py | test_sentiment_analyzer.py | 10+ | News sentiment, API integration |

### Integration Tests (tests/ directory)

| Category | Test File | Purpose |
|----------|-----------|---------|
| Imports | test_imports.py | Module import validation, circular dependency detection |
| API | test_api_endpoints.py | All API endpoints, CORS, response structure |
| Bot | test_bot_integration.py | Bot instance, data consistency, calculations |
| Errors | test_error_patterns.py | Regression tests for known error patterns |
| E2E | test_e2e_critical_path.py | Critical workflow validation |
| yfinance | test_yfinance_mode.py | Price fetching, fallback logic |

## Quick Start

### For Development

1. **After code changes**:
   ```bash
   # Run unit tests for your module
   python3 test_your_module.py -v
   ```

2. **Before committing**:
   ```bash
   # Run all required tests
   python3 run_comprehensive_tests.py
   ```

3. **For specific components**:
   ```bash
   # Test only indicators
   python3 test_indicators.py -v
   
   # Test only API
   python3 run_comprehensive_tests.py -c api
   ```

### For CI/CD

```bash
# Run all tests with proper environment
export ENABLE_PDT_RULES='false'
export PAPER_TRADING_MODE='true'
export SCHWAB_SANDBOX_MODE='true'

python3 run_comprehensive_tests.py
```

## Environment Variables

Tests require these environment variables:

```bash
export ENABLE_PDT_RULES='false'          # Disable PDT rules for testing
export PAPER_TRADING_MODE='true'         # Use paper trading mode
export SCHWAB_SANDBOX_MODE='true'        # Use sandbox API
export BOT_ENABLE_AI='false'             # Disable AI features
export BOT_ENABLE_ML='false'             # Disable ML features
export ENABLE_STOCK_SCREENER='false'     # Disable stock screener
export ENABLE_EMAIL_ALERTS='false'       # Disable email alerts
```

These are automatically set by `run_comprehensive_tests.py`.

## Adding New Tests

### For Root-Level Tests

1. Create `test_your_module.py`
2. Use unittest framework:
   ```python
   import unittest
   from your_module import YourClass
   
   class TestYourClass(unittest.TestCase):
       def test_feature(self):
           # Test code
           pass
   ```
3. Add to `run_comprehensive_tests.py` in appropriate category

### For Structured Tests

1. Create test in `tests/backend/` or `tests/frontend/`
2. Inherit from `BaseTestModule`:
   ```python
   from tests.framework.base_test import BaseTestModule, TestResult
   
   class YourTest(BaseTestModule):
       def test_feature(self):
           def _test():
               # Test code
               return True
           return self.run_test("Feature Test", _test)
   ```
3. Register in `tests/runner.py`

## Best Practices

1. **Mock external APIs**: Never make real API calls in tests
2. **Set environment early**: Set env vars before importing modules
3. **Keep tests isolated**: Each test should be independent
4. **Use descriptive names**: `test_position_size_with_tight_stop` not `test1`
5. **Test edge cases**: Zero, negative, NaN, empty data
6. **Assert explicitly**: Use specific assertions, not just `assertTrue`
7. **Clean up resources**: Use setUp/tearDown for fixtures
8. **Document test purpose**: Add docstrings explaining what's tested

## Common Issues

### Import Errors
**Problem**: `ModuleNotFoundError: No module named 'pandas'`  
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Environment Variables Not Set
**Problem**: Tests fail with unexpected behavior  
**Solution**: Use `run_comprehensive_tests.py` which sets them automatically

### API Tests Failing
**Problem**: All API tests fail immediately  
**Solution**: Start API server: `./start_api.sh` or `uvicorn api.main:app`

### Circular Import Errors
**Problem**: `ImportError: cannot import name 'X' from partially initialized module`  
**Solution**: Run import tests: `python3 run_comprehensive_tests.py -c imports`

## Documentation

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing guide
- **[SELF_TEST_IMPROVEMENTS.md](SELF_TEST_IMPROVEMENTS.md)** - Summary of improvements
- **[tests/README.md](tests/README.md)** - Structured test framework details
- **[tests/ENHANCED_TESTING.md](tests/ENHANCED_TESTING.md)** - Enhanced testing features

## Verification

To verify the test infrastructure is working:

```bash
python3 verify_test_improvements.py
```

This checks:
- Test runner is present and executable
- New test files exist
- Documentation is complete
- Test structure is valid
- Test count is reasonable

## Summary

- **145+ root-level tests** for unit/integration testing
- **11 structured tests** for system-level testing
- **77+ new comprehensive tests** added for indicators, strategies, risk management
- **Unified test runner** for consistent execution
- **Clear documentation** for maintenance and extension

Choose the appropriate framework based on what you're testing:
- **Root level**: Fast, focused unit tests
- **Structured**: Integration, E2E, system tests
- **Comprehensive runner**: All tests in correct order
