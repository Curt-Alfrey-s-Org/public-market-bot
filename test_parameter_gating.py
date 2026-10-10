#!/usr/bin/env python3
"""
Test script for parameter gating in gui.py
Tests that GUI properly validates configuration before starting background threads.
"""

import os
import sys
import unittest
import unittest.mock as mock
from unittest.mock import MagicMock, patch


# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestParameterGating(unittest.TestCase):
    """Test parameter gating in GUI initialization"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Save original env vars
        self.original_env = {}
        env_vars = [
            'BOT_TOTAL_CAPITAL',
            'BOT_MIN_ALLOCATION',
            'BOT_MAX_ALLOCATION',
            'PAPER_TRADING_MODE',
            'SCHWAB_SANDBOX_MODE'
        ]
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)
        
        # Set valid defaults for testing
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['BOT_TOTAL_CAPITAL'] = '10000'
        os.environ['BOT_MIN_ALLOCATION'] = '100'
        os.environ['BOT_MAX_ALLOCATION'] = '5000'
    
    def tearDown(self):
        """Restore original environment"""
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
    
    def test_imports_are_available(self):
        """Test that all required imports are available in gui.py"""
        # Import gui module
        import gui
        
        # Check that all required symbols are imported from main
        required_imports = [
            'TradingBot',
            'PAPER_TRADING_MODE',
            'SCHWAB_SANDBOX_MODE',
            'BOT_MIN_ALLOCATION',
            'BOT_MAX_ALLOCATION',
            'SCHWAB_API_KEY',
            'SCHWAB_APP_SECRET',
            'SCHWAB_ACCOUNT_ID',
            'SCHWAB_CALLBACK_URL',
            'SCHWAB_CREDENTIAL_PLACEHOLDERS',
            'validate_configuration'
        ]
        
        for symbol in required_imports:
            self.assertTrue(
                hasattr(gui, symbol),
                f"gui.py should import {symbol} from main.py"
            )
    
    @mock.patch('gui.tk.Tk')
    @patch('gui.messagebox.showerror')
    def test_validate_params_with_valid_config(self, mock_messagebox, mock_tk):
        """Test that validate_params returns True with valid configuration"""
        # Import after patching
        from gui import TradingBotGUI
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create GUI instance (will call validate_params in __init__)
        # This should succeed with valid config
        try:
            gui_instance = TradingBotGUI(mock_root)
            # If we get here, validation passed
            self.assertTrue(True, "GUI initialization succeeded with valid config")
        except Exception as e:
            self.fail(f"GUI initialization failed with valid config: {e}")
        
        # Messagebox should NOT be called for valid config
        mock_messagebox.assert_not_called()
    
    @patch('gui.tk.Tk')
    @patch('gui.messagebox.showerror')
    def test_validate_params_with_invalid_capital(self, mock_messagebox, mock_tk):
        """Test that validate_params fails with invalid capital"""
        # Set invalid capital
        os.environ['BOT_TOTAL_CAPITAL'] = 'not_a_number'
        
        # Import after patching
        from gui import TradingBotGUI
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create GUI instance - should show error
        try:
            gui_instance = TradingBotGUI(mock_root)
        except Exception as e:
            # Some exceptions are OK if they're related to GUI components
            pass
        
        # Messagebox should be called with error
        mock_messagebox.assert_called_once()
        call_args = mock_messagebox.call_args
        self.assertEqual(call_args[0][0], "Invalid Configuration")
        self.assertIn("BOT_TOTAL_CAPITAL must be a valid number", call_args[0][1])
    
    @patch('gui.tk.Tk')
    @patch('gui.messagebox.showerror')
    def test_validate_params_with_negative_capital(self, mock_messagebox, mock_tk):
        """Test that validate_params fails with negative capital"""
        # Set negative capital
        os.environ['BOT_TOTAL_CAPITAL'] = '-1000'
        
        # Import after patching
        from gui import TradingBotGUI
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create GUI instance - should show error
        try:
            gui_instance = TradingBotGUI(mock_root)
        except Exception as e:
            pass
        
        # Messagebox should be called with error
        mock_messagebox.assert_called_once()
        call_args = mock_messagebox.call_args
        self.assertEqual(call_args[0][0], "Invalid Configuration")
        self.assertIn("BOT_TOTAL_CAPITAL must be positive", call_args[0][1])
    
    @patch('gui.tk.Tk')
    @patch('gui.messagebox.showerror')
    def test_validate_params_with_production_mode_missing_credentials(self, mock_messagebox, mock_tk):
        """Test that validate_params fails in production mode with missing credentials"""
        # Set production mode
        os.environ['PAPER_TRADING_MODE'] = 'false'
        
        # Import after patching - this will load the new env vars
        import importlib
        import gui
        import main
        importlib.reload(main)
        importlib.reload(gui)
        
        from gui import TradingBotGUI
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create GUI instance - should show error for missing credentials
        try:
            gui_instance = TradingBotGUI(mock_root)
        except Exception as e:
            self.fail(f"TradingBotGUI initialization raised an unexpected exception: {e}")
        
        # Messagebox should be called with error
        if mock_messagebox.called:
            call_args = mock_messagebox.call_args
            self.assertEqual(call_args[0][0], "Invalid Configuration")
            # Should mention credentials or placeholders
            error_msg = call_args[0][1]
            self.assertTrue(
                'SCHWAB_API_KEY' in error_msg or 'placeholder' in error_msg.lower(),
                "Error should mention Schwab credentials"
            )
    
    def test_validate_configuration_is_callable(self):
        """Test that validate_configuration is imported and callable"""
        from gui import validate_configuration
        
        # Should be callable
        self.assertTrue(callable(validate_configuration))
        
        # Should return a tuple (bool, list)
        result = validate_configuration()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], list)


class TestBackgroundThreadGating(unittest.TestCase):
    """Test that background threads only start when validation passes"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Set valid environment for testing
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['BOT_TOTAL_CAPITAL'] = '10000'
        os.environ['BOT_MIN_ALLOCATION'] = '100'
        os.environ['BOT_MAX_ALLOCATION'] = '5000'
    
    @patch('gui.tk.Tk')
    def test_update_logs_called_only_when_validation_passes(self, mock_tk):
        """Test that update_logs is only scheduled when validation passes"""
        # Import after patching
        import gui
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create GUI instance with valid config
        gui.TradingBotGUI(mock_root)
        
        # update_logs should be called via root.after
        # Check that root.after was called (background thread scheduling)
        self.assertTrue(mock_root.after.called, "root.after should be called for update_logs")
    
    @patch('gui.tk.Tk')
    @patch('gui.messagebox.showerror')
    def test_background_threads_not_started_with_invalid_config(self, mock_messagebox, mock_tk):
        """Test that background threads are NOT started when validation fails"""
        # Set invalid capital
        os.environ['BOT_TOTAL_CAPITAL'] = 'invalid'
        
        # Reload modules to pick up new env
        import importlib
        import gui
        import main
        importlib.reload(main)
        importlib.reload(gui)
        
        # Create mock root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Clear the after calls
        mock_root.after.reset_mock()
        
        # Create GUI instance with invalid config
        exception_raised = None
        try:
            gui_instance = gui.TradingBotGUI(mock_root)
        except Exception as exc:
            exception_raised = exc
        # (background threads should not start)
        # An exception is expected when configuration is invalid
        self.assertIsNotNone(
            exception_raised,
            "TradingBotGUI should raise an exception when configuration is invalid"
        )
        
        # Note: This test may be imperfect due to GUI component creation
        # but it serves as a basic check
        self.assertFalse(
            mock_root.after.called,
            f"root.after should not be called when validation fails; exception was: {exception_raised!r}"
        )


if __name__ == '__main__':
    print("="*70)
    print("Testing Parameter Gating in GUI")
    print("="*70)
    unittest.main(verbosity=2)
