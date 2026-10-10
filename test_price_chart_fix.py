#!/usr/bin/env python3
"""
Test script to verify price chart works with fallback to yfinance or random simulation
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment for testing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'

from main import TradingBot, validate_api_connectivity

def test_price_fetching():
    """Test that price fetching works with various API availability scenarios"""
    logger.info("="*60)
    logger.info("Testing Price Fetching with Fallback Chain")
    logger.info("="*60)
    
    try:
        # Create bot instance
        logger.info("\nStep 1: Creating TradingBot instance...")
        bot = TradingBot(total_capital=1000.0)
        logger.info("✓ Bot created successfully")
        
        # Test API connectivity
        logger.info("\nStep 2: Testing API connectivity...")
        is_connected, msg = validate_api_connectivity(bot)
        logger.info(f"API Connectivity Result: {is_connected}")
        logger.info(f"Message: {msg}")
        
        if not is_connected:
            logger.error("✗ API connectivity check failed")
            return False
        
        logger.info("✓ API connectivity validated")
        
        # Test price fetching for multiple symbols
        logger.info("\nStep 3: Testing price fetching...")
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_symbols:
            try:
                logger.info(f"\n  Testing {symbol}...")
                price, volume = bot.get_stock_price(symbol, use_random_fallback=True)
                logger.info(f"  ✓ {symbol}: ${price:.2f} (Volume: {volume:,})")
            except Exception as e:
                logger.error(f"  ✗ Failed to fetch {symbol}: {e}")
                return False
        
        logger.info("\n" + "="*60)
        logger.info("✓ All Tests Passed!")
        logger.info("="*60)
        logger.info("\nMode Information:")
        logger.info(f"  - Schwab API Available: {bot.schwab_api_available}")
        logger.info(f"  - Using yfinance Sim: {bot.using_yfinance_sim}")
        logger.info(f"  - Fallback Chain Working: ✓")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_gui_scenario():
    """Test scenario similar to web GUI usage"""
    logger.info("\n" + "="*60)
    logger.info("Testing Web GUI Scenario")
    logger.info("="*60)
    
    try:
        # Simulate web GUI bot creation
        logger.info("\nSimulating web GUI bot creation...")
        bot = TradingBot(total_capital=500.0)
        
        # Simulate price data collection for chart
        logger.info("\nCollecting price data for chart...")
        symbols = ['AAPL', 'TSLA', 'NVDA']
        price_data = {}
        
        for symbol in symbols:
            try:
                price, volume = bot.get_stock_price(symbol, use_random_fallback=True)
                price_data[symbol] = {'price': price, 'volume': volume}
                logger.info(f"  ✓ {symbol}: ${price:.2f}")
            except Exception as e:
                logger.error(f"  ✗ Failed to get price for {symbol}: {e}")
                return False
        
        logger.info("\n✓ Web GUI scenario test passed!")
        logger.info(f"  Collected prices for {len(price_data)} symbols")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Web GUI scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    logger.info("Starting Price Chart Fix Tests\n")
    
    # Run tests
    test1_passed = test_price_fetching()
    test2_passed = test_web_gui_scenario()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Price Fetching Test: {'PASSED ✓' if test1_passed else 'FAILED ✗'}")
    logger.info(f"Web GUI Scenario Test: {'PASSED ✓' if test2_passed else 'FAILED ✗'}")
    logger.info("="*60)
    
    # Exit with appropriate code
    if test1_passed and test2_passed:
        logger.info("\n✓ All tests passed! Price chart should work correctly.")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed. See logs above for details.")
        sys.exit(1)
