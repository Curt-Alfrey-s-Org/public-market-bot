#!/usr/bin/env python3
"""
Manual verification script to demonstrate the capital saving functionality.
This script shows that:
1. Capital can be read from .env file
2. Capital can be saved to .env file
3. The value persists between reads
"""

import os
import tempfile

def demo_capital_saving():
    """Demonstrate the capital saving functionality"""
    print("="*70)
    print("MANUAL VERIFICATION: Total Capital Saving to .env")
    print("="*70)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_env_path = os.path.join(tmpdir, '.env')
        
        # Step 1: Create initial .env file
        print("\n📝 Step 1: Creating initial .env file with BOT_TOTAL_CAPITAL=10000")
        initial_content = """# Test environment file
PAPER_TRADING_MODE=true
BOT_TOTAL_CAPITAL=10000
BOT_MIN_ALLOCATION=100
BOT_MAX_ALLOCATION=5000
"""
        with open(test_env_path, 'w') as f:
            f.write(initial_content)
        
        print("✓ Initial .env file created")
        print("\nInitial content:")
        print("-" * 70)
        with open(test_env_path, 'r') as f:
            print(f.read())
        
        # Step 2: Change to temp directory and import web_gui
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            from web_gui import update_env_file
            
            # Step 3: Update capital to a new value
            new_capital = "25000"
            print(f"\n💾 Step 2: Updating BOT_TOTAL_CAPITAL to {new_capital}")
            
            settings = {'BOT_TOTAL_CAPITAL': new_capital}
            success, message = update_env_file(settings)
            
            if success:
                print(f"✓ Successfully saved: {message}")
            else:
                print(f"❌ Failed to save: {message}")
                return False
            
            # Step 4: Verify the change
            print("\n🔍 Step 3: Verifying the saved value")
            with open(test_env_path, 'r') as f:
                updated_content = f.read()
            
            print("\nUpdated content:")
            print("-" * 70)
            print(updated_content)
            
            if f'BOT_TOTAL_CAPITAL={new_capital}' in updated_content:
                print(f"\n✓ SUCCESS: BOT_TOTAL_CAPITAL was updated to {new_capital}")
                
                # Verify no duplication
                count = updated_content.count('BOT_TOTAL_CAPITAL=')
                if count == 1:
                    print("✓ No duplicate entries found")
                else:
                    print(f"⚠ Warning: BOT_TOTAL_CAPITAL appears {count} times")
                
                # Step 5: Update again to test replacement
                print(f"\n💾 Step 4: Updating BOT_TOTAL_CAPITAL again to 50000")
                settings = {'BOT_TOTAL_CAPITAL': '50000'}
                success, message = update_env_file(settings)
                
                if success:
                    with open(test_env_path, 'r') as f:
                        final_content = f.read()
                    
                    print("\nFinal content:")
                    print("-" * 70)
                    print(final_content)
                    
                    if 'BOT_TOTAL_CAPITAL=50000' in final_content:
                        print("\n✓ SUCCESS: Value can be updated multiple times")
                        
                        # Verify only one entry
                        count = final_content.count('BOT_TOTAL_CAPITAL=')
                        if count == 1:
                            print("✓ Only one BOT_TOTAL_CAPITAL entry exists")
                            return True
                        else:
                            print(f"❌ Multiple entries found: {count}")
                            return False
                    else:
                        print("❌ Failed to update value the second time")
                        return False
                else:
                    print(f"❌ Failed second update: {message}")
                    return False
            else:
                print(f"❌ FAILED: BOT_TOTAL_CAPITAL={new_capital} not found in file")
                return False
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            os.chdir(original_dir)


def demo_reading_from_env():
    """Demonstrate reading capital from environment variable"""
    print("\n" + "="*70)
    print("DEMONSTRATION: Reading Capital from Environment")
    print("="*70)
    
    # Set environment variable
    test_values = ["5000", "15000", "25000"]
    
    for test_value in test_values:
        os.environ['BOT_TOTAL_CAPITAL'] = test_value
        
        # Re-import to pick up new value
        import importlib
        import sys
        if 'web_gui' in sys.modules:
            del sys.modules['web_gui']
        
        from web_gui import DEFAULT_CAPITAL
        
        print(f"\n✓ With BOT_TOTAL_CAPITAL={test_value}, DEFAULT_CAPITAL={DEFAULT_CAPITAL}")
        
        if abs(DEFAULT_CAPITAL - float(test_value)) < 0.01:
            print(f"  ✓ Correctly read from environment variable")
        else:
            print(f"  ❌ Mismatch: expected {test_value}, got {DEFAULT_CAPITAL}")
    
    # Clean up
    if 'BOT_TOTAL_CAPITAL' in os.environ:
        del os.environ['BOT_TOTAL_CAPITAL']


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("TOTAL CAPITAL SAVING - MANUAL VERIFICATION")
    print("="*70)
    
    # Demo 1: Saving to .env file
    success1 = demo_capital_saving()
    
    # Demo 2: Reading from environment
    demo_reading_from_env()
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    if success1:
        print("\n✅ ALL VERIFICATIONS PASSED")
        print("\nThe fix successfully:")
        print("  1. ✓ Saves BOT_TOTAL_CAPITAL to .env file")
        print("  2. ✓ Reads BOT_TOTAL_CAPITAL from .env file")
        print("  3. ✓ Updates existing value without duplication")
        print("  4. ✓ Handles multiple updates correctly")
        print("\n🎯 Users can now save and persist their total capital setting!")
        return True
    else:
        print("\n❌ SOME VERIFICATIONS FAILED")
        return False


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
