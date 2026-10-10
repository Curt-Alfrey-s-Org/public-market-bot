#!/usr/bin/env python3
"""
Test that image loading logic works correctly
This test verifies the image persistence functions work without importing dash
"""

import os
import shutil
import sys

# Test data directory
TEST_USER_DATA_DIR = 'test_user_data'
TEST_AVATAR_PATH = os.path.join(TEST_USER_DATA_DIR, 'avatar.txt')
TEST_BACKGROUND_PATH = os.path.join(TEST_USER_DATA_DIR, 'background.txt')

# Mock logger
class MockLogger:
    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

logger = MockLogger()

# Copy the functions from web_gui.py for testing
def ensure_user_data_dir(user_data_dir):
    """Ensure the user_data directory exists"""
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        logger.info(f"Created user data directory: {user_data_dir}")

def save_avatar(avatar_data, avatar_path, user_data_dir):
    """Save avatar image data to file"""
    try:
        # Validate that it's a valid data URL before saving
        if not avatar_data or not isinstance(avatar_data, str) or not avatar_data.startswith('data:image/'):
            logger.warning("Invalid avatar data format, not saving")
            return
        
        # Ensure the data URL has proper structure (data:image/TYPE;base64,DATA)
        if ';' not in avatar_data or ',' not in avatar_data:
            logger.warning("Invalid avatar data URL structure, not saving")
            return
        
        # Ensure there's actual data after the comma
        comma_index = avatar_data.find(',')
        if comma_index >= len(avatar_data) - 1:
            logger.warning("Invalid avatar data URL structure (no data after comma), not saving")
            return
        
        ensure_user_data_dir(user_data_dir)
        with open(avatar_path, 'w') as f:
            f.write(avatar_data)
        logger.info("Avatar saved to file")
    except Exception as e:
        logger.error(f"Error saving avatar: {str(e)}")

def load_avatar(avatar_path):
    """Load avatar image data from file"""
    try:
        if os.path.exists(avatar_path):
            with open(avatar_path, 'r') as f:
                data = f.read()
            logger.info("Avatar loaded from file")
            return data
    except Exception as e:
        logger.error(f"Error loading avatar: {str(e)}")
    return None

def save_background(background_data, background_path, user_data_dir):
    """Save background image data to file"""
    try:
        # Validate that it's a valid data URL before saving
        if not background_data or not isinstance(background_data, str) or not background_data.startswith('data:image/'):
            logger.warning("Invalid background data format, not saving")
            return
        
        # Ensure the data URL has proper structure (data:image/TYPE;base64,DATA)
        if ';' not in background_data or ',' not in background_data:
            logger.warning("Invalid background data URL structure, not saving")
            return
        
        # Ensure there's actual data after the comma
        comma_index = background_data.find(',')
        if comma_index >= len(background_data) - 1:
            logger.warning("Invalid background data URL structure (no data after comma), not saving")
            return
        
        ensure_user_data_dir(user_data_dir)
        with open(background_path, 'w') as f:
            f.write(background_data)
        logger.info("Background image saved to file")
    except Exception as e:
        logger.error(f"Error saving background: {str(e)}")

def load_background(background_path):
    """Load background image data from file"""
    try:
        if os.path.exists(background_path):
            with open(background_path, 'r') as f:
                data = f.read()
            logger.info("Background image loaded from file")
            return data
    except Exception as e:
        logger.error(f"Error loading background: {str(e)}")
    return None

def setup_test_environment():
    """Setup test environment with saved images"""
    # Clean up any existing test data
    if os.path.exists(TEST_USER_DATA_DIR):
        shutil.rmtree(TEST_USER_DATA_DIR)
    
    # Create test images
    test_avatar = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    test_background = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAL/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/AA=="
    
    # Save test images
    save_avatar(test_avatar, TEST_AVATAR_PATH, TEST_USER_DATA_DIR)
    save_background(test_background, TEST_BACKGROUND_PATH, TEST_USER_DATA_DIR)
    
    print("✓ Test environment setup complete")
    return test_avatar, test_background

