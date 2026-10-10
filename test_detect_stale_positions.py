#!/usr/bin/env python3
"""Test stale position detection feature (Phase 1 enhancement)"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Set test environment variables before importing main
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'

sys.path.insert(0, '.')
from main import TradingBot


class TestDetectStalePositions(unittest.TestCase):
    """Test stale position detection feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
        self.bot.is_simulation = True
        self.bot.using_yfinance_sim = True
        # Clear any positions loaded from database during init
        self.bot.positions = {}
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear positions for test isolation
        self.bot.positions = {}
    
    def test_detect_stale_positions_empty(self):
        """Test detect_stale_positions with no open positions"""
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        
        self.assertIsInstance(stale, dict)
        self.assertEqual(len(stale), 0, "Should return empty dict when no open positions")
    
    def test_detect_stale_positions_fresh_position(self):
        """Test that recently opened positions are not flagged as stale"""
        # Open a position with entry time 1 hour ago
        now = datetime.now()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        
        self.bot.positions['AAPL'] = {
            'entry_price': 150.0,
            'quantity': 10.0,
            'high_price': 150.0,
            'low_price': 149.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': one_hour_ago,
            'side': 'long'
        }
        
        # Check stale with 48h threshold
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        
        self.assertEqual(len(stale), 0, "1-hour old position should not be flagged as stale (48h threshold)")
    
    def test_detect_stale_positions_stale_long_position(self):
        """Test detection of a stale long position (held >48 hours)"""
        # Open a position 60 hours ago
        now = datetime.now()
        sixty_hours_ago = (now - timedelta(hours=60)).isoformat()
        
        entry_price = 150.0
        current_high_price = 153.0  # 2% gain
        
        self.bot.positions['MSFT'] = {
            'entry_price': entry_price,
            'quantity': 5.0,
            'high_price': current_high_price,
            'low_price': 148.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': sixty_hours_ago,
            'side': 'long'
        }
        
        # Detect stale with 48h threshold
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        
        self.assertIn('MSFT', stale, "60-hour old position should be flagged as stale")
        
        msft_stale = stale['MSFT']
        self.assertGreater(msft_stale['hold_duration_hours'], 58, "Hold duration should be ~60 hours")
        self.assertLess(msft_stale['hold_duration_hours'], 62, "Hold duration should be ~60 hours")
        self.assertEqual(msft_stale['entry_price'], entry_price, "Entry price should match")
        self.assertEqual(msft_stale['quantity'], 5.0, "Quantity should match")
        self.assertEqual(msft_stale['side'], 'long', "Side should be 'long'")
        
        # Check P&L calculation
        expected_pnl_pct = ((current_high_price - entry_price) / entry_price) * 100
        self.assertAlmostEqual(msft_stale['current_pnl_percent'], expected_pnl_pct, places=1)
    
    def test_detect_stale_positions_stale_short_position(self):
        """Test detection of a stale short position (held >48 hours)"""
        # Open a short 72 hours ago
        now = datetime.now()
        seventy_two_hours_ago = (now - timedelta(hours=72)).isoformat()
        
        entry_price = 100.0
        current_price = 98.0  # Shorted at 100, now at 98 = 2% gain for short
        
        self.bot.positions['TSLA'] = {
            'entry_price': entry_price,
            'quantity': 8.0,
            'high_price': current_price,  # Use high_price (that's what detect_stale_positions uses)
            'low_price': current_price,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': seventy_two_hours_ago,
            'side': 'short'
        }
        
        # Detect stale
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        
        self.assertIn('TSLA', stale, "Short position >48h should be flagged as stale")
        
        tsla_stale = stale['TSLA']
        self.assertGreater(tsla_stale['hold_duration_hours'], 70)
        self.assertEqual(tsla_stale['side'], 'short')
        
        # For short: P&L = (entry_price - current_price) / entry_price * 100
        expected_pnl_pct = ((entry_price - current_price) / entry_price) * 100
        self.assertAlmostEqual(tsla_stale['current_pnl_percent'], expected_pnl_pct, places=1)
    
    def test_detect_stale_positions_custom_threshold(self):
        """Test custom threshold for stale detection"""
        # Open a position 30 hours ago
        now = datetime.now()
        thirty_hours_ago = (now - timedelta(hours=30)).isoformat()
        
        self.bot.positions['NVDA'] = {
            'entry_price': 500.0,
            'quantity': 2.0,
            'high_price': 510.0,
            'low_price': 495.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': thirty_hours_ago,
            'side': 'long'
        }
        
        # Should NOT be stale with 48h threshold
        stale_48 = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        self.assertNotIn('NVDA', stale_48)
        
        # SHOULD be stale with 24h threshold
        stale_24 = self.bot.detect_stale_positions(stale_threshold_hours=24.0)
        self.assertIn('NVDA', stale_24)
    
    def test_detect_stale_positions_missing_entry_time(self):
        """Test that positions without entry_time are skipped gracefully"""
        # Position without entry_time (legacy positions)
        self.bot.positions['GOOGL'] = {
            'entry_price': 140.0,
            'quantity': 3.0,
            'high_price': 142.0,
            'low_price': 138.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            # No 'entry_time' field
            'side': 'long'
        }
        
        # Should return empty (position without entry_time is skipped)
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        self.assertNotIn('GOOGL', stale, "Position without entry_time should be skipped")
    
    def test_detect_stale_positions_multiple_positions(self):
        """Test detection with multiple open positions at different ages"""
        now = datetime.now()
        
        # Position 1: Fresh (5 hours)
        self.bot.positions['AAPL'] = {
            'entry_price': 150.0,
            'quantity': 10.0,
            'high_price': 151.0,
            'low_price': 149.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': (now - timedelta(hours=5)).isoformat(),
            'side': 'long'
        }
        
        # Position 2: Stale (55 hours)
        self.bot.positions['MSFT'] = {
            'entry_price': 425.0,
            'quantity': 5.0,
            'high_price': 430.0,
            'low_price': 420.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': (now - timedelta(hours=55)).isoformat(),
            'side': 'long'
        }
        
        # Position 3: Very stale (100 hours)
        self.bot.positions['GOOGL'] = {
            'entry_price': 140.0,
            'quantity': 3.0,
            'high_price': 145.0,
            'low_price': 135.0,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': (now - timedelta(hours=100)).isoformat(),
            'side': 'long'
        }
        
        # Detect stale
        stale = self.bot.detect_stale_positions(stale_threshold_hours=48.0)
        
        # Only MSFT and GOOGL should be flagged
        self.assertNotIn('AAPL', stale, "5-hour position should not be stale")
        self.assertIn('MSFT', stale, "55-hour position should be stale")
        self.assertIn('GOOGL', stale, "100-hour position should be stale")
        
        # Verify counts
        self.assertEqual(len(stale), 2, "Should detect 2 stale positions")


