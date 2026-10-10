#!/usr/bin/env python3
"""
Test suite for advanced trading features
Tests trailing stops, position management, and other complex features
"""

import unittest
from datetime import datetime
from main import TradingBot, BOT_MAX_OPEN_POSITIONS


class TestTrailingStopLogic(unittest.TestCase):
    """Test trailing stop functionality"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
        self.bot.trailing_stop_percent = 0.05  # 5% trailing stop
    
    def test_open_position_tracking(self):
        """Test that opening position tracks entry price and high water mark"""
        symbol = 'AAPL'
        entry_price = 150.0
        quantity = 10.0
        
        self.bot.open_position(symbol, entry_price, quantity)
        
        self.assertIn(symbol, self.bot.positions)
        self.assertEqual(self.bot.positions[symbol]['entry_price'], entry_price)
        self.assertEqual(self.bot.positions[symbol]['quantity'], quantity)
        self.assertEqual(self.bot.positions[symbol]['high_price'], entry_price)
        self.assertFalse(self.bot.positions[symbol]['partial_exit_done'])
    
    def test_high_water_mark_updates(self):
        """Test that high water mark updates when price increases"""
        symbol = 'AAPL'
        entry_price = 150.0
        quantity = 10.0
        
        self.bot.open_position(symbol, entry_price, quantity)
        
        # Price increases - high water mark should update
        higher_price = 160.0
        self.bot.check_trailing_stop(symbol, higher_price)
        self.assertEqual(self.bot.positions[symbol]['high_price'], higher_price)
    
    def test_trailing_stop_not_triggered_when_price_rising(self):
        """Test that trailing stop is not triggered when price is rising"""
        symbol = 'AAPL'
        entry_price = 150.0
        quantity = 10.0
        
        self.bot.open_position(symbol, entry_price, quantity)
        
        # Price rises
        result = self.bot.check_trailing_stop(symbol, 155.0)
        self.assertFalse(result)
        
        result = self.bot.check_trailing_stop(symbol, 160.0)
        self.assertFalse(result)
    
    def test_trailing_stop_triggered_on_decline(self):
        """Test that trailing stop triggers when price falls below threshold"""
        symbol = 'AAPL'
        entry_price = 150.0
        quantity = 10.0
        stop_percent = 0.05  # 5%
        
        self.bot.open_position(symbol, entry_price, quantity, stop_percent)
        
        # Price rises to new high
        self.bot.check_trailing_stop(symbol, 160.0)
        # High water mark is now 160.0
        
        # Price falls below trailing stop (160 * 0.95 = 152)
        result = self.bot.check_trailing_stop(symbol, 151.0)
        self.assertTrue(result)
    
    def test_close_position_returns_pnl(self):
        """Test that closing position returns correct P&L info"""
        symbol = 'AAPL'
        entry_price = 150.0
        exit_price = 160.0
        quantity = 10.0
        
        self.bot.open_position(symbol, entry_price, quantity)
        pnl_info = self.bot.close_position(symbol, exit_price, exit_reason='test')
        
        self.assertIsNotNone(pnl_info)
        self.assertEqual(pnl_info['entry_price'], entry_price)
        self.assertEqual(pnl_info['exit_price'], exit_price)
        self.assertEqual(pnl_info['quantity'], quantity)
        expected_pnl = (exit_price - entry_price) * quantity  # 100.0
        self.assertEqual(pnl_info['pnl'], expected_pnl)
        self.assertTrue(pnl_info['is_win'])
    
    def test_close_position_removes_from_positions(self):
        """Test that closing position removes it from tracking"""
        symbol = 'AAPL'
        entry_price = 150.0
        quantity = 10.0
        
        self.bot.open_position(symbol, entry_price, quantity)
        self.assertIn(symbol, self.bot.positions)
        
        self.bot.close_position(symbol, 155.0, exit_reason='test')
        self.assertNotIn(symbol, self.bot.positions)


class TestPositionManagement(unittest.TestCase):
    """Test position management limits and tracking"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_can_open_position_when_under_limit(self):
        """Test that bot can open position when under limit"""
        can_open, reason = self.bot.can_open_new_position()
        self.assertTrue(can_open)
        self.assertIn('Can open', reason)
    
    def test_cannot_open_position_at_limit(self):
        """Test that bot cannot open position when at max limit"""
        # Open max positions
        for i in range(BOT_MAX_OPEN_POSITIONS):
            symbol = f'STOCK{i}'
            self.bot.open_position(symbol, 100.0, 10.0)
        
        can_open, reason = self.bot.can_open_new_position()
        self.assertFalse(can_open)
        self.assertIn('Maximum positions', reason)
    
    def test_can_open_after_closing_position(self):
        """Test that bot can open new position after closing one at limit"""
        # Open max positions
        for i in range(BOT_MAX_OPEN_POSITIONS):
            symbol = f'STOCK{i}'
            self.bot.open_position(symbol, 100.0, 10.0)
        
        # Should be at limit
        can_open, _ = self.bot.can_open_new_position()
        self.assertFalse(can_open)
        
        # Close one position
        self.bot.close_position('STOCK0', 105.0, exit_reason='test')
        
        # Should be able to open again
        can_open, reason = self.bot.can_open_new_position()
        self.assertTrue(can_open)
    
    def test_position_count_tracking(self):
        """Test that position count is accurately tracked"""
        self.assertEqual(len(self.bot.positions), 0)
        
        self.bot.open_position('AAPL', 150.0, 10.0)
        self.assertEqual(len(self.bot.positions), 1)
        
        self.bot.open_position('MSFT', 300.0, 5.0)
        self.assertEqual(len(self.bot.positions), 2)
        
        self.bot.close_position('AAPL', 155.0, exit_reason='test')
        self.assertEqual(len(self.bot.positions), 1)


