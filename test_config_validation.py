#!/usr/bin/env python3
"""
Test script to reproduce the exact dry run scenario
with the provided .env settings and verify the bug fixes.
"""

import os
import sys

# Set environment variables EXACTLY as provided in problem statement
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['BOT_RISK_THRESHOLD'] = '0.04'
os.environ['BOT_MIN_ALLOCATION'] = '500'
os.environ['BOT_MAX_ALLOCATION'] = '5000'
os.environ['BOT_TRAILING_STOP_PERCENT'] = '0.03'
os.environ['BOT_MAX_OPEN_POSITIONS'] = '50'
os.environ['BOT_MAX_CONSECUTIVE_LOSSES'] = '3'
os.environ['BOT_POSITION_SIZE'] = '0.05'
os.environ['BOT_STOP_LOSS_PERCENT'] = '0.06'
os.environ['BOT_TAKE_PROFIT_PERCENT'] = '0.1'
os.environ['BOT_RISK_FREE_RATE'] = '0.01'
os.environ['SCAN_SYMBOLS_FILE'] = 'scan_symbols.txt'
os.environ['TRADING_FREQUENCY'] = '1'
os.environ['DYNAMIC_STOP_ENABLED'] = 'True'
os.environ['VOLATILITY_WINDOW'] = '20'
os.environ['MIN_TRAILING_STOP'] = '0.02'
os.environ['MAX_TRAILING_STOP'] = '0.10'
os.environ['MIN_STOCK_PRICE'] = '1'
os.environ['MIN_DAILY_VOLUME'] = '300000'
os.environ['MAX_STOCK_VOLATILITY'] = '0.15'
os.environ['PARTIAL_EXIT_ENABLED'] = 'True'
os.environ['PARTIAL_EXIT_PERCENTAGE'] = '0.5'
os.environ['SIMULATED_WIN_RATE'] = '0.7'
os.environ['VOLATILITY_NORMALIZATION_MIN'] = '0.01'
os.environ['VOLATILITY_NORMALIZATION_RANGE'] = '0.19'
os.environ['CAPITAL_FLOOR_PERCENT'] = '0.10'
os.environ['ENABLE_ALERTS'] = 'False'
os.environ['ALERT_EMAIL'] = 'operator@example.com'

from main import validate_configuration, setup_logging

def test_configuration_validation():
    """Test that configuration validation catches the inconsistency"""
    setup_logging()
    
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION TEST")
    print("="*60)
    print("\nTesting with provided .env settings...")
    print("BOT_RISK_THRESHOLD=0.04 (4%)")
    print("BOT_MIN_ALLOCATION=500")
    print("Expected: Should catch the inconsistency")
    print("="*60 + "\n")
    
    is_valid, issues = validate_configuration()
    
    if not is_valid:
        print("\n✓ Configuration validation correctly identified issues:")
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. {issue}")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS TO FIX CONFIGURATION")
        print("="*60)
        print("\nOption 1: Increase BOT_RISK_THRESHOLD")
        print("  BOT_RISK_THRESHOLD=0.06  # Allows up to $600 risk on $10k capital")
        print("  - Pros: Allows larger position sizes, more aggressive trading")
        print("  - Cons: Higher risk per trade")
        
        print("\nOption 2: Decrease BOT_MIN_ALLOCATION")
        print("  BOT_MIN_ALLOCATION=400  # Reduces minimum position size")
        print("  - Pros: Keeps risk threshold at 4%")
        print("  - Cons: Smaller position sizes, potentially lower returns")
        
        print("\nOption 3: Balanced approach (RECOMMENDED)")
        print("  BOT_RISK_THRESHOLD=0.05  # 5% risk")
        print("  BOT_MIN_ALLOCATION=450   # $450 minimum")
        print("  - Balanced risk/reward profile")
        
        print("\n" + "="*60)
        return True
    else:
        print("\n✗ Configuration validation failed to catch the issue")
        print("This is unexpected - the validation should detect the inconsistency")
        return False

if __name__ == "__main__":
    success = test_configuration_validation()
    sys.exit(0 if success else 1)
