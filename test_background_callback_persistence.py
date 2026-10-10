#!/usr/bin/env python3
"""
Test background image persistence through callbacks
Simulates the actual callback flow to ensure background persists
"""

import os
import shutil

# Mock the persistence functions
USER_DATA_DIR = 'test_user_data_callback'
BACKGROUND_PATH = os.path.join(USER_DATA_DIR, 'background.txt')

# Global variable to simulate web_gui.py
background_image_data = None

def ensure_user_data_dir():
    """Ensure the user_data directory exists"""
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

def validate_image_data_url(data):
    """Validate that data is a properly formatted image data URL"""
    if not data or not isinstance(data, str) or not data.startswith('data:image/'):
        return False
    if ';' not in data or ',' not in data:
        return False
    comma_index = data.find(',')
    if comma_index >= len(data) - 1:
        return False
    return True

def save_background(background_data):
    """Save background image data to file"""
    if not validate_image_data_url(background_data):
        return
    ensure_user_data_dir()
    with open(BACKGROUND_PATH, 'w') as f:
        f.write(background_data)

def load_background():
    """Load background image data from file"""
    if os.path.exists(BACKGROUND_PATH):
        with open(BACKGROUND_PATH, 'r') as f:
            return f.read()
    return None

def simulate_startup_load():
    """Simulate loading background on startup"""
    global background_image_data
    background = load_background()
    if background:
        background_image_data = background
        print(f"   Loaded background on startup: {len(background)} chars")
    else:
        print("   No background to load on startup")

def simulate_update_background_callback(contents=None, remove_clicks=0, n_intervals=0, triggered_by='interval'):
    """
    Simulate the update_background callback behavior
    This mimics the actual callback in web_gui.py
    """
    global background_image_data
    
    # Handle remove button
    if triggered_by == 'remove-background-button':
        background_image_data = None
        if os.path.exists(BACKGROUND_PATH):
            os.remove(BACKGROUND_PATH)
        print("   Callback: Background removed")
        return {'style': 'default (no background)'}
    
    # Handle upload
    if triggered_by == 'upload-background' and contents is not None:
        if not contents.startswith('data:image/'):
            print("   Callback: Invalid format")
            return {'style': 'default (no background)'}
        
        # Valid upload - save immediately
        background_image_data = contents
        save_background(contents)
        print(f"   Callback: Background uploaded and saved ({len(contents)} chars)")
        return {'style': f'background with image ({len(contents)} chars)'}
    
    # Check if we have a loaded background to display
    # This is the key fix - always check background_image_data
    if background_image_data:
        print(f"   Callback: Using existing background_image_data ({len(background_image_data)} chars)")
        return {'style': f'background with image ({len(background_image_data)} chars)'}
    
    # Default
    print("   Callback: No background, using default")
    return {'style': 'default (no background)'}

def test_callback_persistence():
    """Test that callbacks maintain background persistence"""
    global background_image_data
    
    print("="*60)
    print("Testing Background Callback Persistence")
    print("="*60)
    
    # Clean start
    print("\n1. Clean state")
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    background_image_data = None
    
    # Initial callback (page load, no background)
    print("\n2. Initial page load (no saved background)")
    result = simulate_update_background_callback(triggered_by='interval')
    assert 'default' in result['style'], "Should show default background"
    print("   ✓ Correct: No background shown")
    
    # User uploads background
    print("\n3. User uploads background image")
    test_bg = "data:image/jpeg;base64,testdatahere"
    result = simulate_update_background_callback(contents=test_bg, triggered_by='upload-background')
    assert 'background with image' in result['style'], "Should show uploaded background"
    assert os.path.exists(BACKGROUND_PATH), "Background file should be saved"
    print("   ✓ Background uploaded and saved")
    
    # Simulate interval update (should persist)
    print("\n4. Interval update (should maintain background)")
    result = simulate_update_background_callback(triggered_by='interval')
    assert 'background with image' in result['style'], "Background should persist"
    print("   ✓ Background persisted through interval update")
    
    # Simulate app restart
    print("\n5. Simulate app restart")
    background_image_data = None  # Clear memory
    simulate_startup_load()  # Load from file
    assert background_image_data is not None, "Should load background from file"
    assert background_image_data == test_bg, "Loaded background should match uploaded"
    print("   ✓ Background loaded from file on restart")
    
    # Callback after restart
    print("\n6. Callback after restart (should show loaded background)")
    result = simulate_update_background_callback(triggered_by='interval')
    assert 'background with image' in result['style'], "Should show loaded background"
    print("   ✓ Background shown after restart")
    
    # Multiple interval updates (should keep persisting)
    print("\n7. Multiple interval updates")
    for i in range(5):
        result = simulate_update_background_callback(triggered_by='interval')
        assert 'background with image' in result['style'], f"Background should persist on update {i+1}"
    print("   ✓ Background persisted through 5 interval updates")
    
    # Remove background
    print("\n8. Remove background")
    result = simulate_update_background_callback(triggered_by='remove-background-button')
    assert 'default' in result['style'], "Should show default after removal"
    assert not os.path.exists(BACKGROUND_PATH), "Background file should be deleted"
    print("   ✓ Background removed successfully")
    
    # Callback after removal
    print("\n9. Callback after removal (should show default)")
    result = simulate_update_background_callback(triggered_by='interval')
    assert 'default' in result['style'], "Should still show default"
    print("   ✓ Default background shown after removal")
    
    # Cleanup
    print("\n10. Cleanup")
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    print("   ✓ Cleaned up test data")
    
    print("\n" + "="*60)
    print("✓ All callback persistence tests passed!")
    print("="*60)

if __name__ == '__main__':
    try:
        test_callback_persistence()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on failure
        if os.path.exists(USER_DATA_DIR):
            shutil.rmtree(USER_DATA_DIR)
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on failure
        if os.path.exists(USER_DATA_DIR):
            shutil.rmtree(USER_DATA_DIR)
        exit(1)