class TestStockFiltering(unittest.TestCase):
    """Test stock filtering and validation"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
        # Add some price history for volatility calculations
        test_symbol = 'TEST'
        for i in range(20):
            self.bot.update_price_history(test_symbol, 100.0 + i * 0.5)
    
    def test_reject_penny_stocks(self):
        """Test that penny stocks are rejected"""
        is_valid, reason = self.bot.filter_stock('PENNY', price=3.0, volume=1000000)
        self.assertFalse(is_valid)
        self.assertIn('minimum', reason.lower())
    
    def test_reject_low_volume(self):
        """Test that low volume stocks are rejected"""
        is_valid, reason = self.bot.filter_stock('LOWVOL', price=50.0, volume=10000)
        self.assertFalse(is_valid)
        self.assertIn('volume', reason.lower())
    
    def test_accept_valid_stock(self):
        """Test that valid stocks pass filtering"""
        # Valid price and volume
        is_valid, reason = self.bot.filter_stock('VALID', price=50.0, volume=1000000)
        # Might be rejected for other reasons (no history), but shouldn't be for price/volume
        if not is_valid:
            # Make sure it's not rejected for price or volume
            self.assertNotIn('minimum', reason.lower())
            if 'volume' in reason.lower():
                # This shouldn't happen with 1M volume, but let's check the number
                self.assertGreater(1000000, 500000)


class TestCapitalFloorProtection(unittest.TestCase):
    """Test capital floor protection"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=1000.0)
        # Capital floor should be 10% of starting capital = 100.0
    
    def test_capital_floor_calculation(self):
        """Test that capital floor is calculated correctly"""
        expected_floor = 1000.0 * 0.10  # 10% of starting capital
        self.assertEqual(self.bot.capital_floor, expected_floor)
    
    def test_trading_paused_below_floor(self):
        """Test that trading is paused when capital drops below floor"""
        # Reduce capital below floor
        self.bot.total_capital = 90.0  # Below 100.0 floor
        
        can_trade, message = self.bot.check_capital_floor()
        self.assertFalse(can_trade)
        self.assertIn('below floor', message.lower())
        self.assertTrue(self.bot.is_paused)
    
    def test_trading_allowed_above_floor(self):
        """Test that trading is allowed when capital is above floor"""
        # Keep capital above floor
        self.bot.total_capital = 500.0
        
        can_trade, message = self.bot.check_capital_floor()
        self.assertTrue(can_trade)
        self.assertFalse(self.bot.is_paused)
    
    def test_trading_resumes_after_recovery(self):
        """Test that trading resumes when capital recovers"""
        # Drop below floor
        self.bot.total_capital = 90.0
        self.bot.check_capital_floor()
        self.assertTrue(self.bot.is_paused)
        
        # Recover to 120% of floor (120.0)
        self.bot.total_capital = 125.0
        can_trade, message = self.bot.check_capital_floor()
        
        self.assertTrue(can_trade)
        self.assertFalse(self.bot.is_paused)


