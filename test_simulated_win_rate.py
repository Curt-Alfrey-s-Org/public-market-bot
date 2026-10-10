#!/usr/bin/env python3
"""
Test script to verify SIMULATED_WIN_RATE is being respected
"""

import os
import sys

# Set environment variables before importing main
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['BOT_RISK_THRESHOLD'] = '0.06'  # Fixed: 6% provides buffer above minimum 5% (500/10000)
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

from main import TradingBot, setup_logging

def test_simulated_win_rate():
    """Test that SIMULATED_WIN_RATE is respected in paper trading"""
    setup_logging()
    
    print("\n" + "="*60)
    print("TESTING SIMULATED WIN RATE")
    print("="*60)
    print(f"Expected Win Rate: 70%")
    print(f"Running 5 trades...")
    print("="*60 + "\n")
    
    # Initialize bot with default capital
    bot = TradingBot(total_capital=10000.0)
    
    # Define test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    # Execute trades
    for symbol in test_symbols:
        # Use fixed price and volume for testing
        price = 100.0
        volume = 1000000
        
        print(f"\nExecuting trade for {symbol}...")
        result = bot.execute_trade(symbol, 'BUY', price, volume=volume)
        
        if result and result.get('status') == 'skipped':
            print(f"  Trade skipped: {result.get('message', 'Unknown reason')}")
    
    # Print summary
    bot.print_summary()
    
    # Check win rate
    actual_win_rate = bot.track_record['win_rate']
    expected_win_rate = 0.7
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Expected Win Rate: {expected_win_rate:.2%}")
    print(f"Actual Win Rate: {actual_win_rate:.2%}")
    print(f"Total Trades: {bot.track_record['total_trades']}")
    print(f"Winning Trades: {bot.track_record['winning_trades']}")
    print(f"Losing Trades: {bot.track_record['losing_trades']}")
    
    # With 5 trades at 70% win rate, we expect 3-4 wins
    # Allow some tolerance for randomness
    if bot.track_record['total_trades'] >= 5:
        if 2 <= bot.track_record['winning_trades'] <= 5:
            print(f"\n✓ Win rate is within acceptable range for {bot.track_record['total_trades']} trades")
            print(f"  Note: With 5 trades and 70% win rate, we expect 3-4 wins")
            print(f"  Actual: {bot.track_record['winning_trades']} wins")
            return True
        else:
            print(f"\n✗ Win rate is outside expected range")
            return False
    else:
        print(f"\n✗ Not enough trades executed: {bot.track_record['total_trades']}")
        return False

if __name__ == "__main__":
    success = test_simulated_win_rate()
    sys.exit(0 if success else 1)
