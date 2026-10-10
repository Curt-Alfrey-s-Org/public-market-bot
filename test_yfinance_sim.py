#!/usr/bin/env python3
"""
Test for yfinance simulation mode auto-fallback feature
Tests that bot automatically switches to yfinance sim when Schwab API is unavailable
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Set up test environment
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['SCHWAB_API_KEY'] = 'test_key'
os.environ['SCHWAB_APP_SECRET'] = 'test_secret'

# Import after setting env vars
from main import TradingBot, validate_api_connectivity

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestYfinanceSimMode(unittest.TestCase):
    """Test auto-fallback to yfinance simulation mode"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
        logger.info("Test bot initialized")
    
    def test_auto_fallback_on_schwab_failure(self):
        """Test that bot auto-switches to yfinance sim when Schwab API fails"""
        logger.info("\n=== Testing Auto-Fallback to yfinance Sim ===")
        # Force initial state (Schwab "available") so we test runtime fallback regardless of init/env
        self.bot.schwab_api_available = True
        self.bot.using_yfinance_sim = False
        # Ensure get_stock_price uses sandbox path: paper + sandbox + api_enabled
        with patch.dict(os.environ, {'PAPER_TRADING_MODE': 'true', 'SCHWAB_SANDBOX_MODE': 'true', 'SCHWAB_API_ENABLED': 'on'}):
            # Mock Schwab API to fail, yfinance to succeed
            with patch.object(self.bot, 'fetch_schwab_stock_price', return_value=None):
                with patch.object(self.bot, 'fetch_real_stock_price', return_value=(150.0, 1000000)):
                    # Try to get price - should trigger fallback
                    price, volume = self.bot.get_stock_price('AAPL', use_random_fallback=False)
                    # Verify fallback occurred
                    self.assertFalse(self.bot.schwab_api_available)
                    self.assertTrue(self.bot.using_yfinance_sim)
                    self.assertEqual(price, 150.0)
                    self.assertEqual(volume, 1000000)
        logger.info("✓ Auto-fallback successful: Schwab unavailable → yfinance sim")
    
    def test_trade_mode_tagging(self):
        """Test that trades are tagged with correct mode"""
        logger.info("\n=== Testing Trade Mode Tagging ===")
        self.bot.trade_history = []  # Isolate from DB-loaded trades
        self.bot.using_yfinance_sim = True
        # So record_trade uses 'yfinance_sim' (need api_enabled True to hit that branch)
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'on'}):
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, True)
        # Verify trade was tagged correctly
        self.assertEqual(len(self.bot.trade_history), 1)
        trade = self.bot.trade_history[0]
        self.assertEqual(trade['mode'], 'yfinance_sim')
        self.assertEqual(trade['symbol'], 'AAPL')
        
        logger.info("✓ Trade correctly tagged as 'yfinance_sim'")
    
    def test_separate_trade_filtering(self):
        """Test that trades can be filtered by mode"""
        logger.info("\n=== Testing Trade Mode Filtering ===")
        self.bot.trade_history = []  # Isolate from DB-loaded trades
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'on', 'PAPER_TRADING_MODE': 'true', 'SCHWAB_SANDBOX_MODE': 'true'}):
            self.bot.using_yfinance_sim = True
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, True)
            self.bot.record_trade('GOOGL', 'SELL', 5, 2800.0, False)
            self.bot.using_yfinance_sim = False
            self.bot.record_trade('MSFT', 'BUY', 20, 400.0, True)
        
        # Filter by mode
        sim_trades = self.bot.get_trades_by_mode('yfinance_sim')
        sandbox_trades = self.bot.get_trades_by_mode('schwab_sandbox')
        
        self.assertEqual(len(sim_trades), 2)
        self.assertEqual(len(sandbox_trades), 1)
        
        logger.info(f"✓ Filtered trades: {len(sim_trades)} sim, {len(sandbox_trades)} sandbox")
    
    def test_api_connectivity_validation_with_fallback(self):
        """Test API connectivity validation supports fallback"""
        logger.info("\n=== Testing API Connectivity Validation ===")
        
        # Mock Schwab API to fail, yfinance to succeed
        with patch.object(self.bot, 'fetch_schwab_stock_price', return_value=None):
            with patch.object(self.bot, 'fetch_real_stock_price', return_value=(150.0, 1000000)):
                is_connected, msg = validate_api_connectivity(self.bot)
                
                # Should succeed with yfinance fallback
                self.assertTrue(is_connected)
                self.assertIn('yfinance', msg.lower())
                self.assertTrue(self.bot.using_yfinance_sim)
                
                logger.info(f"✓ API validation: {msg}")
    
    def test_both_apis_unavailable(self):
        """Test behavior when both Schwab and yfinance are unavailable - should fall back to random sim"""
        logger.info("\n=== Testing Both APIs Unavailable (Random Fallback) ===")
        
        # Mock both APIs to fail
        with patch.object(self.bot, 'fetch_schwab_stock_price', return_value=None):
            with patch.object(self.bot, 'fetch_real_stock_price', return_value=None):
                is_connected, msg = validate_api_connectivity(self.bot)
                
                # Should succeed with random simulation fallback
                self.assertTrue(is_connected)
                self.assertIn('random', msg.lower())
                
                logger.info(f"✓ Fallback to random simulation works when both APIs unavailable")
                logger.info(f"  Message: {msg}")


class TestTradeHistorySaving(unittest.TestCase):
    """Test trade history saving with mode separation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
        self.test_filename = 'test_trade_history.json'
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)
    
    def test_save_trade_history(self):
        """Test saving trade history to file"""
        logger.info("\n=== Testing Trade History Saving ===")
        self.bot.trade_history = []  # Isolate from DB-loaded trades
        with patch.dict(os.environ, {'SCHWAB_API_ENABLED': 'on'}):
            self.bot.using_yfinance_sim = True
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, True)
            self.bot.record_trade('GOOGL', 'SELL', 5, 2800.0, False)
        # Save to file
        self.bot.save_trade_history(self.test_filename)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.test_filename))
        
        # Verify file content
        import json
        with open(self.test_filename, 'r') as f:
            data = json.load(f)
        
        self.assertIn('metadata', data)
        self.assertIn('trades', data)
        self.assertEqual(len(data['trades']), 2)
        self.assertEqual(data['trades'][0]['mode'], 'yfinance_sim')
        self.assertEqual(data['trades'][1]['mode'], 'yfinance_sim')
        # metadata.mode is from env (api_disabled/sandbox/simulation/live), not per-trade
        self.assertIn(data['metadata']['mode'], ('yfinance_sim', 'api_disabled', 'simulation', 'sandbox'))
        logger.info(f"✓ Trade history saved successfully to {self.test_filename}")
        logger.info(f"  Trades: {len(data['trades'])}")
        logger.info(f"  Mode: {data['metadata']['mode']}")


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("YFINANCE SIMULATION MODE - AUTO-FALLBACK TESTS")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestYfinanceSimMode))
    suite.addTests(loader.loadTestsFromTestCase(TestTradeHistorySaving))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
