"""
Integration test to verify web GUI mode selection properly configures the bot.
This simulates what happens when a user clicks a mode button in the web GUI.
"""

import unittest
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


@pytest.mark.integration
class TestWebGUIModeIntegration(unittest.TestCase):
    """Test that web GUI mode selection properly configures the bot"""
    
    def setUp(self):
        """Save original environment variables"""
        self.original_env = {}
        self.env_vars = ['PAPER_TRADING_MODE', 'SCHWAB_SANDBOX_MODE', 
                        'SCHWAB_API_ENABLED', 'ENABLE_PDT_RULES']
        for var in self.env_vars:
            self.original_env[var] = os.environ.get(var)
        
        # Set safe defaults for testing
        os.environ['ENABLE_PDT_RULES'] = 'false'
    
    def tearDown(self):
        """Restore original environment variables"""
        for var in self.env_vars:
            if self.original_env[var] is not None:
                os.environ[var] = self.original_env[var]
            elif var in os.environ:
                del os.environ[var]
    
    def test_sandbox_mode_button_click(self):
        """Simulate clicking Sandbox mode button in web GUI"""
        print("\n=== Testing Sandbox Mode Configuration ===")
        
        # This is what web_gui.py does when sandbox button is clicked (lines 2820-2824)
        mode_settings = {
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'true',
            'SCHWAB_API_ENABLED': 'on'
        }
        
        # Apply settings to environment
        for key, value in mode_settings.items():
            os.environ[key] = str(value)
        
        print(f"Applied settings: {mode_settings}")
        
        # Verify helper functions read the correct values
        self.assertTrue(main._get_paper_trading_mode(), 
                       "Sandbox mode: paper trading should be enabled")
        self.assertTrue(main._get_schwab_sandbox_mode(),
                       "Sandbox mode: sandbox should be enabled")
        self.assertTrue(main._get_schwab_api_enabled(),
                       "Sandbox mode: Schwab API should be enabled")
        
        # Create a bot and verify it reads the mode correctly
        bot = main.TradingBot(total_capital=10000.0)
        
        # In sandbox mode, _is_pure_simulation_mode should be False
        # because sandbox requires Schwab API, not pure simulation
        self.assertFalse(bot._is_pure_simulation_mode(),
                        "Sandbox mode is NOT pure simulation mode")
        
        print("✓ Sandbox mode configured correctly")
    
    def test_live_mode_button_click(self):
        """Simulate clicking Live mode button in web GUI"""
        print("\n=== Testing Live Mode Configuration ===")
        
        # This is what web_gui.py does when live button is clicked (lines 2828-2832)
        mode_settings = {
            'PAPER_TRADING_MODE': 'false',
            'SCHWAB_SANDBOX_MODE': 'false',
            'SCHWAB_API_ENABLED': 'on'
        }
        
        # Apply settings to environment
        for key, value in mode_settings.items():
            os.environ[key] = str(value)
        
        print(f"Applied settings: {mode_settings}")
        
        # Verify helper functions read the correct values
        self.assertFalse(main._get_paper_trading_mode(),
                        "Live mode: paper trading should be disabled")
        self.assertFalse(main._get_schwab_sandbox_mode(),
                        "Live mode: sandbox should be disabled")
        self.assertTrue(main._get_schwab_api_enabled(),
                       "Live mode: Schwab API should be enabled")
        
        # Create a bot and verify it reads the mode correctly
        bot = main.TradingBot(total_capital=10000.0)
        
        # In live mode, _is_pure_simulation_mode should be False
        self.assertFalse(bot._is_pure_simulation_mode(),
                        "Live mode is NOT pure simulation mode")
        
        print("✓ Live mode configured correctly")
    
    def test_training_mode_button_click(self):
        """Simulate clicking Training mode (yfinance) button in web GUI"""
        print("\n=== Testing Training Mode Configuration ===")
        
        # This is what web_gui.py does when yfinance button is clicked (lines 2836-2840)
        mode_settings = {
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'false',
            'SCHWAB_API_ENABLED': 'off'
        }
        
        # Apply settings to environment
        for key, value in mode_settings.items():
            os.environ[key] = str(value)
        
        print(f"Applied settings: {mode_settings}")
        
        # Verify helper functions read the correct values
        self.assertTrue(main._get_paper_trading_mode(),
                       "Training mode: paper trading should be enabled")
        self.assertFalse(main._get_schwab_sandbox_mode(),
                        "Training mode: sandbox should be disabled")
        self.assertFalse(main._get_schwab_api_enabled(),
                        "Training mode: Schwab API should be disabled")
        
        # Create a bot and verify it reads the mode correctly
        bot = main.TradingBot(total_capital=10000.0)
        
        # In training mode (API disabled), _is_pure_simulation_mode should be True
        self.assertTrue(bot._is_pure_simulation_mode(),
                       "Training mode IS pure simulation mode")
        
        # Bot should be using yfinance simulation
        self.assertTrue(bot.using_yfinance_sim,
                       "Training mode should use yfinance simulation")
        self.assertFalse(bot.schwab_api_available,
                        "Training mode should not have Schwab API available")
        
        print("✓ Training mode configured correctly")
    
    def test_mode_switch_runtime(self):
        """Test that mode can be changed at runtime (web GUI workflow)"""
        print("\n=== Testing Runtime Mode Switching ===")
        
        # Start in sandbox mode
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        
        print("Starting in Sandbox mode...")
        self.assertTrue(main._get_schwab_sandbox_mode())
        
        # Switch to training mode at runtime (like stopping bot and changing mode in GUI)
        print("Switching to Training mode...")
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        
        # Verify the helper functions immediately see the change
        self.assertFalse(main._get_schwab_sandbox_mode(),
                        "After switch: sandbox should be disabled")
        self.assertFalse(main._get_schwab_api_enabled(),
                        "After switch: API should be disabled")
        
        # Create a new bot instance (simulating what web_gui does after mode change)
        bot = main.TradingBot(total_capital=10000.0)
        self.assertTrue(bot._is_pure_simulation_mode(),
                       "After switch: bot should be in pure simulation mode")
        
        print("✓ Runtime mode switching works correctly")


if __name__ == '__main__':
    # Run with verbose output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWebGUIModeIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
