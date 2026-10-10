#!/usr/bin/env python3
"""
Generate Sanitized Environment Configuration

This script demonstrates how to use the env_conflict_checker module to detect
configuration conflicts and generate a sanitized .env file with safe defaults.
It sets up a test environment with user-provided values and runs the conflict
checker to identify potential issues.

Usage:
    python3 generate_sanitized.py

Output:
    - Prints detected configuration conflicts to console
    - Generates .env.sanitized file with resolved conflicts
"""
import os

# Set user's environment
os.environ['NON_INTERACTIVE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['BOT_TOTAL_CAPITAL'] = '10000'
os.environ['BOT_RISK_THRESHOLD'] = '0.049'
os.environ['BOT_MIN_ALLOCATION'] = '100'
os.environ['BOT_MAX_ALLOCATION'] = '300'
os.environ['BOT_TRAILING_STOP_PERCENT'] = '0.1'
os.environ['BOT_MAX_OPEN_POSITIONS'] = '6'
os.environ['BOT_MAX_CONSECUTIVE_LOSSES'] = '3'
os.environ['BOT_POSITION_SIZE'] = '0.03'
os.environ['BOT_STOP_LOSS_PERCENT'] = '0.2'
os.environ['BOT_TAKE_PROFIT_PERCENT'] = '0.5'
os.environ['BOT_RISK_FREE_RATE'] = '0.01'
os.environ['TRADING_FREQUENCY'] = '3'
os.environ['DYNAMIC_STOP_ENABLED'] = 'true'
os.environ['VOLATILITY_WINDOW'] = '19'
os.environ['MIN_TRAILING_STOP'] = '0.1'
os.environ['MAX_TRAILING_STOP'] = '0.2'
os.environ['MIN_STOCK_PRICE'] = '1'
os.environ['MAX_STOCK_PRICE'] = '60'
os.environ['MIN_DAILY_VOLUME'] = '500000'
os.environ['MAX_STOCK_VOLATILITY'] = '0.15'
os.environ['PARTIAL_EXIT_ENABLED'] = 'true'
os.environ['PARTIAL_EXIT_PERCENTAGE'] = '0.25'
os.environ['SIMULATED_WIN_RATE'] = '0.7'
os.environ['VOLATILITY_NORMALIZATION_MIN'] = '0.01'
os.environ['VOLATILITY_NORMALIZATION_RANGE'] = '0.19'
os.environ['CAPITAL_FLOOR_PERCENT'] = '0.1'
os.environ['ENABLE_PDT_RULES'] = 'true'
os.environ['ENABLE_ALERTS'] = 'true'
os.environ['ALERT_EMAIL'] = 'operator@example.com'
os.environ['WEB_GUI_MAX_SYMBOLS'] = '10'
os.environ['WEB_GUI_CONTINUOUS_TRADING'] = 'true'
os.environ['WEB_GUI_CYCLE_DELAY'] = '3'
os.environ['WEB_GUI_DEBUG'] = 'false'
os.environ['USER_PROFILE_NAME'] = 'Bender'
os.environ['USER_PROFILE_USERNAME'] = '@trader'
os.environ['BOT_MAX_CPU_PERCENT'] = '75'
os.environ['BOT_MAX_MEMORY_PERCENT'] = '75'
os.environ['BOT_THROTTLE_DELAY'] = '10'
os.environ['BOT_ENABLE_THROTTLING'] = 'true'
os.environ['SENTIMENT_METHOD'] = 'vader'

from env_conflict_checker import write_sanitized_env, check_env_conflicts, print_conflict_report

# Show conflicts
conflicts = check_env_conflicts()
print_conflict_report(conflicts)

# Generate sanitized file
write_sanitized_env('.env.sanitized')
