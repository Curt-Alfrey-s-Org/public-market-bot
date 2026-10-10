#!/usr/bin/env python3
"""
Test script to verify that trade settings persist after being saved in the web GUI.
This test simulates the complete flow:
1. Save settings to .env file
2. Reload settings
3. Verify settings were persisted
4. Restart simulation (reload .env)
5. Verify settings still persist
"""

import os
import sys
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Define the .env file path
original_env_file = '.env'

def test_settings_persistence():
    """Test that settings persist after being saved to .env file"""
    print("="*70)
    print("Testing Trade Settings Persistence")
    print("="*70)
    
    # Create a temporary .env file for testing
    backup_env_file = '.env.backup'
    
    # Backup original .env if it exists
    if os.path.exists(original_env_file):
        shutil.copy(original_env_file, backup_env_file)
        print(f"\n✓ Backed up original .env to {backup_env_file}")
    
    try:
        # Step 1: Create a test .env file with initial values
        print("\n1. Creating test .env file with initial values...")
        initial_settings = {
            'BOT_TOTAL_CAPITAL': '10000',
            'BOT_MIN_ALLOCATION': '100',
            'BOT_MAX_ALLOCATION': '500',
            'WEB_GUI_MAX_SYMBOLS': '5',
            'WEB_GUI_CYCLE_DELAY': '5',
        }
        
        with open(original_env_file, 'w') as f:
            f.write("# Test Environment Configuration\n")
            for key, value in initial_settings.items():
                f.write(f"{key}={value}\n")
        
        print("   ✓ Created .env with initial settings")
        for key, value in initial_settings.items():
            print(f"     {key}={value}")
        
        # Step 2: Import web_gui to load settings
        print("\n2. Loading web_gui module (simulates application startup)...")
        # Clear any cached modules
        if 'web_gui' in sys.modules:
            del sys.modules['web_gui']
        
        # Force environment reload
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            print("   ✓ Loaded .env file")
        except ImportError:
            print("   ⚠ python-dotenv not available")
        
        # Import functions from web_gui
        from web_gui import update_env_file, reload_settings_from_env, get_float_env, get_int_env
        
        # Verify initial values
        capital = get_float_env('BOT_TOTAL_CAPITAL', 10000)
        max_symbols = get_int_env('WEB_GUI_MAX_SYMBOLS', 5)
        print(f"   ✓ Initial capital: ${capital}")
        print(f"   ✓ Initial max symbols: {max_symbols}")
        
        # Step 3: Update settings (simulate user clicking save button)
        print("\n3. Updating settings (simulating user save action)...")
        new_settings = {
            'BOT_TOTAL_CAPITAL': '25000',  # Changed from 10000
            'BOT_MIN_ALLOCATION': '200',    # Changed from 100
            'BOT_MAX_ALLOCATION': '1000',   # Changed from 500
            'WEB_GUI_MAX_SYMBOLS': '10',    # Changed from 5
            'WEB_GUI_CYCLE_DELAY': '10',    # Changed from 5
        }
        
        success, message = update_env_file(new_settings)
        if not success:
            print(f"   ✗ Failed to update .env: {message}")
            return False
        
        print("   ✓ Settings saved to .env file")
        for key, value in new_settings.items():
            print(f"     {key}={value}")
        
        # Step 4: Reload settings (this is what happens after save button is clicked)
        print("\n4. Reloading settings from .env file...")
        reload_settings_from_env()
        print("   ✓ Settings reloaded")
        
        # Step 5: Verify settings were updated in memory
        print("\n5. Verifying settings are updated in memory...")
        # Force reload of environment
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            print("   ⚠ python-dotenv not available for reload")
        
        capital = get_float_env('BOT_TOTAL_CAPITAL', 10000)
        min_alloc = get_float_env('BOT_MIN_ALLOCATION', 50)
        max_alloc = get_float_env('BOT_MAX_ALLOCATION', 500)
        max_symbols = get_int_env('WEB_GUI_MAX_SYMBOLS', 5)
        cycle_delay = get_int_env('WEB_GUI_CYCLE_DELAY', 5)
        
        errors = []
        if capital != 25000:
            errors.append(f"Capital not updated: expected 25000, got {capital}")
        else:
            print(f"   ✓ Capital updated: ${capital}")
        
        if min_alloc != 200:
            errors.append(f"Min allocation not updated: expected 200, got {min_alloc}")
        else:
            print(f"   ✓ Min allocation updated: ${min_alloc}")
        
        if max_alloc != 1000:
            errors.append(f"Max allocation not updated: expected 1000, got {max_alloc}")
        else:
            print(f"   ✓ Max allocation updated: ${max_alloc}")
        
        if max_symbols != 10:
            errors.append(f"Max symbols not updated: expected 10, got {max_symbols}")
        else:
            print(f"   ✓ Max symbols updated: {max_symbols}")
        
        if cycle_delay != 10:
            errors.append(f"Cycle delay not updated: expected 10, got {cycle_delay}")
        else:
            print(f"   ✓ Cycle delay updated: {cycle_delay}")
        
        if errors:
            print("\n   ✗ Errors found:")
            for error in errors:
                print(f"     - {error}")
            return False
        
        # Step 6: Simulate page refresh / bot restart
        print("\n6. Simulating page refresh / bot restart...")
        # Clear module cache to simulate restart
        if 'web_gui' in sys.modules:
            del sys.modules['web_gui']
        
        # Reload dotenv (simulates fresh application start)
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            print("   ✓ Simulated application restart")
        except ImportError:
            print("   ⚠ python-dotenv not available for restart simulation")
        
        # Step 7: Verify settings persist after restart
        print("\n7. Verifying settings persist after restart...")
        capital = get_float_env('BOT_TOTAL_CAPITAL', 10000)
        max_symbols = get_int_env('WEB_GUI_MAX_SYMBOLS', 5)
        
        errors = []
        if capital != 25000:
            errors.append(f"Capital not persisted: expected 25000, got {capital}")
        else:
            print(f"   ✓ Capital persisted: ${capital}")
        
        if max_symbols != 10:
            errors.append(f"Max symbols not persisted: expected 10, got {max_symbols}")
        else:
            print(f"   ✓ Max symbols persisted: {max_symbols}")
        
        if errors:
            print("\n   ✗ Persistence errors:")
            for error in errors:
                print(f"     - {error}")
            return False
        
        # Step 8: Verify .env file contains correct values
        print("\n8. Verifying .env file contents...")
        with open(original_env_file, 'r') as f:
            content = f.read()
        
        errors = []
        for key, expected_value in new_settings.items():
            if f"{key}={expected_value}" not in content:
                errors.append(f"{key} not found in .env with value {expected_value}")
            else:
                print(f"   ✓ {key}={expected_value} found in .env")
        
        if errors:
            print("\n   ✗ .env file verification errors:")
            for error in errors:
                print(f"     - {error}")
            return False
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED - Settings persistence is working correctly!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup: restore original .env if it existed
        print("\n9. Cleaning up test files...")
        if os.path.exists(backup_env_file):
            shutil.copy(backup_env_file, original_env_file)
            os.remove(backup_env_file)
            print(f"   ✓ Restored original .env from backup")
        elif os.path.exists(original_env_file):
            os.remove(original_env_file)
            print(f"   ✓ Removed test .env file")

if __name__ == '__main__':
    try:
        success = test_settings_persistence()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
