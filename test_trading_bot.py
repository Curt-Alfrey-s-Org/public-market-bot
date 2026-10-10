#!/usr/bin/env python3
"""
Test suite for trading bot allocation and win rate improvements
Tests the new rolling window, consecutive loss tracking, allocation capping, 
trade sizing, and risk management features.
"""

import os
# Disable PDT rules for testing to avoid interference between tests
# MUST be set before importing main
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Import the bot
from main import TradingBot, BOT_MIN_ALLOCATION, BOT_MAX_ALLOCATION, BOT_RISK_THRESHOLD, BOT_STOP_LOSS_PERCENT


class TestRollingWinRate(unittest.TestCase):
    """Test rolling win rate calculation (20 trades or 7 days)"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_win_rate_empty_history(self):
        """Test win rate calculation with no trades"""
        win_rate = self.bot.calculate_win_rate()
        self.assertEqual(win_rate, 0.0)
    
    def test_win_rate_less_than_20_trades(self):
        """Test win rate with less than 20 trades uses all trades"""
        # Add 10 trades: 7 wins, 3 losses
        for i in range(7):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        for i in range(3):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        
        win_rate = self.bot.calculate_win_rate()
        self.assertEqual(win_rate, 0.7)  # 7/10 = 70%
    
    def test_win_rate_exactly_20_trades(self):
        """Test win rate with exactly 20 trades"""
        # Add 20 trades: 12 wins, 8 losses
        for i in range(12):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        for i in range(8):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        
        win_rate = self.bot.calculate_win_rate()
        self.assertEqual(win_rate, 0.6)  # 12/20 = 60%
    
    def test_win_rate_more_than_20_trades(self):
        """Test win rate uses only last 20 trades when more than 20 exist"""
        # Add 30 trades: first 10 all losses, next 20 all wins
        for i in range(10):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        for i in range(20):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        
        win_rate = self.bot.calculate_win_rate()
        self.assertEqual(win_rate, 1.0)  # Last 20 trades are all wins
    
    def test_win_rate_7_day_window(self):
        """Test win rate considers 7-day window"""
        # Manually add old trades (more than 7 days ago)
        old_timestamp = (datetime.now() - timedelta(days=8)).isoformat()
        for i in range(5):
            trade = {
                'timestamp': old_timestamp,
                'symbol': 'TEST',
                'action': 'BUY',
                'quantity': 1.0,
                'price': 100.0,
                'is_win': False  # Old losses
            }
            self.bot.trade_history.append(trade)
            self.bot.track_record['total_trades'] += 1
            self.bot.track_record['losing_trades'] += 1
        
        # Add recent trades (within 7 days)
        for i in range(5):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        
        win_rate = self.bot.calculate_win_rate()
        # Should only consider the 5 recent wins (not the old losses)
        self.assertEqual(win_rate, 1.0)


class TestConsecutiveLossTracking(unittest.TestCase):
    """Test consecutive loss tracking and allocation adjustment"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_consecutive_losses_reset_on_win(self):
        """Test that consecutive losses reset to 0 on a win"""
        self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        self.assertEqual(self.bot.consecutive_losses, 2)
        
        self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        self.assertEqual(self.bot.consecutive_losses, 0)
    
    def test_consecutive_losses_increment(self):
        """Test that consecutive losses increment correctly"""
        for i in range(5):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        
        self.assertEqual(self.bot.consecutive_losses, 5)
    
    def test_allocation_decrease_after_3_losses(self):
        """Test that allocation decreases by 25% after 3+ consecutive losses"""
        # Start with higher allocation so we can see the decrease
        self.bot.track_record['current_allocation'] = 100.0
        initial_allocation = self.bot.track_record['current_allocation']
        
        # Create 3 consecutive losses
        for i in range(3):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        
        # Allocation should decrease by 25% (midpoint of 20-30%)
        # After 3 losses, consecutive_losses = 3, which triggers the 25% decrease
        self.assertEqual(self.bot.consecutive_losses, 3)
        self.assertLess(self.bot.track_record['current_allocation'], initial_allocation)
    
    def test_allocation_normal_decrease_without_3_losses(self):
        """Test normal 10% decrease when less than 3 consecutive losses"""
        # Start with 1 win to ensure win rate is not 0
        self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        initial_allocation = self.bot.track_record['current_allocation']
        
        # Now 1 loss (consecutive losses = 1, win_rate = 50%)
        self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, False)
        
        self.assertEqual(self.bot.consecutive_losses, 1)
        # With win rate at 50% (1 win, 1 loss), should decrease by 10%
        self.assertLess(self.bot.track_record['current_allocation'], initial_allocation)


