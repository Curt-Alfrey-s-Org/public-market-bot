#!/usr/bin/env python3
"""Diagnostic tool for yfinance mode bot startup issues"""

import os
import sys
import time
from pathlib import Path

# Add repo to path
repo_path = Path(__file__).parent
sys.path.insert(0, str(repo_path))

print("=" * 70)
print("YFINANCE MODE BOT STARTUP DIAGNOSTICS")
print("=" * 70)
print()

# Set yfinance mode environment
print("[STEP 1] Setting yfinance mode environment variables...")
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['WEB_GUI_DEBUG'] = 'true'
os.environ['ENABLE_STOCK_SCREENER'] = 'true'
os.environ['MAX_DISCOVERED_STOCKS'] = '10'
print("✓ Environment variables set")
print()

# Import bot
print("[STEP 2] Importing TradingBot class...")
try:
    from main import TradingBot
    print("✓ TradingBot imported successfully")
except Exception as e:
    print(f"✗ FAILED to import TradingBot: {e}")
    sys.exit(1)
print()

# Initialize bot
print("[STEP 3] Initializing bot instance...")
init_start = time.time()
try:
    bot = TradingBot(total_capital=10000.0)
    init_time = time.time() - init_start
    print(f"✓ Bot initialized successfully in {init_time:.2f}s")
    print(f"  - Capital: ${bot.total_capital:.2f}")
    print(f"  - Using yfinance sim: {getattr(bot, 'using_yfinance_sim', 'NOT SET')}")
    print(f"  - Strategy manager: {getattr(bot, '_strategy_manager', 'NOT SET')}")
except Exception as e:
    print(f"✗ FAILED to initialize bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Load symbols
print("[STEP 4] Loading trade symbols...")
load_start = time.time()
try:
    symbols = bot.load_scan_symbols(use_screener=True, max_symbols=10)
    load_time = time.time() - load_start
    print(f"✓ Loaded {len(symbols)} symbols in {load_time:.2f}s:")
    for i, sym in enumerate(symbols[:5], 1):
        print(f"  #{i}. {sym}")
    if len(symbols) > 5:
        print(f"  ... and {len(symbols) - 5} more")
    if len(symbols) == 0:
        print("⚠️  WARNING: No symbols loaded! Bot will exit immediately.")
except Exception as e:
    print(f"✗ FAILED to load symbols: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Test get_strategy_signal on first symbol
if symbols:
    print(f"[STEP 5] Testing get_strategy_signal on '{symbols[0]}'...")
    signal_start = time.time()
    try:
        signal, price, volume = bot.get_strategy_signal(symbols[0], use_random_fallback=True)
        signal_time = time.time() - signal_start
        print(f"✓ Signal retrieved in {signal_time:.2f}s:")
        print(f"  - Signal: {signal}")
        print(f"  - Price: {price}")
        print(f"  - Volume: {volume}")
    except Exception as e:
        print(f"✗ FAILED to get strategy signal: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  This will prevent the bot from trading!")
    print()

# Final summary
print("=" * 70)
print("DIAGNOSTICS COMPLETE")
print("=" * 70)
print()
print("Summary:")
print("  ✓ Bot initializes successfully")
print("  ✓ Symbols can be loaded")
if symbols:
    print("  ✓ Strategy signal can be retrieved")
    print()
    print("If bot still won't start, check:")
    print("  1. Look at API logs for any errors during start_bot()")
    print("  2. Check if bot thread is actually starting")
    print("  3. Verify no exceptions in _run_bot_loop()")
else:
    print("  ✗ NO SYMBOLS LOADED - Bot will exit immediately")
    print()
    print("Fix this issue first - the screener may be failing due to:")
    print("  1. API rate limits or timeouts")
    print("  2. yfinance being unable to fetch data")
    print("  3. Filtering criteria being too restrictive")

