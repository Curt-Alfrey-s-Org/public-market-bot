# Testing Guide for market-pie5-bot

This guide provides comprehensive information about the testing infrastructure, workflows, and best practices for the market-pie5-bot project.

## Table of Contents
- [Test Configuration](#test-configuration)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Writing Tests](#writing-tests)
- [Code Coverage](#code-coverage)
- [Best Practices](#best-practices)

---

## Test Configuration

### pytest.ini

The project uses pytest as the primary test framework. Configuration is stored in `pytest.ini`:

- **Test Discovery**: Automatically finds `test_*.py` files
- **Parallel Execution**: Supports pytest-xdist for running tests in parallel
- **Coverage**: Integrated with pytest-cov for code coverage reporting
- **Markers**: Organized by test type (unit, integration, e2e, etc.)

### .coveragerc

Coverage configuration includes:

- **Minimum Coverage**: 60% threshold (configurable)
- **Excluded Files**: Test files, demos, verification scripts, venv
- **Branch Coverage**: Enabled for comprehensive coverage metrics
- **Reports**: XML (for CI), HTML (for local viewing), and terminal output

---

## Running Tests

### Comprehensive Test Runner (Recommended)

The project includes a comprehensive test runner that organizes tests in the correct execution order:

**Run all tests in proper order:**
```bash
python3 run_comprehensive_tests.py
```

**Run with verbose output:**
```bash
python3 run_comprehensive_tests.py -v
```

**Run specific category:**
```bash
# Run only unit tests
python3 run_comprehensive_tests.py -c unit

# Run only integration tests
python3 run_comprehensive_tests.py -c integration

# Run only API tests
python3 run_comprehensive_tests.py -c api
```

**Stop on first failure:**
```bash
python3 run_comprehensive_tests.py -s
```

**Test execution order:**
1. **imports** - Import and module validation (required)
2. **unit** - Individual module tests (required)
3. **integration** - Module interaction tests (required)
4. **api** - API endpoint tests (optional - requires API server)
5. **e2e** - End-to-end workflows (optional)
6. **gui** - GUI functionality tests (optional)

### Traditional pytest (Alternative)

**Run all tests:**
```bash
pytest test_*.py -v
```

**Run tests in parallel:**
```bash
pytest test_*.py -n auto
```

**Run with coverage:**
```bash
pytest test_*.py --cov=. --cov-report=term-missing --cov-report=html
```

**Run specific test types:**
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"
```

**Run specific test file:**
```bash
pytest test_trading_bot.py -v
```

**Run specific test:**
```bash
pytest test_trading_bot.py::TestRollingWinRate::test_win_rate_empty_history -v
```

### Environment Variables

Always set these environment variables when running tests:

```bash
export ENABLE_PDT_RULES='false'
export PAPER_TRADING_MODE='true'
export SCHWAB_SANDBOX_MODE='true'
export BOT_ENABLE_AI='false'
export BOT_ENABLE_ML='false'
export ENABLE_STOCK_SCREENER='false'
export ENABLE_EMAIL_ALERTS='false'
```

Or use the convenience script:
```bash
source test_user_env.sh  # If available
```

---

## Test Organization

### Test Structure

The project has two test frameworks:

**1. Root-level test files** (`test_*.py`)
- Use Python's `unittest` framework
- Individual feature and module tests
- Run via pytest or direct python execution

**2. Structured test framework** (`tests/` directory)
- Custom test framework with `BaseTestModule`
- Organized by category (backend, frontend, plugins)
- Run via `tests/runner.py`

### New Comprehensive Tests

Recent additions provide comprehensive module coverage:

| Test File | Module Tested | Coverage |
|-----------|--------------|----------|
| `test_indicators.py` | `indicators.py` | All technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, ATR) with edge cases |
| `test_strategies_comprehensive.py` | `strategies.py` | All trading strategies (SMA, RSI, MACD, Bollinger, Momentum) with signal generation |
| `test_risk_management_comprehensive.py` | `risk_management.py` | Position sizing, risk calculations, edge cases (zero/negative prices, fractional shares) |

These tests include:
- Basic functionality tests
- Edge case handling (NaN, zero, negative values)
- Invalid input handling
- Signal generation verification
- Integration between components

### Test Markers

Tests are organized using pytest markers:

| Marker | Description | Example |
|--------|-------------|---------|
| `@pytest.mark.unit` | Unit tests for individual components | Testing a single function |
| `@pytest.mark.integration` | Integration tests for component interactions | Testing API integration |
| `@pytest.mark.e2e` | End-to-end tests for full workflows | Testing bot lifecycle |
| `@pytest.mark.slow` | Tests that take >5 seconds | Backtesting, large datasets |
| `@pytest.mark.api` | Tests requiring external API access | Schwab API, yfinance |
| `@pytest.mark.gui` | Tests for GUI components | Dash, Tkinter tests |
| `@pytest.mark.security` | Security-related tests | Authentication, encryption |
| `@pytest.mark.performance` | Performance and benchmark tests | Speed, memory usage |

### Adding Markers to Tests

```python
import pytest

@pytest.mark.unit
def test_calculate_position_size():
    """Unit test for position sizing calculation"""
    # Test code here
    pass

@pytest.mark.integration
@pytest.mark.api
def test_fetch_stock_price():
    """Integration test for stock price fetching"""
    # Test code here
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_full_trading_cycle():
    """E2E test for complete trading workflow"""
    # Test code here
    pass
```

### Test File Structure

```
market-pie5-bot/
├── test_*.py              # Unit and integration tests (root level)
├── pytest.ini             # Pytest configuration
├── .coveragerc            # Coverage configuration
└── reports/               # Test reports (generated)
    ├── junit.xml
    ├── coverage.xml
    └── htmlcov/
```

**Note**: Demo and verification scripts should eventually be moved to separate directories:
- `scripts/demos/` - Demo scripts
- `scripts/verification/` - Verification scripts
- `docs/examples/` - Example code

---

## GitHub Actions Workflows

### 1. Tests Workflow (`tests.yml`)

**Trigger**: Push/PR to main/develop branches

**What it does**:
- Runs on Python 3.10, 3.11, 3.12 (matrix)
- Executes all tests in parallel using pytest-xdist
- Generates code coverage reports
- Uploads coverage to Codecov
- Creates test result artifacts

**Status**: ✅ **REQUIRED** - Must pass before merge

**Environment**:
- Paper Trading Mode: `true`
- Sandbox Mode: `true`
- PDT Rules: `false`
- AI/ML Features: `false`

### 2. Lint Workflow (`lint.yml`)

**Trigger**: Push/PR to main/develop branches

**What it does**:
- Runs flake8 for syntax errors (blocking)
- Checks code formatting with black (non-blocking)
- Checks import sorting with isort (non-blocking)
- Runs pylint for code quality (non-blocking)

**Status**: ✅ **REQUIRED** - Critical errors must be fixed

**Results**: Detailed summary in GitHub Actions output

### 3. Security Workflow (`security.yml`)

**Trigger**: Push/PR to main/develop branches, weekly schedule

**What it does**:
- Scans dependencies with Safety (blocking on critical/high)
- Scans code with Bandit (blocking on high-severity)
- Runs CodeQL analysis
- Uploads security reports

**Status**: ✅ **REQUIRED** - High-severity issues must be fixed

**Schedule**: Weekly on Sundays at 00:00 UTC

### 4. E2E Workflow (`e2e.yml`)

**Trigger**: Push/PR to main/develop branches, manual

**What it does**:
- Runs integration tests
- Tests different bot modes (Paper, Sandbox)
- Validates non-interactive mode
- Timeout: 60-120 seconds per test

**Status**: ✅ **REQUIRED** - Must pass before merge

### 5. Copilot Sentinel (`copilot-sentinel.yml`)

**Trigger**: PR events, reviews

**What it does**:
- Prevents premature merging of Copilot PRs
- Checks for work-in-progress indicators
- Validates completion markers

**Status**: ✅ **REQUIRED** - Ensures Copilot work is complete

### 6. Release Workflow (`release.yml`)

**Trigger**: Version tags (v*.*.*)

**What it does**:
- Runs full test suite
- Generates release notes
- Creates distribution archives
- Publishes GitHub release

**Status**: Automated release creation

---

## Writing Tests

### Test Structure

Use the standard unittest or pytest structure:

```python
#!/usr/bin/env python3
"""
Test suite for [component description]
"""

import os
# Set environment variables BEFORE importing modules
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
import pytest
from unittest.mock import patch, MagicMock

from main import TradingBot

@pytest.mark.unit
class TestComponentName(unittest.TestCase):
    """Test suite for ComponentName"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    def test_feature_with_valid_input(self):
        """Test that feature works with valid input"""
        result = self.bot.some_method('valid_input')
        self.assertTrue(result)
        self.assertIn('expected', result)
    
    @patch('requests.get')
    def test_feature_with_api_error(self, mock_get):
        """Test that feature handles API errors gracefully"""
        mock_get.side_effect = Exception("API Error")
        result = self.bot.some_method()
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
```

### Mocking External APIs

**Always mock external API calls** to avoid:
- Real API usage and rate limits
- Test failures due to network issues
- Unnecessary delays

```python
from unittest.mock import patch, MagicMock

@patch('requests.get')
def test_fetch_price(self, mock_get):
    """Test price fetching with mocked API"""
    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 150.0}
    mock_get.return_value = mock_response
    
    price = fetch_stock_price('AAPL')
    self.assertEqual(price, 150.0)
```

### Test Naming Conventions

- Test files: `test_<component>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<feature>_<scenario>`

Examples:
- `test_trading_bot.py`
- `class TestTrailingStop`
- `def test_trailing_stop_with_price_increase()`

---

## Code Coverage

### Viewing Coverage Reports

**Terminal output:**
```bash
pytest test_*.py --cov=. --cov-report=term-missing
```

**HTML report:**
```bash
pytest test_*.py --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

**Coverage requirements:**
- Minimum: 60% overall
- Critical modules should aim for 80%+
- New code should be well-tested

### Coverage Exclusions

The following are excluded from coverage:
- Test files (`test_*.py`)
- Demo files (`demo_*.py`)
- Verification scripts (`verify_*.py`, `validate_*.py`)
- Virtual environment (`venv/`)
- Node modules (`node_modules/`)

---

## Best Practices

### Do's ✅

1. **Always set environment variables** before running tests
2. **Mock external API calls** to avoid real API usage
3. **Use descriptive test names** that explain what's being tested
4. **Add docstrings** to test methods
5. **Use markers** to organize tests by type
6. **Test edge cases** and error conditions
7. **Keep tests independent** - no test should depend on another
8. **Run tests before committing** code changes
9. **Update tests** when changing functionality
10. **Add new tests** for new features

### Don'ts ❌

1. **Don't make real API calls** in tests
2. **Don't skip tests** without good reason
3. **Don't commit failing tests**
4. **Don't use `print()` for debugging** - use logging or pytest's `-s` flag
5. **Don't test implementation details** - test behavior
6. **Don't write tests that depend on external state**
7. **Don't ignore test failures** in CI/CD
8. **Don't disable security checks** without review
9. **Don't commit with syntax errors**
10. **Don't bypass PDT rules** in production mode

### Debugging Test Failures

**Run with verbose output:**
```bash
pytest test_file.py -vv -s
```

**Run with PDB debugger:**
```bash
pytest test_file.py --pdb
```

**Show local variables on failure:**
```bash
pytest test_file.py -l
```

**Run last failed tests only:**
```bash
pytest --lf
```

**Run failed tests first:**
```bash
pytest --ff
```

---

## Continuous Integration

### Required Status Checks

Before a PR can be merged, the following checks must pass:

1. ✅ **Tests** - All unit tests pass on Python 3.10-3.12
2. ✅ **Lint** - No critical syntax errors (flake8)
3. ✅ **Security** - No high-severity security issues
4. ✅ **E2E** - Integration and E2E tests pass
5. ✅ **Copilot Sentinel** - Copilot work is complete (if applicable)

### Workflow Status Badges

Add to README.md:
```markdown
[![Tests](https://github.com/operator/market-pie5-bot/workflows/Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/tests.yml)
[![Code Quality](https://github.com/operator/market-pie5-bot/workflows/Code%20Quality/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/lint.yml)
[![Security](https://github.com/operator/market-pie5-bot/workflows/Security%20Scan/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/security.yml)
[![E2E Tests](https://github.com/operator/market-pie5-bot/workflows/End-to-End%20Tests/badge.svg)](https://github.com/operator/market-pie5-bot/actions/workflows/e2e.yml)
```

---

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
- **Solution**: Install all dependencies: `pip install -r requirements.txt`

**Issue**: Tests fail with environment variable errors
- **Solution**: Set required environment variables (see above)

**Issue**: Tests timeout
- **Solution**: Use `@pytest.mark.slow` and run with `--timeout=300`

**Issue**: Coverage too low
- **Solution**: Add more tests or adjust threshold in `.coveragerc`

**Issue**: Parallel tests fail
- **Solution**: Ensure tests are independent, use fixtures properly

**Issue**: Security scan fails in CI
- **Solution**: Review security report, update dependencies, fix code issues

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest documentation](https://docs.python.org/3/library/unittest.html)
- [GitHub Actions documentation](https://docs.github.com/en/actions)

---

## Questions or Issues?

- Check existing test files for examples
- Review this guide for best practices
- Create an issue on GitHub for help
- Check CI/CD workflow logs for detailed error messages
