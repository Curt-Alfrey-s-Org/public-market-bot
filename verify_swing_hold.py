#!/usr/bin/env python3
"""
Manual verification script for swing hold enforcement.
Demonstrates that the feature works correctly in simulation mode.
"""

import os
from datetime import datetime, timedelta

# Set test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SWING_MIN_HOLD_DAYS'] = '1'
os.environ['ENABLE_PDT_RULES'] = 'false'

import main as main_module

def test_swing_hold_enforcement():
    """Manually test the swing hold enforcement feature"""
    
    print("=" * 70)
    print("SWING HOLD ENFORCEMENT - MANUAL VERIFICATION")
    print("=" * 70)
    
    # Create bot
    bot = main_module.TradingBot(total_capital=10000.0)
    print(f"\n✓ Created bot with $10,000 capital")
    print(f"✓ SWING_MIN_HOLD_DAYS = {os.getenv('SWING_MIN_HOLD_DAYS')}")
    
    # Test 1: Open a position
    print("\n" + "-" * 70)
    print("TEST 1: Opening a position")
    print("-" * 70)
    symbol = 'AAPL'
    bot.open_position(symbol, 150.0, 10.0)
    print(f"✓ Opened position: {symbol} @ $150.00, quantity=10.0")
    entry_time = bot.positions[symbol]['entry_time']
    print(f"✓ Entry time recorded: {entry_time}")
    
    # Test 2: Try to sell immediately (should be blocked)
    print("\n" + "-" * 70)
    print("TEST 2: Attempting immediate sell (should be blocked)")
    print("-" * 70)
    can_sell, msg = bot.check_holding_period(symbol, 'SELL')
    if not can_sell:
        print(f"✓ BLOCKED: {msg}")
    else:
        print(f"✗ ERROR: Sell was allowed but should be blocked!")
        print(f"  Message: {msg}")
        return False
    
    # Test 3: Simulate 25 hours passing
    print("\n" + "-" * 70)
    print("TEST 3: Simulating 25 hours passing")
    print("-" * 70)
    past_time = (datetime.now() - timedelta(hours=25)).isoformat()
    bot.positions[symbol]['entry_time'] = past_time
    print(f"✓ Updated entry time to 25 hours ago: {past_time}")
    
    # Test 4: Try to sell after 25 hours (should be allowed)
    print("\n" + "-" * 70)
    print("TEST 4: Attempting sell after 25 hours (should be allowed)")
    print("-" * 70)
    can_sell, msg = bot.check_holding_period(symbol, 'SELL')
    if can_sell:
        print(f"✓ ALLOWED: {msg}")
    else:
        print(f"✗ ERROR: Sell was blocked but should be allowed!")
        print(f"  Message: {msg}")
        return False
    
    # Test 5: Test with SWING_MIN_HOLD_DAYS=0
    print("\n" + "-" * 70)
    print("TEST 5: Testing with SWING_MIN_HOLD_DAYS=0")
    print("-" * 70)
    os.environ['SWING_MIN_HOLD_DAYS'] = '0'
    # Reimport to get new value
    import importlib
    importlib.reload(main_module)
    bot2 = main_module.TradingBot(total_capital=10000.0)
    bot2.open_position('MSFT', 300.0, 5.0)
    print(f"✓ Opened position: MSFT @ $300.00, quantity=5.0")
    can_sell, msg = bot2.check_holding_period('MSFT', 'SELL')
    if can_sell:
        print(f"✓ ALLOWED (SWING_MIN_HOLD_DAYS=0): {msg}")
    else:
        print(f"✗ ERROR: Sell was blocked with SWING_MIN_HOLD_DAYS=0!")
        print(f"  Message: {msg}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - SWING HOLD ENFORCEMENT WORKING CORRECTLY")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = test_swing_hold_enforcement()
    exit(0 if success else 1)
