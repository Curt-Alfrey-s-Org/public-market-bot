# Environment Configuration Conflict Checker Guide

## Overview

The Environment Configuration Conflict Checker is a utility that automatically detects and resolves conflicting or problematic settings in your `.env` file. It helps ensure your trading bot configuration is safe, consistent, and follows best practices.

## Features

- **Automatic Conflict Detection**: Identifies conflicting environment variable settings
- **Severity Levels**: Categorizes issues as ERROR, WARNING, or INFO
- **Clear Explanations**: Provides detailed descriptions of each conflict
- **Actionable Suggestions**: Offers specific recommendations to fix issues
- **Sanitized Configuration**: Can generate a corrected `.env` file automatically

## Types of Conflicts Detected

### 1. Obsolete Settings

**ENABLE_PDT_RULES is obsolete**
- **Issue**: The `ENABLE_PDT_RULES` setting no longer controls PDT enforcement
- **Explanation**: PDT rules are automatically determined by `PAPER_TRADING_MODE` (disabled in paper mode, enabled in live mode)
- **Severity**: WARNING
- **Fix**: Remove `ENABLE_PDT_RULES` from your .env file

### 2. Mode Configuration Conflicts

**Live Mode with API Disabled**
- **Issue**: `PAPER_TRADING_MODE=false` with `SCHWAB_API_ENABLED=off`
- **Explanation**: Live trading requires Schwab API connectivity
- **Severity**: ERROR
- **Fix**: Set `SCHWAB_API_ENABLED=on` for live trading, or set `PAPER_TRADING_MODE=true` for simulation

**Sandbox Mode with API Disabled**
- **Issue**: `SCHWAB_SANDBOX_MODE=true` with `SCHWAB_API_ENABLED=off`
- **Explanation**: Sandbox mode requires API to be enabled
- **Severity**: WARNING
- **Fix**: Set `SCHWAB_API_ENABLED=on` or set `SCHWAB_SANDBOX_MODE=false`

**Redundant Configuration**
- **Issue**: Both `SCHWAB_SANDBOX_MODE=false` and `SCHWAB_API_ENABLED=off` are set
- **Explanation**: When API is disabled, sandbox mode setting has no effect
- **Severity**: INFO
- **Fix**: Remove `SCHWAB_SANDBOX_MODE` when `SCHWAB_API_ENABLED=off`

### 3. Non-Interactive Mode Issues

**Non-Interactive Without Token**
- **Issue**: `NON_INTERACTIVE=true` with `SCHWAB_API_ENABLED=on` but no `token.json` file
- **Explanation**: Bot will fall back to yfinance simulation mode
- **Severity**: WARNING
- **Fix**: Either:
  1. Run bot interactively first to generate token.json
  2. Set `SCHWAB_API_ENABLED=off` to explicitly use yfinance
  3. Set `NON_INTERACTIVE=false` if you can run interactively

### 4. Risk Parameter Conflicts

**High Stop Loss Percentage**
- **Issue**: `BOT_STOP_LOSS_PERCENT` > 10% (e.g., 20%)
- **Explanation**: Most trading strategies use 5-10% stop losses
- **Severity**: WARNING
- **Fix**: Consider reducing to 0.06 (6%) or lower

**High Take Profit Percentage**
- **Issue**: `BOT_TAKE_PROFIT_PERCENT` > 20% (e.g., 50%)
- **Explanation**: High targets may cause you to miss profit-taking opportunities
- **Severity**: WARNING
- **Fix**: Consider reducing to 0.10 (10%) or lower

**Position Size vs Risk Threshold Mismatch**
- **Issue**: `BOT_POSITION_SIZE` is much larger than `BOT_RISK_THRESHOLD`
- **Explanation**: This may lead to oversized positions
- **Severity**: WARNING
- **Fix**: Align these values - typically position_size should match or be close to risk_threshold

## Usage

### Running the Conflict Checker

#### As a Standalone Tool

```bash
# Check your current environment
python3 env_conflict_checker.py
```

