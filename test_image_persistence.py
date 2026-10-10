#!/usr/bin/env python3
"""
Test image persistence functionality
"""

import os
import shutil

# Mock the web_gui module's persistence functions
USER_DATA_DIR = 'test_user_data'
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

def test_avatar_persistence():
    """Test that avatar data is saved and loaded correctly"""
    print("Testing avatar persistence...")
    
    # Clean up any existing test data
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    
    # Test data
    test_avatar = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # Save avatar
    save_avatar(test_avatar)
    assert os.path.exists(AVATAR_PATH), "Avatar file was not created"
    
    # Load avatar
    loaded_avatar = load_avatar()
    assert loaded_avatar == test_avatar, "Loaded avatar does not match saved avatar"
    
    print("✓ Avatar persistence test passed")

def test_background_persistence():
    """Test that background data is saved and loaded correctly"""
    print("Testing background persistence...")
    
    # Test data
    test_background = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/AA=="
    
    # Save background
    save_background(test_background)
    assert os.path.exists(BACKGROUND_PATH), "Background file was not created"
    
    # Load background
    loaded_background = load_background()
    assert loaded_background == test_background, "Loaded background does not match saved background"
    
    print("✓ Background persistence test passed")

def test_load_nonexistent():
    """Test loading when files don't exist"""
    print("Testing load from nonexistent files...")
    
    # Clean up
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    
    # Try to load when files don't exist
    avatar = load_avatar()
    background = load_background()
    
    assert avatar is None, "Loading nonexistent avatar should return None"
    assert background is None, "Loading nonexistent background should return None"
    
    print("✓ Nonexistent file test passed")

def test_remove_background():
    """Test removing background file"""
    print("Testing background removal...")
    
    # Save a background first
    test_background = "data:image/jpeg;base64,testdata"
    save_background(test_background)
    assert os.path.exists(BACKGROUND_PATH), "Background file was not created"
    
    # Remove it
    if os.path.exists(BACKGROUND_PATH):
        os.remove(BACKGROUND_PATH)
    
    # Verify it's gone
    assert not os.path.exists(BACKGROUND_PATH), "Background file was not removed"
    
    # Load should return None now
    loaded = load_background()
    assert loaded is None, "Loading after removal should return None"
    
    print("✓ Background removal test passed")

def test_invalid_data_validation():
    """Test that invalid data is rejected"""
    print("Testing invalid data validation...")
    
    # Clean up
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    
    # Try to save invalid avatar data
    save_avatar("not a data url")
    assert not os.path.exists(AVATAR_PATH), "Should not save invalid avatar data"
    
    save_avatar(None)
    assert not os.path.exists(AVATAR_PATH), "Should not save None avatar data"
    
    save_avatar("")
    assert not os.path.exists(AVATAR_PATH), "Should not save empty avatar data"
    
    # Test incomplete data URLs
    save_avatar("data:image/")
    assert not os.path.exists(AVATAR_PATH), "Should not save incomplete avatar data URL (just prefix)"
    
    save_avatar("data:image/png")
    assert not os.path.exists(AVATAR_PATH), "Should not save incomplete avatar data URL (no base64)"
    
    save_avatar("data:image/png;base64,")
    assert not os.path.exists(AVATAR_PATH), "Should not save incomplete avatar data URL (no data)"
    
    # Try to save invalid background data
    save_background("not a data url")
    assert not os.path.exists(BACKGROUND_PATH), "Should not save invalid background data"
    
    save_background(None)
    assert not os.path.exists(BACKGROUND_PATH), "Should not save None background data"
    
    # Test incomplete background data URLs
    save_background("data:image/")
    assert not os.path.exists(BACKGROUND_PATH), "Should not save incomplete background data URL (just prefix)"
    
    save_background("data:image/jpeg;base64,")
    assert not os.path.exists(BACKGROUND_PATH), "Should not save incomplete background data URL (no data)"
    
    # Valid data should save
    valid_data = "data:image/png;base64,test"
    save_avatar(valid_data)
    assert os.path.exists(AVATAR_PATH), "Should save valid avatar data"
    
    save_background(valid_data)
    assert os.path.exists(BACKGROUND_PATH), "Should save valid background data"
    
    print("✓ Invalid data validation test passed")

def cleanup():
    """Clean up test data"""
    if os.path.exists(USER_DATA_DIR):
        shutil.rmtree(USER_DATA_DIR)
    print("Test cleanup complete")

if __name__ == '__main__':
    try:
        print("="*60)
        print("Running Image Persistence Tests")
        print("="*60)
        
        test_avatar_persistence()
        test_background_persistence()
        test_load_nonexistent()
        test_remove_background()
        test_invalid_data_validation()
        
        print("="*60)
        print("All tests passed! ✓")
        print("="*60)
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        exit(1)
    finally:
        cleanup()