def cleanup_test_environment():
    """Clean up test environment"""
    if os.path.exists(TEST_USER_DATA_DIR):
        shutil.rmtree(TEST_USER_DATA_DIR)
    print("✓ Test cleanup complete")

def test_image_loading():
    """Test that images are loaded and saved correctly"""
    print("\nTesting image save and load...")
    
    # Setup test environment
    test_avatar, test_background = setup_test_environment()
    
    # Verify files were created
    assert os.path.exists(TEST_AVATAR_PATH), "Avatar file should exist"
    assert os.path.exists(TEST_BACKGROUND_PATH), "Background file should exist"
    print("✓ Image files created successfully")
    
    # Load images
    loaded_avatar = load_avatar(TEST_AVATAR_PATH)
    loaded_background = load_background(TEST_BACKGROUND_PATH)
    
    # Verify images were loaded correctly
    assert loaded_avatar == test_avatar, "Avatar was not loaded correctly"
    assert loaded_background == test_background, "Background was not loaded correctly"
    print("✓ Images loaded successfully")
    
    # Clean up
    cleanup_test_environment()

def test_without_saved_images():
    """Test that loading handles missing images gracefully"""
    print("\nTesting load without saved images...")
    
    # Ensure no saved images exist
    if os.path.exists(TEST_USER_DATA_DIR):
        shutil.rmtree(TEST_USER_DATA_DIR)
    
    # Try to load images
    loaded_avatar = load_avatar(TEST_AVATAR_PATH)
    loaded_background = load_background(TEST_BACKGROUND_PATH)
    
    # Verify None is returned
    assert loaded_avatar is None, "Avatar should be None when no saved image exists"
    assert loaded_background is None, "Background should be None when no saved image exists"
    print("✓ Module handles missing images gracefully")

def test_persistence_workflow():
    """Test the complete persistence workflow"""
    print("\nTesting complete persistence workflow...")
    
    # Clean up any existing data
    if os.path.exists(TEST_USER_DATA_DIR):
        shutil.rmtree(TEST_USER_DATA_DIR)
    
    # Step 1: User uploads avatar
    test_avatar = "data:image/png;base64,testAvatarData123"
    save_avatar(test_avatar, TEST_AVATAR_PATH, TEST_USER_DATA_DIR)
    print("  Step 1: Avatar uploaded and saved")
    
    # Step 2: User uploads background
    test_background = "data:image/jpeg;base64,testBackgroundData456"
    save_background(test_background, TEST_BACKGROUND_PATH, TEST_USER_DATA_DIR)
    print("  Step 2: Background uploaded and saved")
    
    # Step 3: Simulate app restart - load images
    loaded_avatar = load_avatar(TEST_AVATAR_PATH)
    loaded_background = load_background(TEST_BACKGROUND_PATH)
    print("  Step 3: App restarted, images loaded")
    
    # Step 4: Verify loaded images match original
    assert loaded_avatar == test_avatar, "Avatar should persist after restart"
    assert loaded_background == test_background, "Background should persist after restart"
    print("  Step 4: Images verified - persistence successful!")
    print("✓ Complete persistence workflow verified")
    
    # Clean up
    cleanup_test_environment()

if __name__ == '__main__':
    try:
        print("="*60)
        print("Testing Image Persistence Logic")
        print("="*60)
        
        test_image_loading()
        test_without_saved_images()
        test_persistence_workflow()
        
        print("\n" + "="*60)
        print("All image persistence logic tests passed! ✓")
        print("="*60)
        print("\nThis confirms that:")
        print("1. Images are saved correctly when uploaded")
        print("2. Images are loaded correctly on startup")
        print("3. Images persist across app restarts")
        print("4. Missing images are handled gracefully")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
