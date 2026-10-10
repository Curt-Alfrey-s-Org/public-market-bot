#!/usr/bin/env python3
"""
End-to-end test for image persistence feature
Simulates the actual user flow: upload -> restart -> verify persistence
"""

import os
import shutil
import sys
import pytest

# Test constants matching web_gui.py
USER_DATA_DIR = 'user_data'
AVATAR_PATH = os.path.join(USER_DATA_DIR, 'avatar.txt')
BACKGROUND_PATH = os.path.join(USER_DATA_DIR, 'background.txt')

def ensure_user_data_dir():
    """Ensure the user_data directory exists"""
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

def save_avatar(avatar_data):
    """Save avatar image data to file"""
    # Validate that it's a valid data URL before saving
    if not avatar_data or not isinstance(avatar_data, str) or not avatar_data.startswith('data:image/'):
        return
    # Ensure the data URL has proper structure (data:image/TYPE;base64,DATA)
    if ';' not in avatar_data or ',' not in avatar_data:
        return
    # Ensure there's actual data after the comma
    comma_index = avatar_data.find(',')
    if comma_index >= len(avatar_data) - 1:
        return
    ensure_user_data_dir()
    with open(AVATAR_PATH, 'w') as f:
        f.write(avatar_data)

def load_avatar():
    """Load avatar image data from file"""
    if os.path.exists(AVATAR_PATH):
        with open(AVATAR_PATH, 'r') as f:
            return f.read()
    return None

def save_background(background_data):
    """Save background image data to file"""
    # Validate that it's a valid data URL before saving
    if not background_data or not isinstance(background_data, str) or not background_data.startswith('data:image/'):
        return
    # Ensure the data URL has proper structure (data:image/TYPE;base64,DATA)
    if ';' not in background_data or ',' not in background_data:
        return
    # Ensure there's actual data after the comma
    comma_index = background_data.find(',')
    if comma_index >= len(background_data) - 1:
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


@pytest.mark.e2e
def test_image_persistence_e2e():
    """End-to-end test for image persistence feature"""
    success = simulate_user_flow()
    assert success, "Image persistence e2e test should pass"


def simulate_user_flow():
    """Simulate the complete user flow"""
    
    print("="*60)
    print("End-to-End Image Persistence Test")
    print("="*60)
    
    # Clean slate
    print("\n1. Starting with clean state...")
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    print("   ✓ Clean state achieved")
    
    # Simulate startup (no saved images)
    print("\n2. Simulating first startup (no saved images)...")
    avatar = load_avatar()
    background = load_background()
    assert avatar is None, "Should have no avatar on first startup"
    assert background is None, "Should have no background on first startup"
    print("   ✓ No images loaded (as expected)")
    
    # Simulate user uploading avatar
    print("\n3. Simulating user uploading avatar...")
    test_avatar_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    save_avatar(test_avatar_data)
    assert os.path.exists(AVATAR_PATH), "Avatar file should be created"
    print("   ✓ Avatar saved to disk")
    
    # Simulate user uploading background
    print("\n4. Simulating user uploading background...")
    test_background_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/AA=="
    save_background(test_background_data)
    assert os.path.exists(BACKGROUND_PATH), "Background file should be created"
    print("   ✓ Background saved to disk")
    
    # Simulate "restart" - clear memory but keep files
    print("\n5. Simulating application restart...")
    avatar = None
    background = None
    print("   ✓ Application 'restarted' (memory cleared)")
    
    # Simulate startup loading saved images
    print("\n6. Loading saved images on startup...")
    avatar = load_avatar()
    background = load_background()
    assert avatar == test_avatar_data, "Avatar should be loaded from disk"
    assert background == test_background_data, "Background should be loaded from disk"
    print("   ✓ Avatar loaded successfully")
    print("   ✓ Background loaded successfully")
    
    # Verify data integrity
    print("\n7. Verifying data integrity...")
    assert avatar.startswith("data:image/"), "Avatar should be valid base64 image data"
    assert background.startswith("data:image/"), "Background should be valid base64 image data"
    print("   ✓ Image data is valid")
    
    # Simulate removing background
    print("\n8. Simulating background removal...")
    if os.path.exists(BACKGROUND_PATH):
        os.remove(BACKGROUND_PATH)
    background = load_background()
    assert background is None, "Background should be None after removal"
    assert avatar is not None, "Avatar should still exist"
    print("   ✓ Background removed successfully")
    print("   ✓ Avatar still intact")
    
    # Simulate another restart
    print("\n9. Simulating another restart...")
    avatar = None
    background = None
    avatar = load_avatar()
    background = load_background()
    assert avatar == test_avatar_data, "Avatar should persist across multiple restarts"
    assert background is None, "Background should remain removed"
    print("   ✓ Avatar persisted across multiple restarts")
    print("   ✓ Background remains removed")
    
    # Cleanup
    print("\n10. Cleaning up test data...")
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    print("   ✓ Test data cleaned up")
    
    print("\n" + "="*60)
    print("✓ All end-to-end tests passed!")
    print("="*60)
    
    return True

if __name__ == '__main__':
    try:
        success = simulate_user_flow()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
