#!/usr/bin/env python3
"""
Test script to validate that total capital value is saved to .env file
when changed in the bot settings.
"""

import os
import sys
import tempfile
from pathlib import Path
def test_capital_env_variable_exists():
    """Test that BOT_TOTAL_CAPITAL environment variable is documented"""
    print("\n" + "="*60)
    print("TEST 1: BOT_TOTAL_CAPITAL Environment Variable")
    print("="*60)
    
    env_example_path = '.env.example'
    
    if not os.path.exists(env_example_path):
        print(f"❌ FAIL: {env_example_path} not found")
        return False
    
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    if 'BOT_TOTAL_CAPITAL' in content:
        print("✓ BOT_TOTAL_CAPITAL variable found in .env.example")
        
        # Check if documentation mentions live mode behavior
        if 'live' in content.lower() and 'api' in content.lower():
            print("✓ Documentation explains live mode vs paper mode behavior")
        else:
            print("⚠ Warning: Documentation could be clearer about live mode")
        
        return True
    else:
        print("❌ FAIL: BOT_TOTAL_CAPITAL not found in .env.example")
        return False


def test_web_gui_reads_capital():
    """Test that web_gui.py reads BOT_TOTAL_CAPITAL from environment"""
    print("\n" + "="*60)
    print("TEST 2: Web GUI Reads Capital from Environment")
    print("="*60)
    
    # Set test environment variable
    test_capital = "15000"
    os.environ['BOT_TOTAL_CAPITAL'] = test_capital
    
    try:
        # Import web_gui module (will read env vars on import)
        import importlib
        if 'web_gui' in sys.modules:
            importlib.reload(sys.modules['web_gui'])
        
        import web_gui
        
        # Check if DEFAULT_CAPITAL was set from environment
        if hasattr(web_gui, 'DEFAULT_CAPITAL'):
            if abs(web_gui.DEFAULT_CAPITAL - float(test_capital)) < 0.01:
                print(f"✓ DEFAULT_CAPITAL correctly set to {web_gui.DEFAULT_CAPITAL} from BOT_TOTAL_CAPITAL")
                return True
            else:
                print(f"❌ FAIL: DEFAULT_CAPITAL is {web_gui.DEFAULT_CAPITAL}, expected {test_capital}")
                return False
        else:
            print("❌ FAIL: DEFAULT_CAPITAL not found in web_gui module")
            return False
    
    except Exception as e:
        print(f"❌ FAIL: Error importing web_gui: {e}")
        return False
    finally:
        # Clean up
        if 'BOT_TOTAL_CAPITAL' in os.environ:
            del os.environ['BOT_TOTAL_CAPITAL']


def test_update_env_file_saves_capital():
    """Test that update_env_file function saves capital correctly"""
    print("\n" + "="*60)
    print("TEST 3: Saving Capital to .env File")
    print("="*60)
    
    # Create a temporary .env file for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_env_path = os.path.join(tmpdir, '.env')
        
        # Create initial .env file
        initial_content = """# Test .env file
PAPER_TRADING_MODE=true
BOT_TOTAL_CAPITAL=10000
BOT_MIN_ALLOCATION=100
"""
        with open(test_env_path, 'w') as f:
            f.write(initial_content)
        
        # Save current directory and change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Import the update_env_file function
            from web_gui import update_env_file
            
            # Test updating capital
            new_capital = "25000"
            settings = {'BOT_TOTAL_CAPITAL': new_capital}
            
            success, message = update_env_file(settings)
            
            if not success:
                print(f"❌ FAIL: update_env_file returned False: {message}")
                return False
            
            # Read the updated file
            with open(test_env_path, 'r') as f:
                updated_content = f.read()
            
            # Check if capital was updated
            if f'BOT_TOTAL_CAPITAL={new_capital}' in updated_content:
                print(f"✓ Capital successfully updated to {new_capital} in .env file")
                
                # Verify old value was replaced, not appended
                count = updated_content.count('BOT_TOTAL_CAPITAL=')
                if count == 1:
                    print("✓ Old value was replaced (not duplicated)")
                    return True
                else:
                    print(f"❌ FAIL: BOT_TOTAL_CAPITAL appears {count} times in file")
                    return False
            else:
                print(f"❌ FAIL: BOT_TOTAL_CAPITAL={new_capital} not found in updated file")
                print(f"Content: {updated_content}")
                return False
        
        except Exception as e:
            print(f"❌ FAIL: Error testing update_env_file: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Restore original directory
            os.chdir(original_dir)


def test_capital_in_settings_map():
    """Test that capital is included in the settings_map in apply_settings"""
    print("\n" + "="*60)
    print("TEST 4: Capital in Settings Map")
    print("="*60)
    
    try:
        with open('web_gui.py', 'r') as f:
            content = f.read()
        
        # Look for the apply_settings function
        if "'BOT_TOTAL_CAPITAL'" in content or '"BOT_TOTAL_CAPITAL"' in content:
            print("✓ BOT_TOTAL_CAPITAL found in web_gui.py")
            
            # Check if it's in the settings_map
            if 'settings_map' in content and 'BOT_TOTAL_CAPITAL' in content:
                # Find the settings_map section
                settings_map_start = content.find('settings_map = {')
                if settings_map_start > 0:
                    # Check if BOT_TOTAL_CAPITAL is after settings_map definition
                    bot_capital_pos = content.find('BOT_TOTAL_CAPITAL', settings_map_start)
                    if bot_capital_pos > settings_map_start:
                        print("✓ BOT_TOTAL_CAPITAL is included in settings_map")
                        return True
            
            print("❌ FAIL: BOT_TOTAL_CAPITAL not found in settings_map")
            return False
        else:
            print("❌ FAIL: BOT_TOTAL_CAPITAL not found in web_gui.py")
            return False
    
    except Exception as e:
        print(f"❌ FAIL: Error reading web_gui.py: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TOTAL CAPITAL SAVING - TEST SUITE")
    print("="*70)
    
    tests = [
        ("BOT_TOTAL_CAPITAL exists in .env.example", test_capital_env_variable_exists),
        ("Web GUI reads capital from environment", test_web_gui_reads_capital),
        ("update_env_file saves capital correctly", test_update_env_file_saves_capital),
        ("Capital is in settings_map", test_capital_in_settings_map),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*70)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