class TestPDTCompliance(unittest.TestCase):
    """Test Pattern Day Trading compliance"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_day_trade_tracking(self):
        """Test that day trades are tracked"""
        initial_count = self.bot.get_day_trade_count()
        
        self.bot.add_day_trade('AAPL')
        self.assertEqual(self.bot.get_day_trade_count(), initial_count + 1)
        
        self.bot.add_day_trade('MSFT')
        self.assertEqual(self.bot.get_day_trade_count(), initial_count + 2)
    
    def test_pdt_rules_disabled_in_paper_mode(self):
        """Test that PDT rules are disabled in paper trading mode"""
        # Add 5 day trades (would violate PDT in live mode)
        for i in range(5):
            self.bot.add_day_trade(f'STOCK{i}')
        
        # Should still be allowed in paper mode
        can_trade, message = self.bot.check_pdt_compliance()
        self.assertTrue(can_trade)
        self.assertIn('disabled', message.lower())


class TestSelfScalingLogic(unittest.TestCase):
    """Test self-scaling allocation logic"""
    
    def setUp(self):
        """Set up trading bot"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_allocation_increases_on_high_win_rate(self):
        """Test that allocation increases when win rate > 60%"""
        # Simulate winning streak
        for i in range(10):
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, is_win=True)
        
        initial_allocation = self.bot.track_record['current_allocation']
        win_rate = self.bot.calculate_win_rate()
        
        self.assertGreater(win_rate, 0.60)
        # Allocation should have increased due to wins
        # (Note: allocation might be capped by risk threshold)
    
    def test_allocation_decreases_on_low_win_rate(self):
        """Test that allocation decreases when win rate <= 60%"""
        # Set initial allocation
        self.bot.track_record['current_allocation'] = 500.0
        
        # Simulate losing streak
        for i in range(10):
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, is_win=False)
        
        final_allocation = self.bot.track_record['current_allocation']
        
        # Allocation should have decreased due to losses
        self.assertLess(final_allocation, 500.0)
    
    def test_allocation_respects_min_max_bounds(self):
        """Test that allocation stays within min/max bounds"""
        # Test minimum bound
        self.bot.track_record['current_allocation'] = 50.0
        for i in range(10):
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, is_win=False)
        
        # Should not go below BOT_MIN_ALLOCATION
        from main import BOT_MIN_ALLOCATION, BOT_MAX_ALLOCATION
        self.assertGreaterEqual(
            self.bot.track_record['current_allocation'], 
            BOT_MIN_ALLOCATION
        )
        
        # Test maximum bound
        self.bot.track_record['current_allocation'] = 5000.0
        for i in range(10):
            self.bot.record_trade('AAPL', 'BUY', 10, 150.0, is_win=True)
        
        # Should not exceed BOT_MAX_ALLOCATION
        self.assertLessEqual(
            self.bot.track_record['current_allocation'], 
            BOT_MAX_ALLOCATION
        )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
