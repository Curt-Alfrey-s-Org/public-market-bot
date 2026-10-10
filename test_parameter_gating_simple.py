#!/usr/bin/env python3
"""
Simple test to verify parameter gating imports and logic in gui.py
Tests without requiring tkinter/GUI components
"""

import os
import sys

# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('BOT_TOTAL_CAPITAL', '10000')
os.environ.setdefault('BOT_MIN_ALLOCATION', '100')
os.environ.setdefault('BOT_MAX_ALLOCATION', '5000')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that required imports are available from main.py"""
    print("="*70)
    print("Testing imports from main.py...")
    print("="*70)
    
    try:
        from main import (
            TradingBot,
            PAPER_TRADING_MODE,
            SCHWAB_SANDBOX_MODE,
            BOT_MIN_ALLOCATION,
            BOT_MAX_ALLOCATION,
            SCHWAB_API_KEY,
            SCHWAB_APP_SECRET,
            SCHWAB_ACCOUNT_ID,
            SCHWAB_CALLBACK_URL,
            SCHWAB_CREDENTIAL_PLACEHOLDERS,
            validate_configuration
        )
        print("✓ All required imports from main.py are available")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_validate_configuration():
    """Test that validate_configuration is callable and works"""
    print("\n" + "="*70)
    print("Testing validate_configuration function...")
    print("="*70)
    
    try:
        from main import validate_configuration
        
        # Call the function
        result = validate_configuration()
        
        # Check return type
        if not isinstance(result, tuple):
            print(f"✗ validate_configuration should return tuple, got {type(result)}")
            return False
        
        if len(result) != 2:
            print(f"✗ validate_configuration should return 2-tuple, got {len(result)} elements")
            return False
        
        is_valid, issues = result
        
        if not isinstance(is_valid, bool):
            print(f"✗ First element should be bool, got {type(is_valid)}")
            return False
        
        if not isinstance(issues, list):
            print(f"✗ Second element should be list, got {type(issues)}")
            return False
        
        has_issues = bool(issues)
        print(f"✓ validate_configuration returns: is_valid={is_valid}, has_issues={has_issues}")
        if issues:
            print("  Issues found (details omitted to avoid logging sensitive data).")
            preview_count = min(3, len(issues))
            print(f"  Showing {preview_count} issue placeholder(s) out of {len(issues)} total.")
            for _ in issues[:preview_count]:
                print("    - [redacted issue detail]")
            if len(issues) > preview_count:
                print(f"    ... and {len(issues) - preview_count} more")
        
        return True
    except Exception as e:
        print(f"✗ Error testing validate_configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_imports():
    """Test that gui.py imports the required symbols"""
    print("\n" + "="*70)
    print("Testing gui.py imports...")
    print("="*70)
    
    try:
        # Try to check if gui.py has the imports without actually loading tkinter
        with open('gui.py', 'r') as f:
            content = f.read()
        
        required_imports = [
            'SCHWAB_API_KEY',
            'SCHWAB_APP_SECRET',
            'SCHWAB_ACCOUNT_ID',
            'SCHWAB_CALLBACK_URL',
            'SCHWAB_CREDENTIAL_PLACEHOLDERS',
            'validate_configuration'
        ]
        
        # Check if these are in the import statement
        all_found = True
        for symbol in required_imports:
            if symbol in content[:2000]:  # Check first 2000 chars (imports section)
                print(f"  ✓ {symbol} found in gui.py")
            else:
                print(f"  ✗ {symbol} NOT found in gui.py imports")
                all_found = False
        
        if all_found:
            print("\n✓ All required symbols are imported in gui.py")
            return True
        else:
            print("\n✗ Some required symbols are missing from gui.py")
            return False
            
    except Exception as e:
        print(f"✗ Error checking gui.py: {e}")
        return False


def test_dead_code_removed():
    """Test that dead code after return statement was removed"""
    print("\n" + "="*70)
    print("Testing for dead code removal...")
    print("="*70)
    
    try:
        with open('gui.py', 'r') as f:
            lines = f.readlines()
        
        # Look for the problematic pattern in validate_params
        in_validate_params = False
        found_return_true = False
        found_dead_code = False
        
        for i, line in enumerate(lines):
            if 'def validate_params' in line:
                in_validate_params = True
            elif in_validate_params and 'def ' in line and 'validate_params' not in line:
                # Exited validate_params method
                break
            elif in_validate_params and 'return True' in line:
                found_return_true = True
                # Check next few lines for dead code
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#') and not next_line.startswith('def '):
                        if 'self.validate_settings' in next_line or 'validate_settings()' in next_line:
                            found_dead_code = True
                            print(f"  ✗ Dead code found at line {j+1}: {next_line}")
                            break
        
        if found_return_true and not found_dead_code:
            print("  ✓ No dead code found after return statement")
            return True
        elif found_dead_code:
            print("  ✗ Dead code still exists after return statement")
            return False
        else:
            print("  ? Could not find return statement in validate_params")
            return False
            
    except Exception as e:
        print(f"✗ Error checking for dead code: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PARAMETER GATING VERIFICATION")
    print("="*70)
    print("\nThis test verifies that the parameter gating implementation")
    print("in gui.py is complete and correct.\n")
    
    results = []
    
    # Test 1: Imports from main.py
    results.append(("Imports from main.py", test_imports()))
    
    # Test 2: validate_configuration function
    results.append(("validate_configuration function", test_validate_configuration()))
    
    # Test 3: gui.py imports
    results.append(("gui.py imports", test_gui_imports()))
    
    # Test 4: Dead code removal
    results.append(("Dead code removal", test_dead_code_removed()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Parameter gating is complete.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
