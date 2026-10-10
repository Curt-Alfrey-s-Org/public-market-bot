#!/usr/bin/env python3
"""
Simple verification script for async watchlist initialization
Validates the code changes without requiring full dependencies
"""

import ast
import sys

def check_syntax(filename):
    """Check if Python file has valid syntax"""
    try:
        with open(filename, 'r') as f:
            ast.parse(f.read())
        print(f"✓ {filename} has valid syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {filename}: {e}")
        return False

def check_function_exists(filename, function_name):
    """Check if a function exists in the file"""
    with open(filename, 'r') as f:
        content = f.read()
        if f"def {function_name}(" in content:
            print(f"✓ Function '{function_name}' exists in {filename}")
            return True
        else:
            print(f"✗ Function '{function_name}' not found in {filename}")
            return False

def check_variable_exists(filename, variable_name):
    """Check if a global variable exists in the file"""
    with open(filename, 'r') as f:
        content = f.read()
        # Check for variable declaration (either direct assignment or as part of initialization)
        if f"{variable_name} =" in content or f"{variable_name}," in content:
            print(f"✓ Variable '{variable_name}' exists in {filename}")
            return True
        else:
            print(f"✗ Variable '{variable_name}' not found in {filename}")
            return False

def check_pattern_exists(filename, pattern):
    """Check if a specific pattern exists in the file"""
    with open(filename, 'r') as f:
        content = f.read()
        if pattern in content:
            print(f"✓ Pattern found in {filename}: '{pattern[:50]}...'")
            return True
        else:
            print(f"✗ Pattern not found in {filename}: '{pattern[:50]}...'")
            return False

def main():
    print("=" * 60)
    print("Verifying Async Watchlist Initialization Changes")
    print("=" * 60)
    print()
    
    checks = []
    
    # Check syntax
    print("1. Checking syntax...")
    checks.append(check_syntax('web_gui.py'))
    print()
    
    # Check new function exists
    print("2. Checking new function exists...")
    checks.append(check_function_exists('web_gui.py', 'async_initialize_watchlist'))
    print()
    
    # Check new variable exists
    print("3. Checking new state variable exists...")
    checks.append(check_variable_exists('web_gui.py', 'watchlist_loading'))
    print()
    
    # Check threading.Thread usage
    print("4. Checking async initialization with threading...")
    checks.append(check_pattern_exists('web_gui.py', 'threading.Thread'))
    checks.append(check_pattern_exists('web_gui.py', 'target=async_initialize_watchlist'))
    checks.append(check_pattern_exists('web_gui.py', 'daemon=True'))
    print()
    
    # Check loading state handling
    print("5. Checking loading state handling...")
    checks.append(check_pattern_exists('web_gui.py', 'if watchlist_loading:'))
    checks.append(check_pattern_exists('web_gui.py', 'Loading watchlist data'))
    print()
    
    # Check concurrent load prevention
    print("6. Checking concurrent load prevention...")
    checks.append(check_pattern_exists('web_gui.py', 'Watchlist update already in progress'))
    print()
    
    # Summary
    print("=" * 60)
    print(f"Results: {sum(checks)}/{len(checks)} checks passed")
    print("=" * 60)
    
    if all(checks):
        print("✓ All verification checks passed!")
        print()
        print("Changes summary:")
        print("  • Added watchlist_loading state variable")
        print("  • Added async_initialize_watchlist() function")
        print("  • Modified update_watchlist_data() to prevent concurrent loads")
        print("  • Modified format_watchlist_table() to show loading state")
        print("  • Modified main() to start watchlist init in background thread")
        print()
        print("Expected behavior:")
        print("  • Web server starts immediately without blocking")
        print("  • Watchlist loads asynchronously in background")
        print("  • UI shows loading indicator while data is fetched")
        print("  • No more slow startup with stock screener logs blocking")
        return 0
    else:
        print("✗ Some checks failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
