#!/usr/bin/env python3
"""
Test script to verify real-time stock price fetching
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import sys
import logging
from main import TradingBot, setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def test_price_fetching():
    """Test fetching real stock prices"""
    print("="*60)
    print("STOCK PRICE FETCHING TEST")
    print("="*60)
    
    # Initialize bot
    bot = TradingBot(total_capital=10000.0)
    
    # Test symbols (use well-known stocks)
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print(f"\nTesting price fetch for {len(test_symbols)} symbols...")
    print("-"*60)
    
    results = []
    for symbol in test_symbols:
        print(f"\n[{symbol}]")
        
        # Try to fetch real price
        try:
            price, volume = bot.get_stock_price(symbol, use_random_fallback=True)
            
            # Check if this was from cache or real fetch
            is_cached = symbol in bot.price_cache
            source = "Real API" if is_cached else "Simulated (API unavailable)"
            
            print(f"  Price: ${price:.2f}")
            print(f"  Volume: {volume:,}")
            print(f"  Source: {source}")
            
            results.append({
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'success': True
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'symbol': symbol,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r['success'])
    print(f"Successfully fetched: {successful}/{len(test_symbols)}")
    
    if successful > 0:
        avg_price = sum(r['price'] for r in results if r['success']) / successful
        print(f"Average price: ${avg_price:.2f}")
    
    # Show which method was used
    if bot.price_cache:
        print(f"\n✓ Real-time API is working! Fetched {len(bot.price_cache)} real prices")
    else:
        print(f"\n⚠ Using simulated prices (API unavailable or network restricted)")
    
    print("="*60)
    
    return results

if __name__ == "__main__":
    try:
        results = test_price_fetching()
        
        # Exit with appropriate code
        successful = sum(1 for r in results if r['success'])
        sys.exit(0 if successful == len(results) else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
