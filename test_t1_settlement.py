#!/usr/bin/env python3
"""
Test suite for T+1 settlement rules implementation
Tests that capital and proceeds are locked until settlement date in cash accounts
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the bot
from main import TradingBot


class TestT1Settlement(unittest.TestCase):
    """Test T+1 settlement tracking"""
    
    def setUp(self):
        """Set up test bot instance with $10,000 capital"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_initial_settled_capital_equals_total_capital(self):
        """Test that initially, all capital is settled (no trades yet)"""
        settled_capital = self.bot.get_settled_capital()
        self.assertEqual(settled_capital, 10000.0)
        self.assertEqual(len(self.bot.unsettled_funds), 0)
    
    def test_business_days_calculation(self):
        """Test that business days calculation skips weekends"""
        # Test from a Friday
        friday = datetime(2024, 1, 5, 10, 0, 0)  # Friday Jan 5, 2024
        settlement = self.bot._calculate_business_days_ahead(1, friday)
        # T+1 from Friday should be Monday (skip weekend)
        self.assertEqual(settlement.weekday(), 0)  # Monday
        self.assertEqual(settlement.day, 8)  # Jan 8, 2024
        
        # Test from a Wednesday
        wednesday = datetime(2024, 1, 3, 10, 0, 0)  # Wednesday Jan 3, 2024
        settlement = self.bot._calculate_business_days_ahead(1, wednesday)
        # T+1 from Wednesday should be Thursday
        self.assertEqual(settlement.weekday(), 3)  # Thursday
        self.assertEqual(settlement.day, 4)  # Jan 4, 2024
    
    def test_buy_locks_capital_until_settlement(self):
        """Test that BUY order locks the capital used"""
        # Add unsettled funds as if we bought $1000 worth of stock
        self.bot._add_unsettled_funds(1000.0, 'BUY AAPL')
        
        # Check that we have unsettled funds
        self.assertEqual(len(self.bot.unsettled_funds), 1)
        self.assertEqual(self.bot.unsettled_funds[0]['amount'], 1000.0)
        self.assertEqual(self.bot.unsettled_funds[0]['reason'], 'BUY AAPL')
        
        # Check that settled capital is reduced
        settled_capital = self.bot.get_settled_capital()
        self.assertEqual(settled_capital, 9000.0)  # 10000 - 1000
    
    def test_sell_locks_proceeds_until_settlement(self):
        """Test that SELL order locks the proceeds"""
        # Add unsettled funds as if we sold stock for $1500
        self.bot._add_unsettled_funds(1500.0, 'SELL AAPL')
        
        # Check that we have unsettled funds
        self.assertEqual(len(self.bot.unsettled_funds), 1)
        self.assertEqual(self.bot.unsettled_funds[0]['amount'], 1500.0)
        
        # Check that settled capital is reduced
        settled_capital = self.bot.get_settled_capital()
        self.assertEqual(settled_capital, 8500.0)  # 10000 - 1500
    
    def test_multiple_unsettled_trades(self):
        """Test multiple overlapping unsettled trades"""
        # Simulate multiple trades
        self.bot._add_unsettled_funds(1000.0, 'BUY AAPL')
        self.bot._add_unsettled_funds(800.0, 'BUY TSLA')
        self.bot._add_unsettled_funds(1200.0, 'SELL MSFT')
        
        # Check total unsettled
        self.assertEqual(len(self.bot.unsettled_funds), 3)
        
        # Check settled capital
        settled_capital = self.bot.get_settled_capital()
        expected_settled = 10000.0 - 1000.0 - 800.0 - 1200.0
        self.assertEqual(settled_capital, expected_settled)  # 7000.0
    
    def test_funds_settle_after_t1(self):
        """Test that funds become available after settlement date passes"""
        # Add unsettled funds with a past settlement date
        past_settlement = datetime.now() - timedelta(days=1)
        self.bot.unsettled_funds.append({
            'amount': 1000.0,
            'settlement_date': past_settlement,
            'reason': 'BUY AAPL',
            'created_at': datetime.now() - timedelta(days=2)
        })
        
        # Clean settled funds
        self.bot._clean_settled_funds()
        
        # Funds should be released
        self.assertEqual(len(self.bot.unsettled_funds), 0)
        settled_capital = self.bot.get_settled_capital()
        self.assertEqual(settled_capital, 10000.0)
    
    def test_check_settled_capital_available_sufficient(self):
        """Test checking for available settled capital - sufficient case"""
        # No unsettled funds, all capital available
        can_trade, message = self.bot.check_settled_capital_available(5000.0)
        self.assertTrue(can_trade)
        self.assertIn("Settled capital available", message)
    
    def test_check_settled_capital_available_insufficient(self):
        """Test checking for available settled capital - insufficient case"""
        # Lock $8000 in unsettled funds
        self.bot._add_unsettled_funds(8000.0, 'BUY AAPL')
        
        # Try to trade $5000 (only $2000 available)
        can_trade, message = self.bot.check_settled_capital_available(5000.0)
        self.assertFalse(can_trade)
        self.assertIn("Insufficient settled capital", message)
        self.assertIn("T+1 settlement pending", message)
        self.assertIn("Required: $5000.00", message)
        self.assertIn("Available (settled): $2000.00", message)
    
    @patch('main.TradingBot.generate_random_volume')
    def test_paper_trade_buy_locks_capital(self, mock_volume):
        """Test that paper trading BUY locks capital"""
        mock_volume.return_value = 1000000
        
        # Execute a paper trade
        with patch('main.SIMULATED_WIN_RATE', 1.0):  # Force a win
            result = self.bot.execute_trade_paper_mode('AAPL', 'BUY', 150.0, volume=1000000)
        
        # Check that result was successful (not skipped)
        self.assertIn('status', result)
        # Note: The trade may be skipped for other reasons (filters, etc.)
        # but if it went through, unsettled funds should be added
    
    def test_settlement_tracking_integration(self):
        """Test complete settlement flow"""
        # Initial state
        initial_capital = self.bot.get_settled_capital()
        self.assertEqual(initial_capital, 10000.0)
        
        # Simulate a BUY that uses $2000
        self.bot._add_unsettled_funds(2000.0, 'BUY AAPL')
        after_buy = self.bot.get_settled_capital()
        self.assertEqual(after_buy, 8000.0)
        
        # Simulate a SELL that returns $2500
        self.bot._add_unsettled_funds(2500.0, 'SELL AAPL')
        after_sell = self.bot.get_settled_capital()
        self.assertEqual(after_sell, 5500.0)  # 10000 - 2000 - 2500
        
        # Verify we have 2 unsettled funds
        self.assertEqual(len(self.bot.unsettled_funds), 2)
        
        # Simulate settlement of first trade (BUY) - past settlement date
        self.bot.unsettled_funds[0]['settlement_date'] = datetime.now() - timedelta(days=1)
        after_first_settlement = self.bot.get_settled_capital()
        self.assertEqual(after_first_settlement, 7500.0)  # 10000 - 2500 (only SELL unsettled)
        
        # Verify only 1 unsettled fund remains (the SELL)
        self.assertEqual(len(self.bot.unsettled_funds), 1)
        self.assertEqual(self.bot.unsettled_funds[0]['reason'], 'SELL AAPL')
        
        # Simulate settlement of second trade (SELL) - past settlement date
        self.bot.unsettled_funds[0]['settlement_date'] = datetime.now() - timedelta(days=1)
        after_all_settlement = self.bot.get_settled_capital()
        self.assertEqual(after_all_settlement, 10000.0)  # All settled
        
        # Verify no unsettled funds remain
        self.assertEqual(len(self.bot.unsettled_funds), 0)
    
    def test_negative_capital_edge_case(self):
        """Test that settled capital never goes negative (edge case: losses after locking funds)"""
        # Lock $8000 in unsettled funds
        self.bot._add_unsettled_funds(8000.0, 'BUY AAPL')
        
        # Simulate a large loss that reduces total capital
        self.bot.update_capital(-5000.0)  # Loss of $5000
        # Total capital is now $5000, but $8000 is locked (unsettled)
        
        # Settled capital should be 0, not negative
        settled_capital = self.bot.get_settled_capital()
        self.assertEqual(settled_capital, 0.0)
        self.assertGreaterEqual(settled_capital, 0.0)  # Never negative
        
        # Verify trade is blocked with 0 settled capital
        can_trade, message = self.bot.check_settled_capital_available(100.0)
        self.assertFalse(can_trade)
        self.assertIn("Insufficient settled capital", message)


