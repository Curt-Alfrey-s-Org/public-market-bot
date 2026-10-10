#!/usr/bin/env python3
"""
Test for SCHWAB_API_ENABLED environment variable functionality
Tests that the bot correctly respects the API on/off toggle
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Set test environment variables before importing main
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'

# Import after setting env vars
import main


class TestSchwabApiToggle(unittest.TestCase):
    """Test SCHWAB_API_ENABLED functionality"""
    
    def test_env_var_parsing(self):
        """Test that SCHWAB_API_ENABLED is parsed correctly"""
        # Test 'off' value
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'off'}):
            import importlib
            importlib.reload(main)
            self.assertFalse(main.SCHWAB_API_ENABLED)
        
        # Test 'false' value
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'false'}):
            importlib.reload(main)
            self.assertFalse(main.SCHWAB_API_ENABLED)
        
        # Test 'on' value
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'on'}):
            importlib.reload(main)
            self.assertTrue(main.SCHWAB_API_ENABLED)
        
        # Test 'true' value
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'true'}):
            importlib.reload(main)
            self.assertTrue(main.SCHWAB_API_ENABLED)
        
        # Test default value (should be 'on')
        with patch.dict(os.environ, {}, clear=True):
            # Clear and reload
            if 'SCHWAB_API_ENABLED' in os.environ:
                del os.environ['SCHWAB_API_ENABLED']
            importlib.reload(main)
            self.assertTrue(main.SCHWAB_API_ENABLED)
    
    def test_api_disabled_initialization(self):
        """Test that bot initializes correctly with API disabled"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'false'
        }):
            import importlib
            importlib.reload(main)
            
            bot = main.TradingBot(total_capital=10000.0)
            
            # When API is disabled, these flags should be set
            self.assertFalse(bot.schwab_api_available)
            self.assertTrue(bot.using_yfinance_sim)
            self.assertIsNone(bot.schwab_authenticator)
    
    def test_api_enabled_skips_schwab_in_get_stock_price(self):
        """Test that get_stock_price skips Schwab when API disabled"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'true'
        }):
            import importlib
            importlib.reload(main)
            
            bot = main.TradingBot(total_capital=10000.0)
            
            # Mock fetch_schwab_stock_price and fetch_real_stock_price
            bot.fetch_schwab_stock_price = MagicMock(return_value=(100.0, 1000000))
            bot.fetch_real_stock_price = MagicMock(return_value=(101.0, 1100000))
            
            # Call get_stock_price
            price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
            
            # Should NOT call Schwab API when disabled
            bot.fetch_schwab_stock_price.assert_not_called()
            
            # Should call yfinance
            bot.fetch_real_stock_price.assert_called_once_with('AAPL')
            
            # Should return yfinance price
            self.assertEqual(price, 101.0)
            self.assertEqual(volume, 1100000)
    
    def test_api_enabled_uses_schwab(self):
        """Test that get_stock_price uses Schwab when API enabled"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'on',
            'PAPER_TRADING_MODE': 'true',
            'SCHWAB_SANDBOX_MODE': 'true'
        }):
            import importlib
            importlib.reload(main)
            
            bot = main.TradingBot(total_capital=10000.0)
            
            # Mock fetch_schwab_stock_price
            bot.fetch_schwab_stock_price = MagicMock(return_value=(100.0, 1000000))
            bot.fetch_real_stock_price = MagicMock(return_value=(101.0, 1100000))
            
            # Call get_stock_price
            price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
            
            # Should call Schwab API when enabled in sandbox mode
            bot.fetch_schwab_stock_price.assert_called_once_with('AAPL')
            
            # Should NOT call yfinance (Schwab succeeded)
            bot.fetch_real_stock_price.assert_not_called()
            
            # Should return Schwab price
            self.assertEqual(price, 100.0)
            self.assertEqual(volume, 1000000)
    
    def test_validate_api_connectivity_api_disabled(self):
        """Test validate_api_connectivity when API disabled"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'true'
        }):
            import importlib
            importlib.reload(main)
            
            bot = main.TradingBot(total_capital=10000.0)
            
            # Mock yfinance price fetch
            bot.fetch_real_stock_price = MagicMock(return_value=(100.0, 1000000))
            
            # Validate connectivity
            is_connected, message = main.validate_api_connectivity(bot)
            
            # Should succeed
            self.assertTrue(is_connected)
            self.assertIn("Schwab API disabled", message)
            self.assertIn("yfinance", message.lower())
    
    def test_live_mode_with_api_disabled_fails_validation(self):
        """Test that live mode with API disabled fails validation"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'false'  # Live mode
        }):
            import importlib
            importlib.reload(main)
            
            is_valid, issues = main.validate_configuration()
            
            # Should fail validation
            self.assertFalse(is_valid)
            
            # Should have an issue about live mode + API disabled
            self.assertTrue(any('LIVE mode' in issue and 'SCHWAB_API_ENABLED' in issue for issue in issues))
    
    def test_paper_mode_with_api_disabled_passes_validation(self):
        """Test that paper mode with API disabled passes validation"""
        with patch.dict(os.environ, {
            'SCHWAB_API_ENABLED': 'off',
            'PAPER_TRADING_MODE': 'true'
        }):
            import importlib
            importlib.reload(main)
            
            is_valid, issues = main.validate_configuration()
            
            # Should pass validation (or only have unrelated issues)
            # Filter out issues not related to SCHWAB_API_ENABLED
            api_related_issues = [i for i in issues if 'SCHWAB_API_ENABLED' in i]
            self.assertEqual(len(api_related_issues), 0)


def run_tests():
    """Run all tests"""
    print("="*60)
    print("Testing SCHWAB_API_ENABLED functionality")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSchwabApiToggle)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
