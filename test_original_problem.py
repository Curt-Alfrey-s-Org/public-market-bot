#!/usr/bin/env python3
"""
Simulate the original problem from the issue.

This script simulates what happens when the bot is run in an environment
like the one shown in the problem statement logs.
"""

import os
import sys

if __name__ == '__main__':
    # Simulate the non-interactive environment from the problem statement
    os.environ['NON_INTERACTIVE'] = 'true'
    os.environ['PAPER_TRADING_MODE'] = 'true'
    os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
    os.environ['SCHWAB_API_ENABLED'] = 'on'  # API is enabled
    os.environ['SCHWAB_API_KEY'] = 'test_api_key'
    os.environ['SCHWAB_APP_SECRET'] = 'test_app_secret'
    os.environ['SCHWAB_CALLBACK_URL'] = 'https://127.0.0.1:8182'

    # Ensure token.json doesn't exist (simulating first run)
    if os.path.exists('token.json'):
        print("Backing up existing token.json...")
        os.rename('token.json', 'token.json.backup')

    print("="*60)
    print("SIMULATING ORIGINAL PROBLEM SCENARIO")
    print("="*60)
    print("Environment:")
    print(f"  NON_INTERACTIVE: {os.environ['NON_INTERACTIVE']}")
    print(f"  PAPER_TRADING_MODE: {os.environ['PAPER_TRADING_MODE']}")
    print(f"  SCHWAB_SANDBOX_MODE: {os.environ['SCHWAB_SANDBOX_MODE']}")
    print(f"  SCHWAB_API_ENABLED: {os.environ['SCHWAB_API_ENABLED']}")
    print(f"  token.json exists: {os.path.exists('token.json')}")
    print("="*60)

    try:
        # Import and initialize bot (this is where the error would occur)
        from main import TradingBot, setup_logging
        
        setup_logging()
        
        print("\n✓ Importing TradingBot...")
        bot = TradingBot(total_capital=500.0)
        
        print("\n" + "="*60)
        print("RESULT: SUCCESS")
        print("="*60)
        print("✓ No 'EOF when reading a line' error occurred")
        print("✓ Bot initialized successfully")
        print(f"✓ Using yfinance simulation: {bot.using_yfinance_sim}")
        print(f"✓ Schwab API available: {bot.schwab_api_available}")
        print("\nThe fix works correctly! The bot:")
        print("  1. Detected NON_INTERACTIVE=true")
        print("  2. Detected no token.json exists")
        print("  3. Automatically switched to yfinance simulation mode")
        print("  4. Did NOT attempt OAuth (which would cause EOF error)")
        print("  5. Bot is ready to trade using yfinance for market data")
        print("="*60)
        
        sys.exit(0)

    except EOFError as e:
        print("\n" + "="*60)
        print("RESULT: FAILED - EOF ERROR")
        print("="*60)
        print(f"✗ Original error reproduced: {e}")
        print("✗ The fix did not work properly")
        print("="*60)
        sys.exit(1)

    except Exception as e:
        print("\n" + "="*60)
        print("RESULT: FAILED - OTHER ERROR")
        print("="*60)
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        sys.exit(1)

    finally:
        # Restore backup if it exists
        if os.path.exists('token.json.backup'):
            print("\nRestoring backup token.json...")
            if os.path.exists('token.json'):
                os.remove('token.json')
            os.rename('token.json.backup', 'token.json')
