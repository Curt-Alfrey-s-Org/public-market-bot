# GitHub Copilot Instructions for market-pie5-bot

## Current task for Copilot

**See [.github/COPILOT_TASK.md](.github/COPILOT_TASK.md)** for the current scoped task. Create branch `copilot/<task-slug>`, implement, run tests, open a PR. When finished, add the `copilot-completed` label so Copilot Sentinel passes.

### Completion Signals & Label Gate (Copilot PRs)

- **Auto-label:** Copilot PRs (branches starting with `copilot/`) are auto-labeled `copilot-completed` when all checks pass.
- **Gate behavior:** A label gate requires `copilot-completed`; it re-checks when labels change and passes automatically.
- **Manual fallback:** If needed, add the label via the PR sidebar (Labels → `copilot-completed`).

### Workflow for Copilot tasks

1. Read this file for project conventions; open **COPILOT_TASK.md** for task details, branch name, and acceptance criteria.
2. Create the branch: `git checkout -b <branch-name>` (e.g. `copilot/add-dryrun-live-mode-tests`).
3. Implement, run tests, open a PR, then add the **`copilot-completed`** label.

### Branch naming

- `copilot/<short-description>` (e.g. `copilot/add-feature`, `copilot/update-docs`).

---

## Project Overview

**market-pie5-bot** is an intelligent, self-scaling trading bot optimized for Raspberry Pi 5 with AI-powered strategy optimization, paper trading, PDT compliance, and comprehensive GUI.

### Key Technologies
- **Primary Language**: Python 3.10+
- **Web Framework**: Dash (Plotly) for web GUI
- **Desktop GUI**: Tkinter
- **Trading APIs**: Schwab API (via schwab-py), yfinance, Alpha Vantage
- **ML/AI**: scikit-learn, HuggingFace API
- **Data Analysis**: pandas, numpy, backtrader
- **Frontend Enhancement**: Node.js packages (Chart.js, Font Awesome, animate.css)

### Project Structure
```
market-pie5-bot/
├── main.py                     # Core trading bot logic
├── web_gui.py                  # Dash-based web interface
├── gui.py                      # Tkinter desktop interface
├── strategies.py               # Trading strategies (SMA, RSI, MACD, etc.)
├── indicators.py               # Technical indicators
├── risk_management.py          # Position sizing and risk calculations
├── portfolio_optimizer.py      # Modern Portfolio Theory implementation
├── sentiment_analyzer.py       # News sentiment analysis
├── schwab_auth.py             # Schwab OAuth authentication
├── log_manager.py             # Centralized logging system
├── report_generator.py        # Performance analytics and reports
├── backtesting.py             # Backtesting engine
├── backtrader_engine.py       # Backtrader integration
├── ml_signal_filter.py        # Machine learning signal filtering
├── test_*.py                  # Test suites
├── assets/                    # Web GUI assets (CSS, images)
├── .env.example               # Environment variables template
└── requirements.txt           # Python dependencies
```

## Development Workflow

### Build and Setup Commands

**Initial Setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Install Python dependencies
./venv/bin/pip install -r requirements.txt

# Install Node.js dependencies (optional, for web GUI enhancements)
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

**Quick Start:**
```bash
# Start web GUI (recommended)
./start_web_gui.sh

# Start desktop GUI (alternative)
./start_bot.sh

# Run bot in CLI mode
./venv/bin/python3 main.py
```

### Testing Commands

**Run Tests:**
```bash
# Run all tests
pytest test_*.py -v --tb=short

# Run specific test file
pytest test_trading_bot.py -v

# Run with coverage
pytest test_*.py -v --cov=. --cov-report=term-missing

# Run specific test suite
python3 -m unittest test_new_features -v
python3 -m unittest test_gui_features -v
```

**Test Environment Variables:**
When running tests, always set:
```bash
export ENABLE_PDT_RULES='false'
export PAPER_TRADING_MODE='true'
export SCHWAB_SANDBOX_MODE='true'
```

### Linting and Code Quality

**Linting:**
```bash
# Check Python syntax errors and undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Full flake8 check (warnings only)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=venv,node_modules,.git,__pycache__

# Check code formatting
black --check --diff . --exclude="venv|node_modules|\.git"

# Check import sorting
isort --check-only --diff . --skip venv --skip node_modules --skip .git

# Run pylint
pylint *.py --exit-zero --ignore=venv,node_modules,.git,test_*.py --max-line-length=127
```

**Auto-fix Formatting:**
```bash
# Format code with black
black . --exclude="venv|node_modules|\.git"

# Sort imports with isort
isort . --skip venv --skip node_modules --skip .git
```

### Git Workflow

**Branch Naming:**
- Feature branches: `feature/<ticket-id>-<short-description>` or `feature/<description>`
- Bug fixes: `fix/<issue-number>-<description>` or `bugfix/<description>`
- Documentation: `docs/<description>`
- Copilot branches: `copilot/<description>`

