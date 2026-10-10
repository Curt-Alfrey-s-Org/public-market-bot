#!/usr/bin/env python3
"""
Simple verification script for startup fixes

Checks that the code changes were applied correctly without running full tests.
"""

import sys

def check_file_contains(filepath, search_strings):
    """Check if file contains all search strings"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        results = {}
        for search_str in search_strings:
            results[search_str] = search_str in content
        
        return results
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}

def main():
    print("=" * 60)
    print("Startup CPU Fix Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Check web_gui.py
    print("\n1. Checking web_gui.py...")
    web_gui_checks = {
        'WATCHLIST_STARTUP_DELAY': 'Startup delay configuration',
        'get_float_env': 'Startup delay implementation (using helper)',
        'time.sleep(startup_delay)': 'Startup delay execution',
        'system stabilization': 'Startup delay documentation'
    }
    
    results = check_file_contains('web_gui.py', web_gui_checks.keys())
    for key, description in web_gui_checks.items():
        passed = results.get(key, False)
        status = "✓" if passed else "✗"
        print(f"   {status} {description}")
        if not passed:
            all_passed = False
    
    # Check stock_screener.py
    print("\n2. Checking stock_screener.py...")
    screener_checks = {
        'STOCK_FETCH_DELAY': 'Fetch delay configuration',
        'fetch_delay_raw = os.getenv': 'Fetch delay implementation',
        'time.sleep(fetch_delay)': 'Fetch delay execution',
        'STOCK_SCREENER_MAX_CHECK': 'Max check limit configuration',
        'max_check_env = os.getenv': 'Max check limit implementation'
    }
    
    results = check_file_contains('stock_screener.py', screener_checks.keys())
    for key, description in screener_checks.items():
        passed = results.get(key, False)
        status = "✓" if passed else "✗"
        print(f"   {status} {description}")
        if not passed:
            all_passed = False
    
    # Check .env.example
    print("\n3. Checking .env.example...")
    env_checks = {
        'WATCHLIST_STARTUP_DELAY=5.0': 'Watchlist startup delay default',
        'STOCK_SCREENER_MAX_CHECK=100': 'Max check limit default',
        'STOCK_FETCH_DELAY=0.1': 'Fetch delay default',
        'allow system stabilization': 'Configuration documentation'
    }
    
    results = check_file_contains('.env.example', env_checks.keys())
    for key, description in env_checks.items():
        passed = results.get(key, False)
        status = "✓" if passed else "✗"
        print(f"   {status} {description}")
        if not passed:
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed!")
        print("\nThe following fixes have been applied:")
        print("  • 5 second startup delay before watchlist initialization")
        print("  • 0.1 second throttling between stock fetches")
        print("  • Reduced max stocks to check from 200 to 100")
        print("\nThese changes will:")
        print("  • Allow the web server to fully start before screening")
        print("  • Reduce CPU spikes during startup")
        print("  • Prevent system lag/jerking")
        return 0
    else:
        print("✗ Some checks failed - review the output above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
