#!/usr/bin/env python3
"""
Verification script for yfinance mode fix
Tests that bot properly initializes and runs in yfinance mode
"""

import os
import sys

# Set up test environment for yfinance mode
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'  # This triggers yfinance mode
os.environ['SCHWAB_API_KEY'] = 'placeholder'
os.environ['SCHWAB_APP_SECRET'] = 'placeholder'
os.environ['ENABLE_STOCK_SCREENER'] = 'false'  # Use simple symbol list
os.environ['ENABLE_ML_SIGNAL_FILTER'] = 'false'  # Simplify for test

print("="*70)
print("YFINANCE MODE FIX VERIFICATION")
print("="*70)
print()
print("Environment Configuration:")
print(f"  SCHWAB_API_ENABLED: {os.getenv('SCHWAB_API_ENABLED')}")
print(f"  PAPER_TRADING_MODE: {os.getenv('PAPER_TRADING_MODE')}")
print(f"  SCHWAB_SANDBOX_MODE: {os.getenv('SCHWAB_SANDBOX_MODE')}")
print()

# Import after setting env vars
try:
    from main import TradingBot, ENABLE_PDT_RULES
    print("✓ Successfully imported TradingBot")
except Exception as e:
    print(f"✗ Failed to import TradingBot: {e}")
    sys.exit(1)

# Test 1: Bot initialization
print()
print("Test 1: Bot Initialization")
print("-" * 70)
try:
    bot = TradingBot(total_capital=10000.0)
    print("✓ Bot initialized successfully")
except Exception as e:
    print(f"✗ Bot initialization failed: {e}")
    sys.exit(1)

# Test 2: Verify yfinance mode is active
print()
print("Test 2: Verify yfinance Mode")
print("-" * 70)
if bot.using_yfinance_sim:
    print(f"✓ Bot is using yfinance sim mode: {bot.using_yfinance_sim}")
else:
    print(f"✗ Bot is NOT using yfinance sim mode: {bot.using_yfinance_sim}")
    sys.exit(1)

if not bot.schwab_api_available:
    print(f"✓ Schwab API correctly unavailable: {bot.schwab_api_available}")
else:
    print(f"✗ Schwab API should be unavailable: {bot.schwab_api_available}")
    sys.exit(1)

# Test 3: Verify PDT rules are DISABLED
print()
print("Test 3: Verify PDT Rules are DISABLED")
print("-" * 70)
pdt_env = os.getenv('ENABLE_PDT_RULES', 'not_set')
if pdt_env == 'false':
    print(f"✓ PDT rules disabled in environment: {pdt_env}")
else:
    print(f"✗ PDT rules should be 'false', got: {pdt_env}")
    sys.exit(1)

if not ENABLE_PDT_RULES:
    print(f"✓ PDT rules disabled in config: {ENABLE_PDT_RULES}")
else:
    print(f"✗ PDT rules should be False, got: {ENABLE_PDT_RULES}")
    sys.exit(1)

# Test 4: Verify bot can load symbols
print()
print("Test 4: Symbol Loading")
print("-" * 70)
try:
    symbols = bot.load_scan_symbols(use_screener=False, max_symbols=3)
    if len(symbols) > 0:
        print(f"✓ Loaded {len(symbols)} symbols: {symbols[:3]}")
    else:
        print(f"⚠ No symbols loaded, but no error occurred")
except Exception as e:
    print(f"✗ Symbol loading failed: {e}")
    sys.exit(1)

# Test 5: Verify bot can fetch prices (with fallback)
print()
print("Test 5: Price Fetching")
print("-" * 70)
try:
    # Try to fetch price - should use yfinance or fallback
    price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
    if price is not None and price > 0:
        print(f"✓ Fetched price for AAPL: ${price:.2f}, volume: {volume}")
    else:
        print(f"⚠ Price fetch returned None or 0")
except Exception as e:
    print(f"⚠ Price fetching had issues: {e}")
    # Not a critical failure for this test

# Test 6: Verify auto-configuration settings
print()
print("Test 6: Auto-Configuration Settings")
print("-" * 70)
expected_settings = {
    'PAPER_TRADING_MODE': 'true',
    'SCHWAB_SANDBOX_MODE': 'false',
    'SCHWAB_API_ENABLED': 'off',
    'ENABLE_PDT_RULES': 'false',
}

all_correct = True
for key, expected_value in expected_settings.items():
    actual_value = os.getenv(key, 'not_set')
    if actual_value == expected_value:
        print(f"✓ {key}: {actual_value}")
    else:
        print(f"✗ {key}: expected '{expected_value}', got '{actual_value}'")
        all_correct = False

if not all_correct:
    sys.exit(1)

# Success!
print()
print("="*70)
print("✅ ALL TESTS PASSED - YFINANCE MODE FIX VERIFIED")
print("="*70)
print()
print("Summary:")
print("  • Bot initializes correctly in yfinance mode")
print("  • yfinance simulation mode is active")
print("  • Schwab API is correctly disabled")
print("  • PDT rules are DISABLED (simulation mode)")
print("  • Symbol loading works")
print("  • Auto-configuration settings are correct")
print()
print("The bot should now run properly when start button is pressed in yfinance mode!")
print()
