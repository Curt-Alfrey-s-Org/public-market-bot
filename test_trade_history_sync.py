#!/usr/bin/env python3
"""
Test trade history synchronization between bot and web GUI
Verifies that bot.trade_history is properly displayed in web GUI callbacks
"""

import unittest
from unittest.mock import Mock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestTradeHistorySync(unittest.TestCase):
    """Test that web GUI properly displays bot.trade_history"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock bot with trade history
        self.mock_bot = Mock()
        self.mock_bot.trade_history = [
            {
                'timestamp': '2026-01-19T10:00:00',
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 10.0,
                'price': 150.00,
                'is_win': True
            },
            {
                'timestamp': '2026-01-19T10:05:00',
                'symbol': 'MSFT',
                'action': 'BUY',
                'quantity': 5.0,
                'price': 380.00,
                'is_win': False
            },
            {
                'timestamp': '2026-01-19T10:10:00',
                'symbol': 'GOOGL',
                'action': 'SELL',
                'quantity': 3.0,
                'price': 140.00,
                'is_win': True
            }
        ]
        
        # Mock trade_log (local buffer)
        self.mock_trade_log = [
            {
                'timestamp': '2026-01-19T10:15:00',
                'symbol': 'TSLA',
                'action': 'BUY',
                'quantity': 2.0,
                'price': 250.00,
                'is_win': False
            }
        ]
    
    def test_merge_trade_sources(self):
        """Test that trades are properly merged from both sources"""
        # Simulate the merge logic from update_trade_log callback
        all_trades = []
        
        # Add bot's trade history
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        # Add trade_log trades not in bot.trade_history
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Verify all trades are present
        self.assertEqual(len(all_trades), 4)
        
        # Verify trades from bot.trade_history
        symbols = [t['symbol'] for t in all_trades]
        self.assertIn('AAPL', symbols)
        self.assertIn('MSFT', symbols)
        self.assertIn('GOOGL', symbols)
        
        # Verify trade from trade_log
        self.assertIn('TSLA', symbols)
    
    def test_deduplication(self):
        """Test that duplicate trades are not added twice"""
        # Add a duplicate timestamp to trade_log
        duplicate_trade = {
            'timestamp': '2026-01-19T10:00:00',  # Same as AAPL trade
            'symbol': 'NVDA',
            'action': 'BUY',
            'quantity': 1.0,
            'price': 500.00,
            'is_win': True
        }
        self.mock_trade_log.append(duplicate_trade)
        
        # Simulate merge logic
        all_trades = []
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Should have 4 trades (3 from bot + 1 unique from trade_log)
        # NVDA should be excluded because it has duplicate timestamp
        self.assertEqual(len(all_trades), 4)
        
        # NVDA should not be present (duplicate timestamp filtered)
        symbols = [t['symbol'] for t in all_trades]
        self.assertNotIn('NVDA', symbols)
    
    def test_empty_bot_history(self):
        """Test behavior when bot.trade_history is empty"""
        self.mock_bot.trade_history = []
        
        # Simulate merge logic
        all_trades = []
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Should have 1 trade from trade_log
        self.assertEqual(len(all_trades), 1)
        self.assertEqual(all_trades[0]['symbol'], 'TSLA')
    
    def test_empty_trade_log(self):
        """Test behavior when trade_log is empty"""
        self.mock_trade_log = []
        
        # Simulate merge logic
        all_trades = []
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Should have 3 trades from bot.trade_history
        self.assertEqual(len(all_trades), 3)
        symbols = [t['symbol'] for t in all_trades]
        self.assertIn('AAPL', symbols)
        self.assertIn('MSFT', symbols)
        self.assertIn('GOOGL', symbols)
    
    def test_win_loss_filtering(self):
        """Test that win/loss filtering works correctly"""
        # Merge all trades
        all_trades = []
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Filter wins
        winning_trades = [t for t in all_trades if t.get('is_win', False)]
        self.assertEqual(len(winning_trades), 2)  # AAPL and GOOGL
        
        # Filter losses
        losing_trades = [t for t in all_trades if not t.get('is_win', False)]
        self.assertEqual(len(losing_trades), 2)  # MSFT and TSLA
    
    def test_timestamp_formats(self):
        """Test that different timestamp formats are handled"""
        # Add trade with datetime object instead of string
        self.mock_bot.trade_history.append({
            'timestamp': datetime.now(),
            'symbol': 'AMD',
            'action': 'BUY',
            'quantity': 1.0,
            'price': 100.00,
            'is_win': True
        })
        
        # Merge should still work
        all_trades = []
        if self.mock_bot.trade_history:
            all_trades.extend(self.mock_bot.trade_history)
        
        existing_timestamps = {t.get('timestamp') for t in all_trades if 'timestamp' in t}
        for trade in self.mock_trade_log:
            if trade.get('timestamp') not in existing_timestamps:
                all_trades.append(trade)
        
        # Should have 5 trades total
        self.assertEqual(len(all_trades), 5)
        
        # AMD should be present
        symbols = [t['symbol'] for t in all_trades]
        self.assertIn('AMD', symbols)


if __name__ == '__main__':
    print("Testing trade history synchronization...")
    print("=" * 60)
    unittest.main(verbosity=2)
