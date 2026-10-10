#!/usr/bin/env python3
"""
Test script to verify error log fixes
Shows clean output when Schwab API credentials are not configured
"""

import os
import sys
import logging
from io import StringIO

if __name__ == '__main__':
    # Import the constant to ensure test stays synchronized
    from main import SCHWAB_CREDENTIAL_PLACEHOLDERS

    # Capture logging output
    log_capture = StringIO()

    # Set up logging to capture all output
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(log_capture),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set environment variables (placeholder credentials - simulating user's scenario)
    # Use the first placeholder value from the constant to ensure consistency
    os.environ['SCHWAB_API_KEY'] = SCHWAB_CREDENTIAL_PLACEHOLDERS[0]
    os.environ['SCHWAB_APP_SECRET'] = SCHWAB_CREDENTIAL_PLACEHOLDERS[1]
    os.environ['PAPER_TRADING_MODE'] = 'true'
    os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
    os.environ['SCHWAB_API_ENABLED'] = 'on'

    print('\n' + '='*80)
    print('Testing Bot with Placeholder Schwab API Credentials')
    print('='*80 + '\n')

    from main import TradingBot

    print('\n--- Initializing Bot ---\n')
    bot = TradingBot(total_capital=1000.0)

    print('\n--- Fetching Price for AAPL ---\n')
    try:
        price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
        print(f'\n✓ Successfully fetched price: ${price:.2f}, volume: {volume:,}')
    except Exception as e:
        print(f'\n✗ Error fetching price: {e}')

    print('\n' + '='*80)
    print('Analyzing Log Output')
    print('='*80 + '\n')

    # Get captured logs
    logs = log_capture.getvalue()

    # Check for problematic error messages that should NOT appear
    problematic_errors = [
        'EOF when reading a line',
        'OAuth client fetch failed',
        'Authentication failed - invalid or expired API key',
    ]

    print('Checking for problematic error messages that should NOT appear:')
    found_errors = []
    for error in problematic_errors:
        if error in logs:
            print(f'  ✗ FOUND: "{error}"')
            found_errors.append(error)
        else:
            print(f'  ✓ NOT FOUND: "{error}"')

    # Check for good informative messages that SHOULD appear
    good_messages = [
        'Schwab API credentials not configured',
        'Bot will use yfinance for market data',
    ]

    print('\nChecking for informative messages that SHOULD appear:')
    found_good = []
    for message in good_messages:
        if message in logs:
            print(f'  ✓ FOUND: "{message}"')
            found_good.append(message)
        else:
            print(f'  ✗ NOT FOUND: "{message}"')

    print('\n' + '='*80)
    print('Test Results')
    print('='*80 + '\n')

    if not found_errors and len(found_good) == len(good_messages):
        print('✓✓✓ ALL TESTS PASSED ✓✓✓')
        print('No scary error messages when credentials are not configured!')
        sys.exit(0)
    else:
        print('✗✗✗ SOME TESTS FAILED ✗✗✗')
        if found_errors:
            print(f'Found {len(found_errors)} problematic errors')
        if len(found_good) < len(good_messages):
            print(f'Missing {len(good_messages) - len(found_good)} expected informative messages')
        sys.exit(1)
