#!/usr/bin/env python3
"""Test bot initialization in yfinance mode"""

import os
import sys

# Set yfinance mode
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['WEB_GUI_DEBUG'] = 'true'

# Change to repo directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Bot Initialization in yfinance Mode")
print("=" * 60)
print()

try:
    print("[1] Importing TradingBot...")
    from main import TradingBot
    print("✓ Import successful")
    print()
    
    print("[2] Initializing bot with $10,000 capital...")
    bot = TradingBot(total_capital=10000.0)
    print("✓ Bot initialization successful")
    print()
    
    print("[3] Checking attributes...")
    has_strategy_manager = hasattr(bot, '_strategy_manager')
    has_positions = hasattr(bot, 'positions')
    has_trade_history = hasattr(bot, 'trade_history')
    has_running = hasattr(bot, 'running')
    
    print(f"  - _strategy_manager: {has_strategy_manager}")
    print(f"  - positions: {has_positions}")
    print(f"  - trade_history: {has_trade_history}")
    print(f"  - running: {has_running}")
    
    if all([has_strategy_manager, has_positions, has_trade_history]):
        print("✓ All required attributes present")
    else:
        print("✗ Missing attributes!")
        sys.exit(1)
    print()
    
    print("[4] Setting bot.running = True...")
    bot.running = True
    print("✓ Successfully set running flag")
    print()
    
    print("[5] Checking bot state...")
    print(f"  - Capital: ${bot.total_capital:.2f}")
    print(f"  - Mode: {getattr(bot, 'mode', 'NOT SET')}")
    print(f"  - Running: {getattr(bot, 'running', False)}")
    print(f"  - Using yfinance sim: {getattr(bot, 'using_yfinance_sim', False)}")
    print()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED - Bot can be initialized")
    print("=" * 60)
    
except Exception as e:
    print()
    print("=" * 60)
    print("✗ INITIALIZATION FAILED")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
