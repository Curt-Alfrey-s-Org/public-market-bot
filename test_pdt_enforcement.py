"""
Test PDT enforcement logic across different trading modes
Validates that PDT rules are only enforced in production mode
"""

import os
import sys
import unittest
from unittest.mock import patch

# Import the trading bot
from main import TradingBot


class TestPDTEnforcement(unittest.TestCase):
    """Test PDT enforcement in different trading modes"""
    
    def test_pdt_not_enforced_in_paper_mode(self):
        """Test that PDT rules are NOT enforced in paper trading mode"""
        # Simulate being in paper trading mode
        with patch('main.PAPER_TRADING_MODE', True):
            bot = TradingBot(total_capital=500.0)  # Less than $25k
            
            # Add 3 day trades (which would normally trigger PDT limit)
            for i in range(3):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should allow trading in paper mode
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertTrue(can_trade, "PDT should not be enforced in paper mode")
            self.assertIn("disabled", msg.lower(), "Message should indicate PDT is disabled")
            # Should mention either sandbox or simulation mode
            self.assertTrue("sandbox" in msg.lower() or "simulation" in msg.lower(), 
                          "Message should mention sandbox or simulation mode")
    
    def test_pdt_not_enforced_in_sandbox_mode(self):
        """Test that PDT rules are NOT enforced in sandbox mode"""
        # Simulate being in sandbox mode (which is a type of paper trading)
        with patch('main.PAPER_TRADING_MODE', True):
            with patch('main.SCHWAB_SANDBOX_MODE', True):
                bot = TradingBot(total_capital=500.0)  # Less than $25k
                
                # Add 3 day trades (which would normally trigger PDT limit)
                for i in range(3):
                    bot.add_day_trade(f"TEST{i}")
                
                # Check PDT compliance - should allow trading in sandbox mode
                can_trade, msg = bot.check_pdt_compliance()
                
                self.assertTrue(can_trade, "PDT should not be enforced in sandbox mode")
                self.assertIn("disabled", msg.lower(), "Message should indicate PDT is disabled")
                self.assertIn("sandbox mode", msg.lower(), "Message should specifically mention sandbox mode")
    
    def test_pdt_enforced_in_production_mode(self):
        """Test that PDT rules ARE enforced in production/live mode"""
        # Simulate being in production mode
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=500.0)  # Less than $25k
            
            # Add 3 day trades (should trigger PDT limit)
            for i in range(3):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should block trading in production mode
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertFalse(can_trade, "PDT should be enforced in production mode")
            self.assertIn("PDT Limit Reached", msg, "Message should indicate PDT limit reached")
    
    def test_pdt_allows_trading_under_limit_in_production(self):
        """Test that PDT allows trading when under the 3-trade limit in production"""
        # Simulate being in production mode
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=500.0)  # Less than $25k
            
            # Add only 2 day trades (under the limit)
            for i in range(2):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should allow trading
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertTrue(can_trade, "PDT should allow trading under the 3-trade limit")
            self.assertIn("PDT OK", msg, "Message should indicate PDT is OK")
            self.assertIn("2/3", msg, "Message should show 2/3 trades used")
    
    def test_pdt_allows_trading_with_high_capital_in_production(self):
        """Test that PDT allows trading with $25k+ capital in production"""
        # Simulate being in production mode
        with patch('main.PAPER_TRADING_MODE', False):
            bot = TradingBot(total_capital=30000.0)  # Over $25k - exempt from PDT
            
            # Add 3+ day trades
            for i in range(5):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should allow trading with high capital
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertTrue(can_trade, "PDT should allow unlimited trading with $25k+ capital")
            self.assertIn("PDT OK", msg, "Message should indicate PDT is OK")
    
    def test_unlimited_day_trades_in_paper_mode(self):
        """Test that paper mode allows unlimited day trades"""
        # Simulate being in paper trading mode
        with patch('main.PAPER_TRADING_MODE', True):
            bot = TradingBot(total_capital=500.0)  # Less than $25k
            
            # Add many day trades (way over the normal limit)
            for i in range(10):
                bot.add_day_trade(f"TEST{i}")
            
            # Check PDT compliance - should still allow trading
            can_trade, msg = bot.check_pdt_compliance()
            
            self.assertTrue(can_trade, "Paper mode should allow unlimited day trades")
            self.assertIn("disabled", msg.lower(), "Message should indicate PDT is disabled")
            # Should mention either sandbox or simulation mode
            self.assertTrue("sandbox" in msg.lower() or "simulation" in msg.lower(), 
                          "Message should mention sandbox or simulation mode")


if __name__ == '__main__':
    unittest.main()
