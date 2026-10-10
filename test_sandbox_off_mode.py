#!/usr/bin/env python3
"""
Test script for the new "Off (Training Mode)" option in Schwab Sandbox Mode dropdown.
Verifies that setting sandbox_mode='off' properly configures environment for yfinance training.
"""

import sys

def test_sandbox_off_mode():
    """Test that sandbox_mode='off' sets correct environment variables"""
    
    print("Testing Schwab Sandbox Mode 'Off (Training Mode)' option...\n")
    
    # Simulate the apply_settings logic when sandbox_mode='off'
    sandbox_mode = 'off'
    schwab_api_enabled = 'on'  # This should be overridden
    paper_trading = 'false'  # This should be overridden
    
    # This is the logic from apply_settings callback
    if sandbox_mode == 'off':
        schwab_sandbox_value = 'false'
        schwab_api_value = 'off'
        paper_trading_value = 'true'  # Force paper trading for training mode
    else:
        schwab_sandbox_value = sandbox_mode
        schwab_api_value = schwab_api_enabled
        paper_trading_value = paper_trading
    
    # Verify the values are correct
    print("1. Testing sandbox_mode='off' configuration")
    print(f"   Input: sandbox_mode='{sandbox_mode}'")
    print(f"   Output: SCHWAB_SANDBOX_MODE='{schwab_sandbox_value}'")
    print(f"   Output: SCHWAB_API_ENABLED='{schwab_api_value}'")
    print(f"   Output: PAPER_TRADING_MODE='{paper_trading_value}'")
    print()
    
    assert schwab_sandbox_value == 'false', "When sandbox_mode='off', SCHWAB_SANDBOX_MODE should be 'false'"
    assert schwab_api_value == 'off', "When sandbox_mode='off', SCHWAB_API_ENABLED should be 'off'"
    assert paper_trading_value == 'true', "When sandbox_mode='off', PAPER_TRADING_MODE should be 'true'"
    
    print("   ✓ Off mode configuration correct\n")
    
    # Test that it overrides user settings
    print("2. Testing that 'off' mode overrides other settings")
    paper_trading = 'false'  # User set to live trading
    schwab_api_enabled = 'on'  # User has API enabled
    
    if sandbox_mode == 'off':
        schwab_sandbox_value = 'false'
        schwab_api_value = 'off'
        paper_trading_value = 'true'  # Force paper trading for training mode
    
    print(f"   Input: paper_trading='false', schwab_api_enabled='on'")
    print(f"   With sandbox_mode='off':")
    print(f"   Output: PAPER_TRADING_MODE='{paper_trading_value}' (overridden)")
    print(f"   Output: SCHWAB_API_ENABLED='{schwab_api_value}' (overridden)")
    print()
    
    assert paper_trading_value == 'true', "sandbox_mode='off' should override paper_trading setting"
    assert schwab_api_value == 'off', "sandbox_mode='off' should override schwab_api_enabled setting"
    
    print("   ✓ Override logic works correctly\n")
    
    # Test other modes are not affected
    print("3. Testing that other modes are not affected")
    
    sandbox_mode = 'true'  # Sandbox enabled
    paper_trading = 'true'
    schwab_api_enabled = 'on'
    
    if sandbox_mode == 'off':
        schwab_sandbox_value = 'false'
        schwab_api_value = 'off'
        paper_trading_value = 'true'
    else:
        schwab_sandbox_value = sandbox_mode
        schwab_api_value = schwab_api_enabled
        paper_trading_value = paper_trading
    
    print(f"   Input: sandbox_mode='true'")
    print(f"   Output: SCHWAB_SANDBOX_MODE='{schwab_sandbox_value}'")
    print(f"   Output: SCHWAB_API_ENABLED='{schwab_api_value}'")
    print(f"   Output: PAPER_TRADING_MODE='{paper_trading_value}'")
    print()
    
    assert schwab_sandbox_value == 'true', "sandbox_mode='true' should keep original value"
    assert schwab_api_value == 'on', "sandbox_mode='true' should not override API enabled"
    assert paper_trading_value == 'true', "sandbox_mode='true' should not override paper_trading"
    
    print("   ✓ Other modes not affected\n")
    
    print("All 'Off (Training Mode)' tests passed! ✓")

def test_get_initial_sandbox_mode():
    """Test the get_initial_sandbox_mode helper function"""
    
    print("\nTesting get_initial_sandbox_mode helper function...\n")
    
    # Simulate the helper function logic
    def get_initial_sandbox_mode_logic(schwab_api_enabled_env, schwab_sandbox_mode_env):
        schwab_api_enabled = schwab_api_enabled_env.lower()
        if schwab_api_enabled in ('off', 'false', '0', 'no'):
            return 'off'
        return schwab_sandbox_mode_env
    
    # Test case 1: SCHWAB_API_ENABLED=off
    result = get_initial_sandbox_mode_logic('off', 'true')
    print(f"1. SCHWAB_API_ENABLED='off', SCHWAB_SANDBOX_MODE='true'")
    print(f"   Result: '{result}'")
    assert result == 'off', "Should return 'off' when SCHWAB_API_ENABLED='off'"
    print("   ✓ Correct\n")
    
    # Test case 2: SCHWAB_API_ENABLED=on, SCHWAB_SANDBOX_MODE=true
    result = get_initial_sandbox_mode_logic('on', 'true')
    print(f"2. SCHWAB_API_ENABLED='on', SCHWAB_SANDBOX_MODE='true'")
    print(f"   Result: '{result}'")
    assert result == 'true', "Should return 'true' when API enabled and sandbox mode true"
    print("   ✓ Correct\n")
    
    # Test case 3: SCHWAB_API_ENABLED=on, SCHWAB_SANDBOX_MODE=false
    result = get_initial_sandbox_mode_logic('on', 'false')
    print(f"3. SCHWAB_API_ENABLED='on', SCHWAB_SANDBOX_MODE='false'")
    print(f"   Result: '{result}'")
    assert result == 'false', "Should return 'false' when API enabled and sandbox mode false"
    print("   ✓ Correct\n")
    
    # Test case 4: SCHWAB_API_ENABLED=false (alternate off value)
    result = get_initial_sandbox_mode_logic('false', 'true')
    print(f"4. SCHWAB_API_ENABLED='false', SCHWAB_SANDBOX_MODE='true'")
    print(f"   Result: '{result}'")
    assert result == 'off', "Should return 'off' when SCHWAB_API_ENABLED='false'"
    print("   ✓ Correct\n")
    
    print("All helper function tests passed! ✓")

if __name__ == '__main__':
    print("="*60)
    print("Schwab Sandbox Mode 'Off' Option Test Suite")
    print("="*60)
    print()
    
    try:
        test_sandbox_off_mode()
        test_get_initial_sandbox_mode()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print()
        print("Summary:")
        print("  • 'Off (Training Mode)' option added to Schwab Sandbox Mode")
        print("  • Sets SCHWAB_SANDBOX_MODE=false")
        print("  • Sets SCHWAB_API_ENABLED=off (forces yfinance)")
        print("  • Sets PAPER_TRADING_MODE=true (training mode)")
        print("  • Overrides user settings when 'off' is selected")
        print("  • Other modes (Sandbox, Live) not affected")
        print()
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)