**Commit Message Format:**
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the subject line under 72 characters
- Examples:
  - `Add sentiment analysis integration`
  - `Fix trailing stop calculation in risk management`
  - `Update web GUI with enhanced charts`

**Pull Request Guidelines:**
- Always create a PR for review, even for small changes
- Ensure all tests pass before requesting review
- Update documentation if the change affects user-facing features
- Reference related issues in PR description

## Code Style and Conventions

### Python Style Guidelines

**General:**
- Follow PEP 8 style guide
- Maximum line length: 127 characters (relaxed from PEP 8's 79)
- Use 4 spaces for indentation (never tabs)
- Use descriptive variable names (avoid single-letter names except in loops)

**Function and Class Design:**
- Keep functions focused and under 40 lines when possible
- Use type hints for function parameters and return values when applicable
- Add docstrings to all public functions and classes
- Example:
```python
def calculate_position_size(
    capital: float,
    risk_per_trade: float,
    stop_loss_percent: float
) -> float:
    """
    Calculate position size based on risk management rules.
    
    Args:
        capital: Available trading capital
        risk_per_trade: Maximum risk as decimal (e.g., 0.02 for 2%)
        stop_loss_percent: Stop loss as decimal (e.g., 0.03 for 3%)
    
    Returns:
        Position size in dollars
    """
    return (capital * risk_per_trade) / stop_loss_percent
```

**Error Handling:**
- Use specific exception types, not bare `except:`
- Log errors with appropriate context
- Example:
```python
try:
    price = fetch_stock_price(symbol)
except requests.RequestException as e:
    logger.error(f"Failed to fetch price for {symbol}: {e}")
    return None
```

**Logging:**
- Use the centralized `LogManager` class for trade logging
- Use Python's `logging` module for application logs
- Log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for non-critical issues
  - `ERROR`: Error messages for failures
  - `CRITICAL`: Critical errors that may stop the bot

**Configuration:**
- All configuration should be in `.env` file (never hardcode)
- Use `python-dotenv` to load environment variables
- Provide sensible defaults in code with `os.getenv('VAR', 'default')`
- Document all environment variables in `.env.example`

### Testing Conventions

**Test Structure:**
- Use `unittest` framework (already established in project)
- Test files must start with `test_` prefix
- Group related tests in classes that inherit from `unittest.TestCase`
- Use descriptive test method names: `test_<feature>_<scenario>`

**Test Patterns:**
```python
import unittest
from unittest.mock import patch, MagicMock

class TestTradingBot(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test."""
        self.bot = TradingBot(total_capital=10000.0)
    
    def tearDown(self):
        """Clean up after each test."""
        pass
    
    def test_execute_trade_successful_buy(self):
        """Test that BUY trades execute correctly."""
        result = self.bot.execute_trade('AAPL', 'BUY', 150.0)
        self.assertTrue(result)
        self.assertIn('AAPL', self.bot.positions)
    
    @patch('requests.get')
    def test_fetch_price_with_api_error(self, mock_get):
        """Test price fetching handles API errors gracefully."""
        mock_get.side_effect = requests.RequestException("API Error")
        price = self.bot.fetch_stock_price('AAPL')
        self.assertIsNone(price)
```

**Mocking External APIs:**
- Always mock external API calls (Schwab, yfinance, HuggingFace)
- Use `unittest.mock.patch` for mocking
- Don't make real API calls in tests (wastes resources and causes failures)

### Documentation

**When to Update Documentation:**
- New features or significant changes: Update README.md
- Breaking changes: Update CHANGELOG.md
- API changes: Update relevant guide files (e.g., WEB_GUI_GUIDE.md)
- Environment variable changes: Update .env.example

**Documentation Files:**
- `README.md`: Main project documentation, features, setup
- `CONTRIBUTING.md`: Contribution guidelines
- `CHANGELOG.md`: Version history and changes
- `*_GUIDE.md`: Specific feature guides (WEB_GUI_GUIDE.md, TRADING_ENHANCEMENTS_GUIDE.md, etc.)

## Boundaries and Restrictions

### Do NOT:

**Security:**
- ❌ Never commit `.env` files or API keys to the repository
- ❌ Never commit `token.json` (Schwab OAuth token)
- ❌ Never hardcode credentials in source code
- ❌ Never log sensitive information (API keys, tokens, passwords)

**Files to Never Modify:**
- ❌ Never edit `venv/` directory (virtual environment)
- ❌ Never edit `node_modules/` directory (npm packages)
- ❌ Never edit `.git/` directory
- ❌ Never delete or modify `.gitignore` without good reason
- ❌ Never modify `LICENSE` file

**Testing:**
- ❌ Never remove or disable existing tests without discussion
- ❌ Never skip tests in CI/CD workflows
- ❌ Never commit code that fails existing tests
- ❌ Never make real API calls in test suites

**Bot Architecture:**
- ❌ Never assume the bot is running just because the API is responding
- ⚠️ **IMPORTANT:** The FastAPI server (`uvicorn api.main:app`) and the trading bot (`main.py`) are **separate processes**
- When testing/optimizing: Always verify bot status with `GET /api/bot/status` → check `"running": true`
- If bot shows `"running": false`, the API is healthy but the bot is **not trading**
- To start bot on remote: Use `/api/bot/start` endpoint OR SSH and run `python main.py` in venv
- Without the bot running, optimizer will report 0 trades even if settings are applied correctly

**Code Quality:**
- ❌ Never ignore linting errors without justification
- ❌ Never use `pylint: disable` comments without explanation
- ❌ Never commit code with syntax errors
- ❌ Never leave commented-out code blocks (remove them)
- ❌ Never use `print()` for logging (use `logging` module)

**Trading Safety:**
- ❌ Never bypass PDT rules in production mode (regulatory requirement)
- ❌ Never disable risk management checks in live trading
- ❌ Never set `PAPER_TRADING_MODE=false` without explicit user confirmation
- ❌ Never modify capital floor protection logic

### DO:

**Best Practices:**
- ✅ Always run tests before committing
- ✅ Always update tests when changing functionality
- ✅ Always use environment variables for configuration
- ✅ Always log important operations (trades, errors, API calls)
- ✅ Always validate user input and API responses
- ✅ Always handle exceptions gracefully
- ✅ Always use type hints for function parameters
- ✅ Always add docstrings to public functions and classes
- ✅ Always format code with `black` before committing
- ✅ Always check imports with `isort` before committing

**Code Changes:**
- ✅ Keep changes small and focused
- ✅ Add tests for new features
- ✅ Update documentation for user-facing changes
- ✅ Use descriptive variable and function names
- ✅ Follow existing code patterns and conventions
- ✅ Add comments for complex logic (when necessary)

## Trading Bot Specific Guidelines

### PDT Compliance (Pattern Day Trading)
- PDT rules are **ONLY enforced in production mode** (`PAPER_TRADING_MODE=false`)
- Accounts under $25,000 are limited to 3 day trades per 5 business days
- Never bypass PDT enforcement in production (regulatory requirement)
- PDT tracking logic is in `main.py` - modifications require careful review

### Sandbox vs Production Modes

**Sandbox Mode** (`SCHWAB_SANDBOX_MODE=true`):
- Uses Schwab sandbox API endpoints
- Requires API connectivity - **NO fallback** to yfinance/random prices
- If API fails, bot must **STOP with CRITICAL ERROR**
- For realistic testing before production

**Simulation Mode** (`SCHWAB_SANDBOX_MODE=false`, `PAPER_TRADING_MODE=true`):
- Uses yfinance or random prices
- No API requirement
- Falls back gracefully when APIs unavailable
- For algorithm testing and development

**Production Mode** (`PAPER_TRADING_MODE=false`):
- Uses real money via Schwab production API
- Requires full credential validation
- Enforces PDT rules automatically
- Requires explicit user confirmation

### Risk Management
- Default risk threshold: 2% per trade (`BOT_RISK_THRESHOLD=0.02`)
- Capital floor: 10% of starting capital (bot pauses if breached)
- Trailing stop default: 3% (`BOT_TRAILING_STOP_PERCENT=0.03`)
- Never disable these protections in live trading

### API Integration
- Schwab API: OAuth 2.0 authentication via `schwab-py`
- HuggingFace API: For AI strategy optimization
- yfinance: Fallback for market data
- Alpha Vantage: Fundamental data
- Always handle API rate limits and timeouts gracefully

## Common Tasks and Patterns

### Adding a New Trading Strategy

1. Add strategy class to `strategies.py`:
```python
class NewStrategy:
    def __init__(self, params):
        self.params = params
    
    def generate_signal(self, data):
        # Implementation
        return signal  # 'BUY', 'SELL', or 'HOLD'
```

2. Add tests in `test_trading_enhancements.py`
3. Update documentation in `TRADING_ENHANCEMENTS_GUIDE.md`

### Adding a New Environment Variable

1. Add to `.env.example` with description
2. Load in code: `os.getenv('NEW_VAR', 'default_value')`
3. Document in README.md if user-facing
4. Update test fixtures to set the variable

### Adding a New Web GUI Component

1. Add component to `web_gui.py`
2. Follow existing Dash callback patterns
3. Add assets (CSS/JS) to `assets/` directory
4. Test in browser on multiple devices
5. Update `WEB_GUI_GUIDE.md` documentation

## Resources and References

- **Schwab API Documentation**: https://developer.schwab.com
- **Dash Documentation**: https://dash.plotly.com
- **Backtrader Documentation**: https://www.backtrader.com/docu/
- **Python Style Guide (PEP 8)**: https://pep8.org
- **Project Guides**: See `*_GUIDE.md` files in repository root

## Questions or Issues?

- Check existing issues: https://github.com/operator/market-pie5-bot/issues
- Review project status: `PROJECT_STATUS.md`
- Check troubleshooting: See "Troubleshooting" section in README.md
- Create new issue with:
  - Clear description
  - Steps to reproduce
  - Expected vs actual behavior
  - Relevant logs (sanitize credentials!)
  - Environment details (Python version, OS, etc.)
