#!/usr/bin/env python3
"""
Test script to verify AI Assistant integration in web GUI
Tests that the new AI Assistant tab components are properly defined
"""

import sys
import pytest


@pytest.mark.integration
def test_ai_assistant_integration_wrapper():
    """Pytest wrapper for AI assistant integration test"""
    web_gui_ok = test_ai_assistant_components()
    env_ok = test_env_example()
    main_ok = test_main_py()
    assert web_gui_ok and env_ok and main_ok, "AI assistant integration test should pass"


def test_ai_assistant_components():
    """Test that AI Assistant components are present in web_gui.py"""
    
    print("="*60)
    print("TESTING AI ASSISTANT INTEGRATION")
    print("="*60)
    
    with open('web_gui.py', 'r') as f:
        content = f.read()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check for AI Assistant tab
    print("\n[TEST 1] Checking for AI Assistant tab definition...")
    if "dcc.Tab(label='🤖 AI Assistant'" in content:
        print("  ✓ AI Assistant tab found")
        tests_passed += 1
    else:
        print("  ✗ AI Assistant tab NOT found")
        tests_failed += 1
    
    # Test 2: Check for AI request button
    print("\n[TEST 2] Checking for AI request button...")
    if "id='ai-request-button'" in content:
        print("  ✓ AI request button found")
        tests_passed += 1
    else:
        print("  ✗ AI request button NOT found")
        tests_failed += 1
    
    # Test 3: Check for AI suggestions display
    print("\n[TEST 3] Checking for AI suggestions display...")
    if "id='ai-suggestions-display'" in content:
        print("  ✓ AI suggestions display found")
        tests_passed += 1
    else:
        print("  ✗ AI suggestions display NOT found")
        tests_failed += 1
    
    # Test 4: Check for AI apply button
    print("\n[TEST 4] Checking for AI apply button...")
    if "id='ai-apply-button'" in content:
        print("  ✓ AI apply button found")
        tests_passed += 1
    else:
        print("  ✗ AI apply button NOT found")
        tests_failed += 1
    
    # Test 5: Check for AI performance summary callback
    print("\n[TEST 5] Checking for AI performance summary callback...")
    if "def update_ai_performance_summary" in content:
        print("  ✓ AI performance summary callback found")
        tests_passed += 1
    else:
        print("  ✗ AI performance summary callback NOT found")
        tests_failed += 1
    
    # Test 6: Check for AI request suggestions callback
    print("\n[TEST 6] Checking for AI request suggestions callback...")
    if "def request_ai_suggestions" in content:
        print("  ✓ AI request suggestions callback found")
        tests_passed += 1
    else:
        print("  ✗ AI request suggestions callback NOT found")
        tests_failed += 1
    
    # Test 7: Check for MAX_STOCK_PRICE setting
    print("\n[TEST 7] Checking for MAX_STOCK_PRICE setting...")
    if "id='setting-max-price'" in content:
        print("  ✓ MAX_STOCK_PRICE setting input found")
        tests_passed += 1
    else:
        print("  ✗ MAX_STOCK_PRICE setting input NOT found")
        tests_failed += 1
    
    # Test 8: Check that MAX_STOCK_PRICE is saved to env
    print("\n[TEST 8] Checking MAX_STOCK_PRICE in settings map...")
    if "'MAX_STOCK_PRICE': str(max_price)" in content:
        print("  ✓ MAX_STOCK_PRICE in settings map")
        tests_passed += 1
    else:
        print("  ✗ MAX_STOCK_PRICE NOT in settings map")
        tests_failed += 1
    
    # Test 9: Check for minimum trades logic
    print("\n[TEST 9] Checking for minimum trades validation...")
    if "min_trades" in content and "total_trades < min_trades" in content:
        print("  ✓ Minimum trades validation found")
        tests_passed += 1
    else:
        print("  ✗ Minimum trades validation NOT found")
        tests_failed += 1
    
    # Test 10: Check for loading indicator
    print("\n[TEST 10] Checking for loading indicator...")
    if "id='ai-loading-indicator'" in content:
        print("  ✓ Loading indicator found")
        tests_passed += 1
    else:
        print("  ✗ Loading indicator NOT found")
        tests_failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print("="*60)
    
    return tests_failed == 0


def test_env_example():
    """Test that .env.example has MAX_STOCK_PRICE"""
    print("\n" + "="*60)
    print("TESTING .ENV.EXAMPLE FILE")
    print("="*60)
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    print("\n[TEST] Checking for MAX_STOCK_PRICE in .env.example...")
    if "MAX_STOCK_PRICE=" in content:
        print("  ✓ MAX_STOCK_PRICE found in .env.example")
        return True
    else:
        print("  ✗ MAX_STOCK_PRICE NOT found in .env.example")
        return False


def test_main_py():
    """Test that main.py has MAX_STOCK_PRICE"""
    print("\n" + "="*60)
    print("TESTING MAIN.PY FILE")
    print("="*60)
    
    with open('main.py', 'r') as f:
        content = f.read()
    
    print("\n[TEST] Checking for MAX_STOCK_PRICE in main.py...")
    if "MAX_STOCK_PRICE = float(os.getenv('MAX_STOCK_PRICE'" in content:
        print("  ✓ MAX_STOCK_PRICE found in main.py")
        return True
    else:
        print("  ✗ MAX_STOCK_PRICE NOT found in main.py")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AI ASSISTANT INTEGRATION TEST SUITE")
    print("="*60)
    
    # Run all tests
    web_gui_ok = test_ai_assistant_components()
    env_ok = test_env_example()
    main_ok = test_main_py()
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"web_gui.py: {'✓ PASSED' if web_gui_ok else '✗ FAILED'}")
    print(f".env.example: {'✓ PASSED' if env_ok else '✗ FAILED'}")
    print(f"main.py: {'✓ PASSED' if main_ok else '✗ FAILED'}")
    print("="*60)
    
    if web_gui_ok and env_ok and main_ok:
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
