#!/usr/bin/env python3
"""
Test script to verify that validation gaps are fixed.
Tests the 7 previously unvalidated environment variables.
"""

import os
import sys
import unittest

# Set required environment variables to valid defaults first
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['ENABLE_PDT_RULES'] = 'false'

# Import after setting env vars
import main


class TestValidationGaps(unittest.TestCase):
    """Test that previously missing validations now work correctly"""
    
    def setUp(self):
        """Set up valid configuration before each test"""
        main.setup_logging()
        
        # Set all variables to valid values
        os.environ['BOT_POSITION_SIZE'] = '0.01'
        os.environ['BOT_RISK_FREE_RATE'] = '0.01'
        os.environ['BOT_STOP_LOSS_PERCENT'] = '0.06'
        os.environ['HIGH_SALE_PERCENT'] = '0.10'
        os.environ['MAX_DISCOVERED_STOCKS'] = '10'
        os.environ['PARTIAL_EXIT_STOP_TIGHTENING'] = '0.8'
        os.environ['SWING_MIN_HOLD_DAYS'] = '1'
        
        # Set placeholder API keys to avoid validation errors
        os.environ['ALPHA_VANTAGE_API_KEY'] = 'test_alpha_vantage_key'
        os.environ['NEWS_API_KEY'] = 'test_news_api_key'
        os.environ['FINNHUB_API_KEY'] = 'test_finnhub_key'
        
        # Set other required variables
        os.environ['BOT_RISK_THRESHOLD'] = '0.06'
        os.environ['BOT_MIN_ALLOCATION'] = '50'
        os.environ['BOT_MAX_ALLOCATION'] = '500'
        os.environ['BOT_TRAILING_STOP_PERCENT'] = '0.03'
        os.environ['VOLATILITY_WINDOW'] = '20'
        os.environ['MIN_STOCK_PRICE'] = '5.0'
        os.environ['MAX_STOCK_PRICE'] = '1000.0'
        os.environ['MIN_DAILY_VOLUME'] = '500000'
        os.environ['MAX_STOCK_VOLATILITY'] = '0.15'
        os.environ['MIN_TRAILING_STOP'] = '0.02'
        os.environ['MAX_TRAILING_STOP'] = '0.10'
        os.environ['PARTIAL_EXIT_PERCENTAGE'] = '0.5'
        os.environ['SIMULATED_WIN_RATE'] = '0.6'
        os.environ['VOLATILITY_NORMALIZATION_MIN'] = '0.01'
        os.environ['VOLATILITY_NORMALIZATION_RANGE'] = '0.19'
        os.environ['CAPITAL_FLOOR_PERCENT'] = '0.10'
        os.environ['BOT_MAX_OPEN_POSITIONS'] = '5'
        os.environ['BOT_MAX_CONSECUTIVE_LOSSES'] = '3'
        os.environ['TRADING_FREQUENCY'] = '2'
        os.environ['BOT_ENABLE_THROTTLING'] = 'true'
        os.environ['BOT_MAX_CPU_PERCENT'] = '75'
        os.environ['BOT_MAX_MEMORY_PERCENT'] = '75'
        os.environ['BOT_THROTTLE_DELAY'] = '5'
    
    def _reload_and_validate(self):
        """Helper method to reload main module and run validation"""
        import importlib
        importlib.reload(main)
        return main.validate_configuration()
    
    def test_valid_configuration_passes(self):
        """Test that a valid configuration passes validation"""
        is_valid, issues = self._reload_and_validate()
        self.assertTrue(is_valid, f"Valid configuration failed: {issues}")
        self.assertEqual(len(issues), 0, f"Expected no issues, got: {issues}")
    
    def test_bot_position_size_invalid_negative(self):
        """Test that BOT_POSITION_SIZE rejects negative values"""
        os.environ['BOT_POSITION_SIZE'] = '-0.01'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative BOT_POSITION_SIZE should be invalid")
        self.assertTrue(any('BOT_POSITION_SIZE' in issue for issue in issues),
                        f"Expected BOT_POSITION_SIZE error, got: {issues}")
    
    def test_bot_position_size_invalid_too_large(self):
        """Test that BOT_POSITION_SIZE rejects values > 1"""
        os.environ['BOT_POSITION_SIZE'] = '1.5'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "BOT_POSITION_SIZE > 1 should be invalid")
        self.assertTrue(any('BOT_POSITION_SIZE' in issue for issue in issues),
                        f"Expected BOT_POSITION_SIZE error, got: {issues}")
    
    def test_bot_risk_free_rate_invalid_negative(self):
        """Test that BOT_RISK_FREE_RATE rejects negative values"""
        os.environ['BOT_RISK_FREE_RATE'] = '-0.01'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative BOT_RISK_FREE_RATE should be invalid")
        self.assertTrue(any('BOT_RISK_FREE_RATE' in issue for issue in issues),
                        f"Expected BOT_RISK_FREE_RATE error, got: {issues}")
    
    def test_bot_risk_free_rate_invalid_too_large(self):
        """Test that BOT_RISK_FREE_RATE rejects values > 1"""
        os.environ['BOT_RISK_FREE_RATE'] = '1.5'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "BOT_RISK_FREE_RATE > 1 should be invalid")
        self.assertTrue(any('BOT_RISK_FREE_RATE' in issue for issue in issues),
                        f"Expected BOT_RISK_FREE_RATE error, got: {issues}")
    
    def test_bot_stop_loss_percent_invalid_negative(self):
        """Test that BOT_STOP_LOSS_PERCENT rejects negative values"""
        os.environ['BOT_STOP_LOSS_PERCENT'] = '-0.05'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative BOT_STOP_LOSS_PERCENT should be invalid")
        self.assertTrue(any('BOT_STOP_LOSS_PERCENT' in issue for issue in issues),
                        f"Expected BOT_STOP_LOSS_PERCENT error, got: {issues}")
    
    def test_bot_stop_loss_percent_invalid_too_large(self):
        """Test that BOT_STOP_LOSS_PERCENT rejects values > 1"""
        os.environ['BOT_STOP_LOSS_PERCENT'] = '1.2'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "BOT_STOP_LOSS_PERCENT > 1 should be invalid")
        self.assertTrue(any('BOT_STOP_LOSS_PERCENT' in issue for issue in issues),
                        f"Expected BOT_STOP_LOSS_PERCENT error, got: {issues}")
    
    def test_high_sale_percent_invalid_negative(self):
        """Test that HIGH_SALE_PERCENT rejects negative values"""
        os.environ['HIGH_SALE_PERCENT'] = '-0.10'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative HIGH_SALE_PERCENT should be invalid")
        self.assertTrue(any('HIGH_SALE_PERCENT' in issue for issue in issues),
                        f"Expected HIGH_SALE_PERCENT error, got: {issues}")
    
    def test_high_sale_percent_invalid_too_large(self):
        """Test that HIGH_SALE_PERCENT rejects values > 1"""
        os.environ['HIGH_SALE_PERCENT'] = '2.0'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "HIGH_SALE_PERCENT > 1 should be invalid")
        self.assertTrue(any('HIGH_SALE_PERCENT' in issue for issue in issues),
                        f"Expected HIGH_SALE_PERCENT error, got: {issues}")
    
    def test_max_discovered_stocks_invalid_negative(self):
        """Test that MAX_DISCOVERED_STOCKS rejects negative values"""
        os.environ['MAX_DISCOVERED_STOCKS'] = '-5'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative MAX_DISCOVERED_STOCKS should be invalid")
        self.assertTrue(any('MAX_DISCOVERED_STOCKS' in issue for issue in issues),
                        f"Expected MAX_DISCOVERED_STOCKS error, got: {issues}")
    
    def test_max_discovered_stocks_invalid_zero(self):
        """Test that MAX_DISCOVERED_STOCKS rejects zero"""
        os.environ['MAX_DISCOVERED_STOCKS'] = '0'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "MAX_DISCOVERED_STOCKS = 0 should be invalid")
        self.assertTrue(any('MAX_DISCOVERED_STOCKS' in issue for issue in issues),
                        f"Expected MAX_DISCOVERED_STOCKS error, got: {issues}")
    
    def test_partial_exit_stop_tightening_invalid_negative(self):
        """Test that PARTIAL_EXIT_STOP_TIGHTENING rejects negative values"""
        os.environ['PARTIAL_EXIT_STOP_TIGHTENING'] = '-0.2'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative PARTIAL_EXIT_STOP_TIGHTENING should be invalid")
        self.assertTrue(any('PARTIAL_EXIT_STOP_TIGHTENING' in issue for issue in issues),
                        f"Expected PARTIAL_EXIT_STOP_TIGHTENING error, got: {issues}")
    
    def test_partial_exit_stop_tightening_invalid_too_large(self):
        """Test that PARTIAL_EXIT_STOP_TIGHTENING rejects values > 1"""
        os.environ['PARTIAL_EXIT_STOP_TIGHTENING'] = '1.5'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "PARTIAL_EXIT_STOP_TIGHTENING > 1 should be invalid")
        self.assertTrue(any('PARTIAL_EXIT_STOP_TIGHTENING' in issue for issue in issues),
                        f"Expected PARTIAL_EXIT_STOP_TIGHTENING error, got: {issues}")
    
    def test_swing_hold_min_days_invalid_negative(self):
        """Test that SWING_MIN_HOLD_DAYS rejects negative values"""
        os.environ['SWING_MIN_HOLD_DAYS'] = '-1'
        is_valid, issues = self._reload_and_validate()
        self.assertFalse(is_valid, "Negative SWING_MIN_HOLD_DAYS should be invalid")
        self.assertTrue(any('SWING_MIN_HOLD_DAYS' in issue for issue in issues),
                        f"Expected SWING_MIN_HOLD_DAYS error, got: {issues}")
    
    def test_swing_hold_min_days_accepts_zero(self):
        """Test that SWING_MIN_HOLD_DAYS accepts zero (day trading mode)"""
        os.environ['SWING_MIN_HOLD_DAYS'] = '0'
        is_valid, issues = self._reload_and_validate()
        self.assertTrue(is_valid, f"SWING_MIN_HOLD_DAYS = 0 should be valid: {issues}")


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestValidationGaps)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