This will:
1. Load your `.env` file (if it exists)
2. Check for conflicts
3. Display a detailed report
4. Optionally generate a sanitized `.env` file

#### Integrated with Bot Startup

The conflict checker runs automatically when you start the bot via `validate_configuration()` in `main.py`. Warnings are logged but don't prevent bot startup - only ERRORS block startup.

### Generating a Sanitized Configuration

#### Interactive Method

```bash
python3 env_conflict_checker.py
# Follow prompts to generate .env.sanitized
```

#### Programmatic Method

```python
from env_conflict_checker import write_sanitized_env

write_sanitized_env('.env.sanitized')
```

#### Review and Apply

```bash
# Review the sanitized file
cat .env.sanitized

# If acceptable, replace your current .env
cp .env .env.backup  # Backup first
mv .env.sanitized .env
```

## Example Conflict Report

```
======================================================================
ENVIRONMENT CONFIGURATION CONFLICT REPORT
======================================================================

🔴 ERRORS (1) - Must be fixed:
----------------------------------------------------------------------

1. Invalid Live Trading Configuration
   Variables: PAPER_TRADING_MODE, SCHWAB_API_ENABLED
   Issue: Cannot run in live mode with Schwab API disabled.
   ⚠️  Fix: Set SCHWAB_API_ENABLED=on or PAPER_TRADING_MODE=true

⚠️  WARNINGS (2) - Should be addressed:
----------------------------------------------------------------------

1. High Stop Loss Percentage
   Variables: BOT_STOP_LOSS_PERCENT
   Issue: BOT_STOP_LOSS_PERCENT=20% is unusually high.
   💡 Suggestion: Consider reducing to 0.06 (6%) or lower

2. Obsolete PDT Rules Setting
   Variables: ENABLE_PDT_RULES, PAPER_TRADING_MODE
   Issue: ENABLE_PDT_RULES has no effect in paper trading mode.
   💡 Suggestion: Remove ENABLE_PDT_RULES from .env

ℹ️  INFO (1) - Informational:
----------------------------------------------------------------------

1. Redundant Configuration
   Variables: SCHWAB_SANDBOX_MODE, SCHWAB_API_ENABLED
   Note: When API is disabled, sandbox mode setting is irrelevant.
   💡 Tip: Remove SCHWAB_SANDBOX_MODE when SCHWAB_API_ENABLED=off

======================================================================
Total issues: 1 errors, 2 warnings, 1 info
======================================================================
```

## What the Sanitizer Does

The sanitized configuration generator:

1. **Removes obsolete settings**
   - `ENABLE_PDT_RULES` is removed (determined by `PAPER_TRADING_MODE`)

2. **Resolves mode conflicts**
   - If `SCHWAB_API_ENABLED=off`, forces `PAPER_TRADING_MODE=true` and `SCHWAB_SANDBOX_MODE=false`
   - Ensures live mode always has API enabled

3. **Adjusts risky parameters**
   - Caps `BOT_STOP_LOSS_PERCENT` at 10% (6% recommended)
   - Caps `BOT_TAKE_PROFIT_PERCENT` at 20% (10% recommended)

4. **Aligns related settings**
   - Sets `BOT_POSITION_SIZE` to match `BOT_RISK_THRESHOLD`

5. **Preserves safe settings**
   - All other configuration values are kept as-is

## Best Practices

### Recommended Configuration Patterns

#### Training/Development Mode (No API)
```bash
PAPER_TRADING_MODE=true
SCHWAB_API_ENABLED=off
SCHWAB_SANDBOX_MODE=false  # Optional, has no effect

BOT_RISK_THRESHOLD=0.02
BOT_POSITION_SIZE=0.02
BOT_STOP_LOSS_PERCENT=0.06
BOT_TAKE_PROFIT_PERCENT=0.10
```