class TestTradeRecordingWithDuration(unittest.TestCase):
    """Test trade recording with entry_time and exit_time fields"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
        self.bot.is_simulation = True
        self.bot.using_yfinance_sim = True
    
    def test_record_buy_sets_entry_time(self):
        """Test that BUY trade records entry_time"""
        entry_time_str = datetime.now().isoformat()
        
        self.bot.record_trade(
            symbol='AAPL',
            action='BUY',
            quantity=10.0,
            price=150.0,
            is_win=False,
            entry_time=entry_time_str
        )
        
        trade = self.bot.trade_history[-1]
        self.assertEqual(trade['action'], 'BUY')
        self.assertIn('entry_time', trade)
        self.assertEqual(trade['entry_time'], entry_time_str)
        self.assertNotIn('exit_time', trade, "BUY trade should not have exit_time")
    
    def test_record_short_sets_entry_time(self):
        """Test that SHORT trade records entry_time"""
        entry_time_str = datetime.now().isoformat()
        
        self.bot.record_trade(
            symbol='TSLA',
            action='SHORT',
            quantity=5.0,
            price=250.0,
            is_win=False,
            entry_time=entry_time_str
        )
        
        trade = self.bot.trade_history[-1]
        self.assertEqual(trade['action'], 'SHORT')
        self.assertIn('entry_time', trade)
        self.assertEqual(trade['entry_time'], entry_time_str)
        self.assertNotIn('exit_time', trade, "SHORT trade should not have exit_time")
    
    def test_record_sell_sets_exit_time(self):
        """Test that SELL trade records exit_time (not entry_time)"""
        exit_time_str = datetime.now().isoformat()
        
        self.bot.record_trade(
            symbol='AAPL',
            action='SELL',
            quantity=10.0,
            price=155.0,
            is_win=True,
            entry_price=150.0,
            exit_price=155.0,
            pnl=50.0,
            pnl_percent=3.33,
            hold_duration=2.5,
            exit_time=exit_time_str
        )
        
        trade = self.bot.trade_history[-1]
        self.assertEqual(trade['action'], 'SELL')
        self.assertIn('exit_time', trade)
        self.assertEqual(trade['exit_time'], exit_time_str)
        # For SELL, entry_price is added if provided as parameter
        self.assertIn('entry_price', trade)
        self.assertEqual(trade['entry_price'], 150.0)
        # But entry_time is NOT set for SELL (only for BUY/SHORT)
        self.assertNotIn('entry_time', trade)
    
    def test_record_cover_sets_exit_time(self):
        """Test that COVER trade records exit_time (not entry_time)"""
        exit_time_str = datetime.now().isoformat()
        
        self.bot.record_trade(
            symbol='TSLA',
            action='COVER',
            quantity=5.0,
            price=245.0,
            is_win=True,
            entry_price=250.0,
            exit_price=245.0,
            pnl=25.0,
            pnl_percent=2.0,
            hold_duration=1.5,
            exit_time=exit_time_str
        )
        
        trade = self.bot.trade_history[-1]
        self.assertEqual(trade['action'], 'COVER')
        self.assertIn('exit_time', trade)
        self.assertEqual(trade['exit_time'], exit_time_str)
    
    def test_hold_duration_hours_field(self):
        """Test that hold_duration parameter creates hold_duration_hours field"""
        self.bot.record_trade(
            symbol='MSFT',
            action='SELL',
            quantity=5.0,
            price=430.0,
            is_win=True,
            entry_price=425.0,
            pnl=25.0,
            pnl_percent=1.18,
            hold_duration=48.5  # 48.5 hours
        )
        
        trade = self.bot.trade_history[-1]
        self.assertIn('hold_duration_hours', trade)
        self.assertEqual(trade['hold_duration_hours'], 48.5)


if __name__ == '__main__':
    unittest.main()
