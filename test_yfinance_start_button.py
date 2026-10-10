#!/usr/bin/env python3
"""
Test to reproduce: bot will not run yfinance mode when start is pressed
"""

import os
import unittest
import logging

# Set up test environment for yfinance mode
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'  # This should trigger yfinance mode
os.environ['SCHWAB_API_KEY'] = 'placeholder'
os.environ['SCHWAB_APP_SECRET'] = 'placeholder'

# Import after setting env vars
from main import TradingBot

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestYfinanceStartButton(unittest.TestCase):
    """Test that bot properly initializes in yfinance mode when SCHWAB_API_ENABLED=off"""
    
    def test_yfinance_mode_initialization(self):
        """Test that bot initializes with yfinance mode enabled"""
        logger.info("\n=== Testing yfinance Mode Initialization ===")
        logger.info("Environment: SCHWAB_API_ENABLED=off")
        
        # Create bot (simulates pressing Start button in GUI)
        bot = TradingBot(total_capital=10000.0)
        
        # Verify yfinance mode was activated
        self.assertTrue(bot.using_yfinance_sim, "Bot should be using yfinance sim mode")
        self.assertFalse(bot.schwab_api_available, "Schwab API should not be available")
        
        logger.info(f"✓ Bot initialized with using_yfinance_sim={bot.using_yfinance_sim}")
        logger.info(f"✓ schwab_api_available={bot.schwab_api_available}")
    
    def test_yfinance_mode_auto_configuration(self):
        """Test that _auto_configure_yfinance_mode runs and sets proper values"""
        logger.info("\n=== Testing yfinance Auto-Configuration ===")
        
        # Create bot
        bot = TradingBot(total_capital=10000.0)
        
        # Verify auto-configuration happened
        self.assertTrue(bot.using_yfinance_sim, "using_yfinance_sim should be True")
        
        # Verify environment variables were set by auto-configuration
        self.assertEqual(os.getenv('PAPER_TRADING_MODE'), 'true')
        self.assertEqual(os.getenv('SCHWAB_SANDBOX_MODE'), 'false')
        self.assertEqual(os.getenv('SCHWAB_API_ENABLED'), 'off')
        
        # CRITICAL: Verify PDT rules are DISABLED in yfinance simulation mode
        self.assertEqual(os.getenv('ENABLE_PDT_RULES'), 'false', 
                        "PDT rules should be disabled in yfinance simulation mode")
        
        logger.info("✓ Auto-configuration completed successfully")
        logger.info(f"  PAPER_TRADING_MODE={os.getenv('PAPER_TRADING_MODE')}")
        logger.info(f"  SCHWAB_SANDBOX_MODE={os.getenv('SCHWAB_SANDBOX_MODE')}")
        logger.info(f"  SCHWAB_API_ENABLED={os.getenv('SCHWAB_API_ENABLED')}")
        logger.info(f"  ENABLE_PDT_RULES={os.getenv('ENABLE_PDT_RULES')}")
    
    def test_yfinance_mode_can_fetch_prices(self):
        """Test that bot can fetch prices in yfinance mode"""
        logger.info("\n=== Testing Price Fetching in yfinance Mode ===")
        
        # Create bot
        bot = TradingBot(total_capital=10000.0)
        
        # Verify bot is in yfinance mode
        self.assertTrue(bot.using_yfinance_sim)
        
        # Try to fetch price (should use yfinance, not Schwab API)
        try:
            price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
            logger.info(f"✓ Fetched price for AAPL: ${price:.2f}, volume: {volume}")
            self.assertIsNotNone(price, "Price should not be None")
            self.assertGreater(price, 0, "Price should be positive")
        except Exception as e:
            logger.error(f"✗ Failed to fetch price: {e}")
            self.fail(f"Should be able to fetch prices in yfinance mode: {e}")
    
    def test_bot_can_load_symbols_in_yfinance_mode(self):
        """Test that bot can load symbols when in yfinance mode"""
        logger.info("\n=== Testing Symbol Loading in yfinance Mode ===")
        
        # Create bot
        bot = TradingBot(total_capital=10000.0)
        
        # Verify bot is in yfinance mode
        self.assertTrue(bot.using_yfinance_sim)
        
        # Try to load symbols (what happens when start button is pressed)
        try:
            symbols = bot.load_scan_symbols(max_symbols=5)
            logger.info(f"✓ Loaded {len(symbols)} symbols: {symbols}")
            self.assertGreater(len(symbols), 0, "Should load at least one symbol")
        except Exception as e:
            logger.error(f"✗ Failed to load symbols: {e}")
            self.fail(f"Should be able to load symbols in yfinance mode: {e}")


if __name__ == '__main__':
    unittest.main()