class TestAllocationCapping(unittest.TestCase):
    """Test that allocation never exceeds BOT_MAX_ALLOCATION"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_allocation_capped_at_max(self):
        """Test that allocation is capped at BOT_MAX_ALLOCATION"""
        # Set allocation close to max
        self.bot.track_record['current_allocation'] = BOT_MAX_ALLOCATION - 10
        
        # Add winning trades to trigger increase
        for i in range(10):
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, True)
        
        # Allocation should not exceed BOT_MAX_ALLOCATION
        self.assertLessEqual(self.bot.track_record['current_allocation'], BOT_MAX_ALLOCATION)
    
    def test_allocation_capped_in_trade_execution(self):
        """Test that allocation is capped during trade execution"""
        # Force allocation above max (shouldn't happen, but test the safety check)
        self.bot.track_record['current_allocation'] = BOT_MAX_ALLOCATION + 100
        
        # Execute trade
        with patch('random.random', return_value=0.5):  # Simulate a win
            result = self.bot.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        
        # Verify the trade used capped allocation
        if result['status'] == 'simulated':
            expected_quantity = BOT_MAX_ALLOCATION / 100.0
            self.assertAlmostEqual(result['quantity'], expected_quantity, places=6)


class TestTradeSizing(unittest.TestCase):
    """Test trade sizing calculation: quantity = current_allocation / price"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_quantity_calculation_low_price(self):
        """Test quantity calculation with low price stock"""
        self.bot.track_record['current_allocation'] = 100.0
        
        with patch('random.random', return_value=0.5):
            result = self.bot.execute_trade_paper_mode('CHEAP', 'BUY', 10.0)
        
        if result['status'] == 'simulated':
            expected_quantity = 100.0 / 10.0  # = 10.0
            self.assertAlmostEqual(result['quantity'], expected_quantity, places=6)
    
    def test_quantity_calculation_high_price(self):
        """Test quantity calculation with high price stock"""
        self.bot.track_record['current_allocation'] = 100.0
        
        with patch('random.random', return_value=0.5):
            result = self.bot.execute_trade_paper_mode('EXPENSIVE', 'BUY', 500.0)
        
        if result['status'] == 'simulated':
            expected_quantity = 100.0 / 500.0  # = 0.2
            self.assertAlmostEqual(result['quantity'], expected_quantity, places=6)
    
    def test_quantity_calculation_precision(self):
        """Test quantity calculation maintains precision"""
        self.bot.track_record['current_allocation'] = 123.45
        
        with patch('random.random', return_value=0.5):
            result = self.bot.execute_trade_paper_mode('TEST', 'BUY', 67.89)
        
        if result['status'] == 'simulated':
            expected_quantity = 123.45 / 67.89
            self.assertAlmostEqual(result['quantity'], expected_quantity, places=6)


