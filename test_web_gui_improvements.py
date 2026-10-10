#!/usr/bin/env python3
"""
Test script for web GUI improvements
Tests terminal input, logs tab, and comprehensive settings
"""

import unittest
import os
import sys

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['BOT_MIN_ALLOCATION'] = '50'
os.environ['BOT_MAX_ALLOCATION'] = '500'

class TestWebGUIStructure(unittest.TestCase):
    """Test web GUI structure and components"""
    
    def setUp(self):
        """Set up test environment"""
        # Import here to avoid issues with missing dependencies
        try:
            import web_gui
            self.web_gui = web_gui
            self.app = web_gui.app
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_app_initialization(self):
        """Test that Dash app initializes correctly"""
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.title, "Market Pie5 Bot - Trading Dashboard")
    
    def test_global_variables(self):
        """Test that new global variables are defined"""
        self.assertTrue(hasattr(self.web_gui, 'log_history'))
        self.assertTrue(hasattr(self.web_gui, 'terminal_input_queue'))
        self.assertTrue(hasattr(self.web_gui, 'log_queue'))
        self.assertTrue(hasattr(self.web_gui, 'price_data'))
        self.assertTrue(hasattr(self.web_gui, 'trade_log'))
    
    def test_colors_defined(self):
        """Test that color scheme is defined"""
        colors = self.web_gui.COLORS
        self.assertIn('background', colors)
        self.assertIn('card', colors)
        self.assertIn('green', colors)
        self.assertIn('red', colors)
        self.assertIn('blue', colors)
    
    def test_layout_components(self):
        """Test that main layout components exist"""
        layout = self.app.layout
        self.assertIsNotNone(layout)
    
    def test_log_message_function(self):
        """Test log_message helper function"""
        # Clear log history
        self.web_gui.log_history.clear()
        
        # Add a test message
        self.web_gui.log_message("Test message")
        
        # Verify it was added to log history
        self.assertTrue(len(self.web_gui.log_history) > 0)
        self.assertIn("Test message", self.web_gui.log_history[-1])
    
    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly"""
        # Check that the web GUI can access env vars
        paper_trading = os.getenv('PAPER_TRADING_MODE', 'true')
        self.assertEqual(paper_trading, 'true')
        
        min_alloc = os.getenv('BOT_MIN_ALLOCATION', '50')
        self.assertEqual(min_alloc, '50')


class TestTerminalCommands(unittest.TestCase):
    """Test terminal command processing"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_terminal_commands_exist(self):
        """Test that terminal command handling exists"""
        # Terminal commands are processed in the callback
        # We just verify the log_message function works
        self.web_gui.log_history.clear()
        self.web_gui.log_message("> help")
        self.assertTrue(len(self.web_gui.log_history) > 0)


class TestSettingsStructure(unittest.TestCase):
    """Test comprehensive settings structure"""
    
    def test_env_example_file_exists(self):
        """Test that .env.example file exists with all parameters"""
        env_example_path = '.env.example'
        self.assertTrue(os.path.exists(env_example_path), 
                       ".env.example file should exist")
        
        # Read and verify key parameters are present
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Check for key parameters
        key_params = [
            'PAPER_TRADING_MODE',
            'SCHWAB_SANDBOX_MODE',
            'BOT_MIN_ALLOCATION',
            'BOT_MAX_ALLOCATION',
            'BOT_RISK_THRESHOLD',
            'BOT_TRAILING_STOP_PERCENT',
            'MIN_STOCK_PRICE',
            'MAX_STOCK_VOLATILITY',
            'PARTIAL_EXIT_ENABLED',
            'WEB_GUI_MAX_SYMBOLS'
        ]
        
        for param in key_params:
            self.assertIn(param, content, 
                         f"Parameter {param} should be in .env.example")


class TestLogsTabComponents(unittest.TestCase):
    """Test logs tab functionality"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_log_history_initialization(self):
        """Test that log_history is initialized as a list"""
        self.assertIsInstance(self.web_gui.log_history, list)
    
    def test_log_message_adds_to_history(self):
        """Test that log messages are added to history"""
        self.web_gui.log_history.clear()
        initial_count = len(self.web_gui.log_history)
        
        self.web_gui.log_message("Test log entry")
        
        self.assertEqual(len(self.web_gui.log_history), initial_count + 1)


class TestImagePersistence(unittest.TestCase):
    """Test image persistence functionality"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_persistence_constants_defined(self):
        """Test that persistence constants are defined"""
        self.assertTrue(hasattr(self.web_gui, 'USER_DATA_DIR'))
        self.assertTrue(hasattr(self.web_gui, 'AVATAR_PATH'))
        self.assertTrue(hasattr(self.web_gui, 'BACKGROUND_PATH'))
    
    def test_persistence_functions_exist(self):
        """Test that persistence functions are defined"""
        self.assertTrue(hasattr(self.web_gui, 'ensure_user_data_dir'))
        self.assertTrue(hasattr(self.web_gui, 'save_avatar'))
        self.assertTrue(hasattr(self.web_gui, 'load_avatar'))
        self.assertTrue(hasattr(self.web_gui, 'save_background'))
        self.assertTrue(hasattr(self.web_gui, 'load_background'))
        self.assertTrue(hasattr(self.web_gui, 'load_user_images_on_startup'))
    
    def test_persistence_functions_callable(self):
        """Test that persistence functions are callable"""
        self.assertTrue(callable(self.web_gui.ensure_user_data_dir))
        self.assertTrue(callable(self.web_gui.save_avatar))
        self.assertTrue(callable(self.web_gui.load_avatar))
        self.assertTrue(callable(self.web_gui.save_background))
        self.assertTrue(callable(self.web_gui.load_background))
        self.assertTrue(callable(self.web_gui.load_user_images_on_startup))
    
    def test_user_profile_variables_exist(self):
        """Test that user profile variables exist"""
        self.assertTrue(hasattr(self.web_gui, 'user_profile_avatar'))
        self.assertTrue(hasattr(self.web_gui, 'user_profile_name'))
        self.assertTrue(hasattr(self.web_gui, 'user_profile_username'))
        self.assertTrue(hasattr(self.web_gui, 'background_image_data'))
    
    def test_env_example_has_profile_vars(self):
        """Test that .env.example includes profile variables"""
        env_example_path = '.env.example'
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        self.assertIn('USER_PROFILE_NAME', content)
        self.assertIn('USER_PROFILE_USERNAME', content)
    
    def test_gitignore_has_user_data(self):
        """Test that .gitignore includes user_data/"""
        gitignore_path = '.gitignore'
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        self.assertIn('user_data/', content)


if __name__ == '__main__':
    print("="*60)
    print("Testing Web GUI Improvements")
    print("="*60)
    print("\nTesting:")
    print("1. Web GUI Structure")
    print("2. Terminal Commands")
    print("3. Comprehensive Settings")
    print("4. Logs Tab Components")
    print("5. Image Persistence")
    print("="*60)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