#### Sandbox Testing Mode (With API)
```bash
PAPER_TRADING_MODE=true
SCHWAB_API_ENABLED=on
SCHWAB_SANDBOX_MODE=true

BOT_RISK_THRESHOLD=0.02
BOT_POSITION_SIZE=0.02
BOT_STOP_LOSS_PERCENT=0.06
BOT_TAKE_PROFIT_PERCENT=0.10
```

#### Live Trading Mode
```bash
PAPER_TRADING_MODE=false
SCHWAB_API_ENABLED=on
SCHWAB_SANDBOX_MODE=false  # Ignored in live mode

BOT_RISK_THRESHOLD=0.02
BOT_POSITION_SIZE=0.02
BOT_STOP_LOSS_PERCENT=0.06
BOT_TAKE_PROFIT_PERCENT=0.10
```

### Risk Parameter Guidelines

| Parameter | Recommended Range | Description |
|-----------|------------------|-------------|
| `BOT_RISK_THRESHOLD` | 0.01 - 0.03 (1-3%) | Maximum risk per trade |
| `BOT_POSITION_SIZE` | Same as risk threshold | Position size as % of capital |
| `BOT_STOP_LOSS_PERCENT` | 0.05 - 0.10 (5-10%) | Stop loss percentage |
| `BOT_TAKE_PROFIT_PERCENT` | 0.08 - 0.15 (8-15%) | Take profit percentage |
| `BOT_TRAILING_STOP_PERCENT` | 0.02 - 0.05 (2-5%) | Trailing stop percentage |

### Settings to Remove

These settings are no longer used and should be removed from your `.env`:

- ❌ `ENABLE_PDT_RULES` - Replaced by `PAPER_TRADING_MODE`

## Integration with Existing Workflow

### 1. Initial Setup
```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env

# Check for conflicts
python3 env_conflict_checker.py

# Apply sanitized version if needed
mv .env.sanitized .env
```

### 2. Before Starting Bot
```bash
# Run conflict check
python3 env_conflict_checker.py

# Review any warnings or errors
# Fix critical issues

# Start bot
./start_web_gui.sh
```

### 3. After Modifying Configuration
```bash
# Check for new conflicts
python3 env_conflict_checker.py

# Generate sanitized version
python3 -c "from env_conflict_checker import write_sanitized_env; write_sanitized_env()"

# Review and apply if needed
```

## Troubleshooting

### "Module not found" Error
```bash
# Ensure you're in the bot directory
cd /path/to/market-pie5-bot

# Run with full path
python3 /path/to/market-pie5-bot/env_conflict_checker.py
```

### Conflicts Not Detected
- Ensure `.env` file exists in the current directory
- Check that environment variables are properly formatted (KEY=value)
- Verify no extra spaces around `=` signs

### Sanitized File Not Generated
- Check write permissions in the current directory
- Ensure the script runs to completion
- Look for error messages in the output

## API Reference

### Main Functions

#### `check_env_conflicts() -> List[EnvConflict]`
Checks environment for conflicts and returns a list of issues.

#### `print_conflict_report(conflicts: List[EnvConflict]) -> None`
Prints a formatted report of detected conflicts.

#### `create_sanitized_env() -> Dict[str, str]`
Creates a dictionary of sanitized environment variables.

#### `write_sanitized_env(output_path: str = '.env.sanitized') -> None`
Writes sanitized configuration to a file.

### EnvConflict Class

```python
class EnvConflict:
    severity: str        # 'ERROR', 'WARNING', or 'INFO'
    title: str          # Brief conflict title
    description: str    # Detailed explanation
    affected_vars: List[str]  # Environment variables involved
    suggestion: str     # Recommendation to fix
```

## Support

If you encounter issues with the conflict checker:

1. Check the [GitHub Issues](https://github.com/operator/market-pie5-bot/issues) page
2. Review the [README.md](README.md) for general configuration guidance
3. See [CONTRIBUTING.md](CONTRIBUTING.md) for reporting bugs

## Changelog

### Version 1.0 (2025-01-20)
- Initial release
- Detects 8 types of configuration conflicts
- Generates sanitized configuration files
- Integrates with main bot validation
- Comprehensive test suite
