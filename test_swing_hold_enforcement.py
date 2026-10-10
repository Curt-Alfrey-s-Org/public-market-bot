"""
Test swing trading hold period enforcement logic.
Validates that minimum holding periods are enforced across all trading modes.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the trading bot
from main import TradingBot


class TestSwingHoldEnforcement(unittest.TestCase):
    """Test minimum holding period enforcement for swing trading strategy"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        # Set test environment variables
        os.environ['ENABLE_PDT_RULES'] = 'false'
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SWING_MIN_HOLD_DAYS'] = '1'  # Enforce 1 day minimum hold
    
    def test_check_holding_period_allows_buy(self):
        """Test that holding period check allows BUY actions"""
        bot = TradingBot(total_capital=10000.0)
        
        # BUY actions should always be allowed
        can_trade, msg = bot.check_holding_period('AAPL', 'BUY')
        
        self.assertTrue(can_trade, "BUY action should be allowed")
        self.assertIn("BUY action", msg, "Message should indicate BUY is not checked")
    
    def test_check_holding_period_allows_sell_with_no_position(self):
        """Test that holding period check allows SELL when no position exists"""
        bot = TradingBot(total_capital=10000.0)
        
        # SELL without position should be allowed (backward compatibility)
        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
        
        self.assertTrue(can_trade, "SELL should be allowed when no position exists")
        self.assertIn("No open position", msg, "Message should indicate no position")
    
    def test_check_holding_period_blocks_same_day_sell(self):
        """Test that holding period check blocks SELL on same day as BUY"""
        bot = TradingBot(total_capital=10000.0)
        
        # Open a position
        bot.open_position('AAPL', 150.0, 10.0)
        
        # Try to sell immediately (same day)
        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
        
        self.assertFalse(can_trade, "SELL should be blocked on same day as BUY")
        self.assertIn("Holding period not met", msg, "Message should indicate holding period not met")
        self.assertIn("24.0h required", msg, "Message should show 24h requirement")
    
    def test_check_holding_period_allows_sell_after_min_hold(self):
        """Test that holding period check allows SELL after minimum hold period"""
        bot = TradingBot(total_capital=10000.0)
        
        # Open a position with entry time 25 hours ago
        past_time = (datetime.now() - timedelta(hours=25)).isoformat()
        bot.positions['AAPL'] = {
            'entry_price': 150.0,
            'quantity': 10.0,
            'high_price': 150.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': past_time
        }
        
        # Try to sell (should be allowed after 25 hours)
        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
        
        self.assertTrue(can_trade, "SELL should be allowed after minimum hold period")
        self.assertIn("Holding period met", msg, "Message should indicate holding period met")
    
    def test_check_holding_period_with_zero_days_setting(self):
        """Test that setting SWING_MIN_HOLD_DAYS=0 allows same-day sells"""
        # Set environment variable to 0 days
        with patch('main.SWING_MIN_HOLD_DAYS', 0):
            bot = TradingBot(total_capital=10000.0)
            
            # Open a position
            bot.open_position('AAPL', 150.0, 10.0)
            
            # Try to sell immediately (should be allowed with 0 days setting)
            can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
            
            self.assertTrue(can_trade, "SELL should be allowed with SWING_MIN_HOLD_DAYS=0")
    
    def test_check_holding_period_with_multi_day_setting(self):
        """Test that holding period check works with multi-day requirements"""
        # Set environment variable to 2 days
        with patch('main.SWING_MIN_HOLD_DAYS', 2):
            bot = TradingBot(total_capital=10000.0)
            
            # Open a position with entry time 25 hours ago (just over 1 day)
            past_time = (datetime.now() - timedelta(hours=25)).isoformat()
            bot.positions['AAPL'] = {
                'entry_price': 150.0,
                'quantity': 10.0,
                'high_price': 150.0,
                'stop_percent': 0.03,
                'partial_exit_done': False,
                'entry_time': past_time
            }
            
            # Try to sell (should be blocked - need 2 days)
            can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
            
            self.assertFalse(can_trade, "SELL should be blocked with 2-day requirement")
            self.assertIn("48.0h required", msg, "Message should show 48h requirement")
    
    def test_check_holding_period_with_missing_entry_time(self):
        """Test that holding period check allows SELL when entry_time is missing"""
        bot = TradingBot(total_capital=10000.0)
        
        # Open a position without entry_time (backward compatibility)
        bot.positions['AAPL'] = {
            'entry_price': 150.0,
            'quantity': 10.0,
            'high_price': 150.0,
            'stop_percent': 0.03,
            'partial_exit_done': False
        }
        
        # Try to sell (should be allowed for backward compatibility)
        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
        
        self.assertTrue(can_trade, "SELL should be allowed when entry_time is missing")
        self.assertIn("No entry time recorded", msg, "Message should indicate missing entry time")
    
    def test_execute_trade_paper_mode_enforces_holding_period(self):
        """Test that execute_trade_paper_mode enforces holding period for SELLs"""
        bot = TradingBot(total_capital=10000.0)
        
        # Open a position
        bot.open_position('AAPL', 150.0, 10.0)
        
        # Try to execute a SELL immediately (should be blocked)
        result = bot.execute_trade_paper_mode('AAPL', 'SELL', 155.0, volume=1000000)
        
        self.assertEqual(result['status'], 'skipped', "Trade should be skipped")
        self.assertEqual(result['reason'], 'holding_period_not_met', "Reason should be holding period not met")
        self.assertIn("Holding period not met", result['message'], "Message should explain holding period")
    
    def test_execute_trade_live_mode_enforces_holding_period(self):
        """Test that execute_trade_live_mode enforces holding period for SELLs"""
        # Mock Schwab API environment
        with patch('main.PAPER_TRADING_MODE', False):
            with patch('main.SCHWAB_API_KEY', 'test_key'):
                with patch('main.SCHWAB_APP_SECRET', 'test_secret'):
                    with patch('main.SCHWAB_ACCOUNT_ID', 'test_account'):
                        bot = TradingBot(total_capital=30000.0)  # Over $25k to avoid PDT
                        
                        # Mock the credentials validation
                        bot._validate_live_mode_credentials = MagicMock(return_value=True)
                        
                        # Open a position
                        bot.open_position('AAPL', 150.0, 10.0)
                        
                        # Try to execute a SELL immediately (should be blocked)
                        result = bot.execute_trade_live_mode('AAPL', 'SELL', 155.0)
                        
                        self.assertEqual(result['status'], 'skipped', "Trade should be skipped")
                        self.assertEqual(result['reason'], 'holding_period_not_met', "Reason should be holding period not met")
                        self.assertIn("Holding period not met", result['message'], "Message should explain holding period")
    
    def test_holding_period_enforcement_in_all_modes(self):
        """Test that holding period is enforced in sandbox, simulation, and live modes"""
        test_cases = [
            {'PAPER_TRADING_MODE': True, 'SCHWAB_SANDBOX_MODE': True, 'mode': 'sandbox'},
            {'PAPER_TRADING_MODE': True, 'SCHWAB_SANDBOX_MODE': False, 'mode': 'simulation'},
            {'PAPER_TRADING_MODE': False, 'SCHWAB_SANDBOX_MODE': False, 'mode': 'live'},
        ]
        
        for test_case in test_cases:
            with self.subTest(mode=test_case['mode']):
                with patch('main.PAPER_TRADING_MODE', test_case['PAPER_TRADING_MODE']):
                    with patch('main.SCHWAB_SANDBOX_MODE', test_case['SCHWAB_SANDBOX_MODE']):
                        bot = TradingBot(total_capital=30000.0)
                        
                        # Open a position
                        bot.open_position('AAPL', 150.0, 10.0)
                        
                        # Check holding period (should be blocked)
                        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
                        
                        self.assertFalse(can_trade, f"SELL should be blocked in {test_case['mode']} mode")
                        self.assertIn("Holding period not met", msg, 
                                    f"Message should indicate holding period not met in {test_case['mode']} mode")
    
    def test_holding_period_calculates_correct_duration(self):
        """Test that holding period correctly calculates time held"""
        bot = TradingBot(total_capital=10000.0)
        
        # Open a position with entry time 12 hours ago
        hours_held = 12
        past_time = (datetime.now() - timedelta(hours=hours_held)).isoformat()
        bot.positions['AAPL'] = {
            'entry_price': 150.0,
            'quantity': 10.0,
            'high_price': 150.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': past_time
        }
        
        # Try to sell (should be blocked)
        can_trade, msg = bot.check_holding_period('AAPL', 'SELL')
        
        self.assertFalse(can_trade, "SELL should be blocked with only 12 hours held")
        # Check that the message contains approximately 12 hours
        self.assertIn("12.", msg, "Message should show approximately 12 hours held")
        self.assertIn("24.0h required", msg, "Message should show 24h requirement")


if __name__ == '__main__':
    unittest.main()