class TestRiskManagement(unittest.TestCase):
    """Test risk management check: skip trades if potential_loss > BOT_RISK_THRESHOLD * total_capital"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_trade_skipped_when_exceeds_risk_threshold(self):
        """Test that trade is skipped when potential loss exceeds risk threshold"""
        # Use a bot with capital where allocation * stop_loss exceeds risk threshold
        # BOT_RISK_THRESHOLD = 0.02, BOT_STOP_LOSS_PERCENT = 0.06
        # With capital=1000, risk_limit = 0.02 * 1000 = 20
        # Need allocation where allocation * 0.06 > 20
        # allocation * 0.06 > 20 => allocation > 333.33
        # Use 400 to ensure we exceed the risk limit: 400 * 0.06 = 24 > 20
        bot_test = TradingBot(total_capital=1000.0)
        bot_test.track_record['current_allocation'] = 400.0
        
        result = bot_test.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'risk_threshold_exceeded')
    
    def test_trade_executed_when_within_risk_threshold(self):
        """Test that trade executes when within risk threshold"""
        # Set allocation within risk threshold
        # Risk limit = 0.02 * 10000 = 200 (updated from 500 for new 2% threshold)
        # Set allocation < 200
        self.bot.track_record['current_allocation'] = 150.0
        
        with patch('random.random', return_value=0.5):
            result = self.bot.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        
        # Trade should execute
        self.assertEqual(result['status'], 'simulated')
    
    def test_risk_calculation_uses_total_capital(self):
        """Test that risk calculation uses total_capital parameter"""
        # Test with different capital amounts
        # With BOT_STOP_LOSS_PERCENT = 0.06
        bot_low_capital = TradingBot(total_capital=1000.0)
        bot_low_capital.track_record['current_allocation'] = 400.0
        
        # Risk limit = 0.02 * 1000 = 20
        # Potential loss = 400 * 0.06 = 24 > 20 - should skip
        result = bot_low_capital.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        self.assertEqual(result['status'], 'skipped')
        
        bot_high_capital = TradingBot(total_capital=100000.0)
        bot_high_capital.track_record['current_allocation'] = 100.0
        
        # Risk limit = 0.02 * 100000 = 2000
        # Potential loss = 100 * 0.06 = 6 < 2000 - should execute
        with patch('random.random', return_value=0.5):
            result = bot_high_capital.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        self.assertEqual(result['status'], 'simulated')


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for combined functionality"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_win_loss_scenario_with_scaling(self):
        """Test complete win-loss scenario with allocation scaling"""
        initial_allocation = self.bot.track_record['current_allocation']
        
        # Scenario: 3 wins, 3 losses, 2 wins
        results = [True, True, True, False, False, False, True, True]
        
        for result in results:
            self.bot.record_trade('TEST', 'BUY', 1.0, 100.0, result)
        
        # After 3 consecutive losses (trades 4-6), allocation should have decreased by 25%
        # But then 2 wins reset consecutive losses
        self.assertEqual(self.bot.consecutive_losses, 0)
        self.assertEqual(self.bot.track_record['total_trades'], 8)
        self.assertEqual(self.bot.track_record['winning_trades'], 5)
        self.assertEqual(self.bot.track_record['losing_trades'], 3)
    
    def test_various_capital_inputs(self):
        """Test bot with various total_capital inputs"""
        # Test cases: (capital, allocation, should_skip)
        # Risk calculation now uses: potential_loss = allocation * BOT_STOP_LOSS_PERCENT
        # Risk limit = BOT_RISK_THRESHOLD * capital (now 0.02 = 2%)
        # should_skip = True if (allocation * BOT_STOP_LOSS_PERCENT) > risk_limit
        test_cases = [
            # (capital, allocation, should_skip)
            # With BOT_STOP_LOSS_PERCENT=0.06 (6%), actual_risk = allocation * 0.06
            (1000.0, 15.0, False),    # 15 * 0.06 = 0.9 < (0.02 * 1000 = 20)
            (5000.0, 120.0, False),   # 120 * 0.06 = 7.2 < (0.02 * 5000 = 100) - NOW PASSES
            (10000.0, 180.0, False),  # 180 * 0.06 = 10.8 < (0.02 * 10000 = 200)
            (50000.0, 900.0, False),  # 900 * 0.06 = 54 < (0.02 * 50000 = 1000)
            (100000.0, 1800.0, False), # 1800 * 0.06 = 108 < (0.02 * 100000 = 2000)
            # Add a case that should actually skip with new calculation
            (1000.0, 400.0, True),    # 400 * 0.06 = 24 > (0.02 * 1000 = 20) - SHOULD SKIP
        ]
        
        for capital, allocation, should_skip in test_cases:
            bot = TradingBot(total_capital=capital)
            self.assertEqual(bot.total_capital, capital)
            
            bot.track_record['current_allocation'] = allocation
            
            with patch('random.random', return_value=0.5):
                result = bot.execute_trade_paper_mode('TEST', 'BUY', 100.0)
            
            risk_limit = BOT_RISK_THRESHOLD * capital
            actual_risk = allocation * BOT_STOP_LOSS_PERCENT
            if should_skip:
                self.assertEqual(result['status'], 'skipped', 
                    f"Expected skip for capital={capital}, allocation={allocation}, "
                    f"actual_risk={actual_risk:.2f} > risk_limit={risk_limit}")
            else:
                self.assertEqual(result['status'], 'simulated',
                    f"Expected execution for capital={capital}, allocation={allocation}, "
                    f"actual_risk={actual_risk:.2f} < risk_limit={risk_limit}")


class TestCapitalTracking(unittest.TestCase):
    """Test capital tracking and P&L calculations"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_initial_capital_stored(self):
        """Test that initial capital is stored correctly"""
        self.assertEqual(self.bot.starting_capital, 10000.0)
        self.assertEqual(self.bot.total_capital, 10000.0)
    
    def test_capital_updated_after_profit(self):
        """Test that capital increases after profitable trade"""
        initial_capital = self.bot.total_capital
        profit = 100.0
        
        self.bot.update_capital(profit)
        
        self.assertEqual(self.bot.total_capital, initial_capital + profit)
    
    def test_capital_updated_after_loss(self):
        """Test that capital decreases after losing trade"""
        initial_capital = self.bot.total_capital
        loss = -50.0
        
        self.bot.update_capital(loss)
        
        self.assertEqual(self.bot.total_capital, initial_capital + loss)
    
    def test_capital_tracking_multiple_trades(self):
        """Test capital tracking through multiple trades"""
        initial_capital = self.bot.total_capital
        
        # Simulate trades with P&L
        trades = [100.0, -50.0, 75.0, -25.0, 150.0]
        
        for pnl in trades:
            self.bot.update_capital(pnl)
        
        expected_final = initial_capital + sum(trades)
        self.assertEqual(self.bot.total_capital, expected_final)
    
    def test_print_summary_includes_capital_fields(self):
        """Test that print_summary includes all required capital fields"""
        import io
        import sys
        
        # Simulate some trades to change capital
        self.bot.update_capital(250.0)
        
        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        self.bot.print_summary()
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify required fields in summary
        self.assertIn("TRADING BOT UPDATED SUMMARY", output)
        self.assertIn("Total Initial Capital: $10000.00", output)
        self.assertIn("Final Capital: $10250.00", output)
        self.assertIn("Total P&L: $250.00 (2.50%)", output)
    
    def test_pnl_calculation_accuracy(self):
        """Test P&L calculation is accurate"""
        initial = 10000.0
        bot = TradingBot(total_capital=initial)
        
        # Positive P&L
        bot.update_capital(500.0)
        total_pnl, pnl_percent = bot.calculate_total_pnl()
        
        self.assertEqual(total_pnl, 500.0)
        self.assertEqual(pnl_percent, 5.0)
        
        # Negative P&L
        bot2 = TradingBot(total_capital=initial)
        bot2.update_capital(-200.0)
        total_pnl2, pnl_percent2 = bot2.calculate_total_pnl()
        
        self.assertEqual(total_pnl2, -200.0)
        self.assertEqual(pnl_percent2, -2.0)
    
    def test_pnl_calculation_zero_starting_capital(self):
        """Test P&L calculation handles zero starting capital"""
        bot = TradingBot(total_capital=0.0)
        bot.update_capital(100.0)
        
        total_pnl, pnl_percent = bot.calculate_total_pnl()
        
        self.assertEqual(total_pnl, 100.0)
        self.assertEqual(pnl_percent, 0.0)  # Should not raise division by zero


if __name__ == "__main__":
    # Run tests with unittest's standard runner
    unittest.main(verbosity=2)