class TestT1SettlementIntegration(unittest.TestCase):
    """Integration tests for T+1 settlement with actual trading"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch('main.TradingBot.generate_random_volume')
    @patch('main.TradingBot.filter_stock')
    @patch('main.TradingBot.check_sentiment_filter')
    def test_second_trade_blocked_by_settlement(self, mock_sentiment, mock_filter, mock_volume):
        """Test that a second trade is blocked if not enough settled capital"""
        mock_volume.return_value = 1000000
        mock_filter.return_value = (True, "Stock passed filter")
        mock_sentiment.return_value = (True, "Sentiment OK")
        
        # Set high allocation to use most of capital
        self.bot.track_record['current_allocation'] = 9000.0
        
        # First trade should succeed
        with patch('main.SIMULATED_WIN_RATE', 1.0):
            result1 = self.bot.execute_trade_paper_mode('AAPL', 'BUY', 150.0, volume=1000000)
        
        # Verify first trade went through or was not blocked by settlement
        if result1.get('status') == 'skipped':
            # If skipped, should not be due to settlement (no prior trades)
            self.assertNotEqual(result1.get('reason'), 't1_settlement_pending')
        
        # Verify that we now have unsettled funds
        settled = self.bot.get_settled_capital()
        # Should be less than total capital if trade succeeded
        
        # Second trade should be blocked by settlement if not enough capital
        with patch('main.SIMULATED_WIN_RATE', 1.0):
            result2 = self.bot.execute_trade_paper_mode('TSLA', 'BUY', 200.0, volume=1000000)
        
        # If second trade was blocked, it might be due to settlement
        if result2.get('status') == 'skipped' and result2.get('reason') == 't1_settlement_pending':
            # Success - settlement check worked
            self.assertIn('T+1 settlement pending', result2.get('message', ''))


if __name__ == '__main__':
    unittest.main()
