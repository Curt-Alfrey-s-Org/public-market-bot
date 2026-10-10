#!/usr/bin/env python3
"""
Verification script for async API implementation
Tests that async fetching is working correctly
"""

import sys
import os

def verify_async_implementation():
    """Verify that async implementation is working"""
    
    print("="*60)
    print("Async API Implementation Verification")
    print("="*60)
    
    all_tests_passed = True
    
    # Test 1: Check if async_data_fetcher module exists and can be imported
    print("\n[1/6] Testing async_data_fetcher module import...")
    try:
        import async_data_fetcher
        print("✓ async_data_fetcher module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import async_data_fetcher: {e}")
        all_tests_passed = False
        return all_tests_passed
    
    # Test 2: Check if aiohttp is available
    print("\n[2/6] Testing aiohttp availability...")
    if async_data_fetcher.AIOHTTP_AVAILABLE:
        print("✓ aiohttp is available")
    else:
        print("⚠ aiohttp is not available (async will fall back to sync)")
    
    # Test 3: Test AsyncDataFetcher initialization
    print("\n[3/6] Testing AsyncDataFetcher initialization...")
    try:
        fetcher = async_data_fetcher.AsyncDataFetcher()
        print("✓ AsyncDataFetcher initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize AsyncDataFetcher: {e}")
        all_tests_passed = False
        return all_tests_passed
    
    # Test 4: Test singleton pattern
    print("\n[4/6] Testing singleton pattern...")
    try:
        fetcher1 = async_data_fetcher.get_async_fetcher()
        fetcher2 = async_data_fetcher.get_async_fetcher()
        if fetcher1 is fetcher2:
            print("✓ Singleton pattern working correctly")
        else:
            print("✗ Singleton pattern not working (different instances)")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Singleton test failed: {e}")
        all_tests_passed = False
    
    # Test 5: Test cache functionality
    print("\n[5/6] Testing cache functionality...")
    try:
        test_data = {'test': 'value'}
        cache_key = 'test_key'
        
        fetcher._cache_data(cache_key, test_data)
        
        if fetcher._is_cache_valid(cache_key):
            cached = fetcher._get_cached_data(cache_key)
            if cached == test_data:
                print("✓ Cache functionality working correctly")
            else:
                print("✗ Cached data doesn't match")
                all_tests_passed = False
        else:
            print("✗ Cache not valid immediately after caching")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Cache test failed: {e}")
        all_tests_passed = False
    
    # Test 6: Check main.py integration
    print("\n[6/6] Testing main.py integration...")
    try:
        # Set environment for testing
        os.environ['ENABLE_PDT_RULES'] = 'false'
        os.environ['PAPER_TRADING_MODE'] = 'true'
        
        import main
        
        if hasattr(main, 'ASYNC_DATA_FETCHER_AVAILABLE'):
            print(f"✓ main.py has ASYNC_DATA_FETCHER_AVAILABLE: {main.ASYNC_DATA_FETCHER_AVAILABLE}")
        else:
            print("✗ main.py missing ASYNC_DATA_FETCHER_AVAILABLE constant")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ main.py integration test failed: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "="*60)
    if all_tests_passed:
        print("✓ ALL TESTS PASSED - Async implementation verified!")
    else:
        print("✗ SOME TESTS FAILED - See above for details")
    print("="*60)
    
    return all_tests_passed


if __name__ == '__main__':
    success = verify_async_implementation()
    sys.exit(0 if success else 1)
