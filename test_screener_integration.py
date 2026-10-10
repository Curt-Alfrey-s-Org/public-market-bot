#!/usr/bin/env python3
"""
Simple integration test for stock screener feature
Tests that stock screener can be called and returns results
"""

import os
import sys
import pytest


@pytest.mark.integration
def test_screener_integration_wrapper():
    """Pytest wrapper for stock screener integration test"""
    success = test_screener_basic()
    assert success, "Stock screener integration test should pass"

# Set test environment
os.environ['MIN_STOCK_PRICE'] = '5.0'
os.environ['MAX_STOCK_PRICE'] = '1000.0'
os.environ['MIN_DAILY_VOLUME'] = '500000'
os.environ['MAX_STOCK_VOLATILITY'] = '0.15'

# Import the screener
from stock_screener import StockScreener, screen_for_trades

def test_screener_basic():
    """Test basic screener functionality"""
    print("Testing Stock Screener...")
    print("=" * 60)
    
    # Initialize screener
    screener = StockScreener()
    print("✓ Screener initialized successfully")
    
    # Test filtering logic
    valid_stock = {
        'symbol': 'TEST',
        'price': 100.0,
        'volume': 1000000,
        'volatility': 0.05,
        'marketCap': 1000000000
    }
    
    passes, reason = screener.filter_stock(valid_stock)
    assert passes, f"Valid stock should pass: {reason}"
    print(f"✓ Valid stock passes filter: {reason}")
    
    # Test invalid stock (price too low)
    invalid_stock = {
        'symbol': 'PENNY',
        'price': 2.0,  # Below minimum
        'volume': 1000000,
        'volatility': 0.05,
        'marketCap': 100000000
    }
    
    passes, reason = screener.filter_stock(invalid_stock)
    assert not passes, "Invalid stock should not pass"
    print(f"✓ Invalid stock rejected: {reason}")
    
    # Test popular stocks fallback
    popular = screener.get_popular_stocks(count=5)
    assert len(popular) == 5, "Should return 5 popular stocks"
    print(f"✓ Popular stocks fallback works: {popular}")
    
    # Test get_screened_or_fallback
    # This will use popular stocks since yfinance likely not available
    results = screener.get_screened_or_fallback(max_results=5)
    assert len(results) > 0, "Should return some stocks"
    assert len(results) <= 5, "Should not exceed max_results"
    print(f"✓ Screened/fallback returns {len(results)} stocks: {results}")
    
    # Test convenience function
    results = screen_for_trades(max_stocks=3)
    assert len(results) <= 3, "Should respect max_stocks limit"
    print(f"✓ Convenience function works: {results}")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    return True

if __name__ == "__main__":
    try:
        success = test_screener_basic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
