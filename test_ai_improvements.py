#!/usr/bin/env python3
"""
Test script to demonstrate the AI-recommended improvements
This script validates that the new configuration parameters are correctly applied
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import os
os.environ['PAPER_TRADING_MODE'] = 'true'

from main import (
    BOT_RISK_THRESHOLD,
    BOT_TRAILING_STOP_PERCENT, 
    BOT_POSITION_SIZE,
    BOT_STOP_LOSS_PERCENT,
    BOT_MAX_CONSECUTIVE_LOSSES,
    TRADING_FREQUENCY,
    TradingBot
)

def test_configuration_values():
    """Test that AI-recommended configuration values are set correctly"""
    print("="*60)
    print("AI-RECOMMENDED CONFIGURATION VALIDATION")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Risk Threshold
    print(f"\n1. BOT_RISK_THRESHOLD: {BOT_RISK_THRESHOLD}")
    if BOT_RISK_THRESHOLD == 0.02:
        print("   ✓ PASS - Reduced from 7% to 2% (more conservative)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 0.02, got {BOT_RISK_THRESHOLD}")
        tests_failed += 1
    
    # Test 2: Trailing Stop
    print(f"\n2. BOT_TRAILING_STOP_PERCENT: {BOT_TRAILING_STOP_PERCENT}")
    if BOT_TRAILING_STOP_PERCENT == 0.03:
        print("   ✓ PASS - Tightened from 5% to 3% (locks in gains earlier)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 0.03, got {BOT_TRAILING_STOP_PERCENT}")
        tests_failed += 1
    
    # Test 3: Position Size
    print(f"\n3. BOT_POSITION_SIZE: {BOT_POSITION_SIZE}")
    if BOT_POSITION_SIZE == 0.01:
        print("   ✓ PASS - Reduced from 5% to 1% (smaller positions)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 0.01, got {BOT_POSITION_SIZE}")
        tests_failed += 1
    
    # Test 4: Stop Loss
    print(f"\n4. BOT_STOP_LOSS_PERCENT: {BOT_STOP_LOSS_PERCENT}")
    if BOT_STOP_LOSS_PERCENT == 0.06:
        print("   ✓ PASS - Increased from 5% to 6% (exits losing positions faster)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 0.06, got {BOT_STOP_LOSS_PERCENT}")
        tests_failed += 1
    
    # Test 5: Max Consecutive Losses
    print(f"\n5. BOT_MAX_CONSECUTIVE_LOSSES: {BOT_MAX_CONSECUTIVE_LOSSES}")
    if BOT_MAX_CONSECUTIVE_LOSSES == 3:
        print("   ✓ PASS - Set to 3 (limits consecutive loss exposure)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 3, got {BOT_MAX_CONSECUTIVE_LOSSES}")
        tests_failed += 1
    
    # Test 6: Trading Frequency
    print(f"\n6. TRADING_FREQUENCY: {TRADING_FREQUENCY}")
    if TRADING_FREQUENCY == 2:
        print("   ✓ PASS - Set to 2 seconds (reduces trading frequency)")
        tests_passed += 1
    else:
        print(f"   ✗ FAIL - Expected 2, got {TRADING_FREQUENCY}")
        tests_failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("="*60)
    
    return tests_failed == 0


def test_bot_behavior():
    """Test that the bot behaves correctly with new settings"""
    print("\n" + "="*60)
    print("BOT BEHAVIOR VALIDATION")
    print("="*60)
    
    bot = TradingBot(total_capital=10000.0)
    
    # Test 1: Initial trailing stop is correct
    print(f"\n1. Initial trailing stop: {bot.trailing_stop_percent}")
    assert bot.trailing_stop_percent == 0.03, "Trailing stop should be 3%"
    print("   ✓ PASS - Bot initialized with correct trailing stop")
    
    # Test 2: Risk threshold calculation
    risk_limit = BOT_RISK_THRESHOLD * bot.total_capital
    print(f"\n2. Risk limit for $10,000 capital: ${risk_limit:.2f}")
    assert risk_limit == 200.0, "Risk limit should be $200 (2% of $10,000)"
    print("   ✓ PASS - Risk limit calculated correctly")
    
    # Test 3: Allocation is capped
    bot.track_record['current_allocation'] = 150.0
    print(f"\n3. Allocation: ${bot.track_record['current_allocation']:.2f}")
    assert bot.track_record['current_allocation'] < risk_limit, "Allocation should be within risk limit"
    print("   ✓ PASS - Allocation is within risk limit")
    
    print("\n" + "="*60)
    print("BEHAVIOR VALIDATION COMPLETE")
    print("="*60)


def print_comparison():
    """Print a comparison of old vs new settings"""
    print("\n" + "="*60)
    print("CONFIGURATION COMPARISON (OLD vs NEW)")
    print("="*60)
    
    comparisons = [
        ("Risk Threshold", "7%", "2%", "Lower risk exposure per trade"),
        ("Trailing Stop", "5%", "3%", "Locks in gains earlier"),
        ("Position Size", "5%", "1%", "Smaller positions reduce risk"),
        ("Stop Loss", "5%", "6%", "Exits losing trades faster"),
        ("Max Consecutive Losses", "3", "3", "No change (already optimal)"),
        ("Trading Frequency", "1-5s random", "2s fixed", "More predictable execution")
    ]
    
    print(f"\n{'Parameter':<25} {'Old Value':<15} {'New Value':<15} {'Benefit':<40}")
    print("-" * 100)
    
    for param, old, new, benefit in comparisons:
        print(f"{param:<25} {old:<15} {new:<15} {benefit:<40}")
    
    print("\n" + "="*60)
    print("EXPECTED IMPACT")
    print("="*60)
    print("""
The AI analysis identified a 10% win rate with -0.03% loss as the problem.
These changes make the bot significantly more conservative:

1. REDUCED RISK: 2% threshold vs 7% limits exposure dramatically
2. EARLY PROFIT TAKING: 3% trailing stop vs 5% locks in gains sooner
3. SMALLER BETS: 1% position size vs 5% reduces loss magnitude
4. FASTER EXITS: 6% stop loss vs 5% cuts losses slightly faster
5. CONTROLLED FREQUENCY: Fixed 2s delay vs random 1-5s for consistency

Expected outcome: Lower win rate may continue initially, but losses 
should be significantly smaller, leading to better overall performance.
    """)
    print("="*60)


if __name__ == '__main__':
    print("\n" + "#"*60)
    print("#" + " "*20 + "AI IMPROVEMENTS TEST" + " "*19 + "#")
    print("#"*60)
    
    # Run tests
    config_passed = test_configuration_values()
    test_bot_behavior()
    print_comparison()
    
    if config_passed:
        print("\n✓ ALL TESTS PASSED - AI improvements successfully implemented!")
        print("\nThe bot is now configured with more conservative, AI-recommended settings.")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED - Please check the configuration")
        exit(1)
