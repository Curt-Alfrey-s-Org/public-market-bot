#!/usr/bin/env python3
"""Quick test for error log fixes"""

import os
import sys
from unittest.mock import patch

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Test 1: _strategy_manager initialization
print("=" * 60)
print("Test 1: _strategy_manager initialization")
print("=" * 60)

from main import TradingBot

bot = TradingBot()
has_strategy_manager = hasattr(bot, '_strategy_manager')
print(f"✓ Bot has '_strategy_manager' attribute: {has_strategy_manager}")
if not has_strategy_manager:
    print("✗ FAILED: _strategy_manager not initialized")
    sys.exit(1)
print()

# Test 2: Trade mode detection with yfinance_sim flag
print("=" * 60)
print("Test 2: Trade mode detection (yfinance_sim)")
print("=" * 60)

import main as main_module

bot2 = TradingBot(total_capital=10000.0)
bot2.using_yfinance_sim = True
bot2.positions = {}
bot2.trade_history = []

# Patch _get_schwab_api_enabled to return True (so it doesn't use 'api_disabled' mode)
with patch.object(main_module, '_get_schwab_api_enabled', return_value=True):
    result = bot2.execute_trade('AAPL', 'BUY', 45.0, volume=500_000)

print(f"Trade executed: {result}")
print(f"Trades recorded: {len(bot2.trade_history)}")

if len(bot2.trade_history) > 0:
    trade = bot2.trade_history[-1]
    mode = trade.get('mode')
    print(f"Trade mode: {mode}")
    
    if mode == 'yfinance_sim':
        print("✓ PASS: Trade recorded with mode='yfinance_sim'")
    else:
        print(f"✗ FAILED: Expected mode='yfinance_sim', got mode='{mode}'")
        sys.exit(1)
else:
    print("✗ FAILED: No trades recorded")
    sys.exit(1)

print()
print("=" * 60)
print("All tests PASSED!")
print("=" * 60)
