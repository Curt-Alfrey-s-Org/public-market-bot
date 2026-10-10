#!/usr/bin/env python3
"""
Test script to verify win rate auto-tuning via AI/ML integration
Tests that apply_ai_suggestions() uses track_record to trigger ML optimization
when win rate is below the 70% target
"""

import os
import sys
import unittest
from unittest.mock import patch

# Set test environment variables before importing main
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['BOT_RISK_THRESHOLD'] = '0.06'
os.environ['BOT_MIN_ALLOCATION'] = '500'
os.environ['BOT_MAX_ALLOCATION'] = '5000'
os.environ['BOT_TRAILING_STOP_PERCENT'] = '0.03'
os.environ['BOT_MAX_OPEN_POSITIONS'] = '50'
os.environ['BOT_MAX_CONSECUTIVE_LOSSES'] = '3'
os.environ['BOT_POSITION_SIZE'] = '0.05'
os.environ['BOT_STOP_LOSS_PERCENT'] = '0.06'
os.environ['BOT_TAKE_PROFIT_PERCENT'] = '0.1'
os.environ['SIMULATED_WIN_RATE'] = '0.6'
os.environ['WIN_RATE_TARGET'] = '0.70'
os.environ['CAPITAL_FLOOR_PERCENT'] = '0.10'
os.environ['ENABLE_ALERTS'] = 'False'

from main import TradingBot, WIN_RATE_TARGET


class TestWinRateAutoTuning(unittest.TestCase):
    """Test cases for win rate auto-tuning feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_win_rate_target_constant_exists(self):
        """Test that WIN_RATE_TARGET constant is defined"""
        self.assertEqual(WIN_RATE_TARGET, 0.70)
        print(f"✓ WIN_RATE_TARGET constant is set to {WIN_RATE_TARGET:.0%}")
    
    def test_apply_ai_suggestions_checks_win_rate(self):
        """Test that apply_ai_suggestions checks track_record win rate"""
        # Set up bot with low win rate (below target)
        self.bot.track_record['win_rate'] = 0.55  # 55% < 70% target
        self.bot.track_record['total_trades'] = 20  # Enough trades for tuning
        
        # Mock the ML optimizer
        with patch.object(self.bot, 'optimize_parameters_ml') as mock_optimize:
            mock_optimize.return_value = (
                {'BOT_TRAILING_STOP_PERCENT': 0.04},  # Optimized params
                0.72  # Predicted win rate
            )
            
            # Mock AI response (empty is fine, we're testing the win rate check)
            ai_response = {'error': 'test'}
            
            # Call apply_ai_suggestions
            self.bot.apply_ai_suggestions(ai_response, auto_apply=True)
            
            # Verify ML optimization was triggered
            mock_optimize.assert_called_once()
            print("✓ ML optimization triggered when win rate below target")
    
    def test_apply_ai_suggestions_skips_optimization_when_win_rate_high(self):
        """Test that optimization is skipped when win rate is above target"""
        # Set up bot with high win rate (above target)
        self.bot.track_record['win_rate'] = 0.75  # 75% > 70% target
        self.bot.track_record['total_trades'] = 20
        
        # Mock the ML optimizer
        with patch.object(self.bot, 'optimize_parameters_ml') as mock_optimize:
            # Mock AI response
            ai_response = {'error': 'test'}
            
            # Call apply_ai_suggestions
            self.bot.apply_ai_suggestions(ai_response, auto_apply=True)
            
            # Verify ML optimization was NOT triggered
            mock_optimize.assert_not_called()
            print("✓ ML optimization skipped when win rate above target")
    
    def test_apply_ai_suggestions_requires_minimum_trades(self):
        """Test that optimization requires at least 10 trades"""
        # Set up bot with low win rate but insufficient trades
        self.bot.track_record['win_rate'] = 0.55  # 55% < 70% target
        self.bot.track_record['total_trades'] = 5  # Less than 10 trades
        
        # Mock the ML optimizer
        with patch.object(self.bot, 'optimize_parameters_ml') as mock_optimize:
            # Mock AI response
            ai_response = {'error': 'test'}
            
            # Call apply_ai_suggestions
            result = self.bot.apply_ai_suggestions(ai_response, auto_apply=True)
            
            # Verify ML optimization was NOT triggered
            mock_optimize.assert_not_called()
            print("✓ ML optimization skipped when insufficient trades (<10)")
    
    def test_apply_ai_suggestions_applies_ml_params_when_auto_apply_true(self):
        """Test that ML-optimized parameters are applied when auto_apply=True"""
        # Set up bot with low win rate
        self.bot.track_record['win_rate'] = 0.55
        self.bot.track_record['total_trades'] = 20
        
        # Store original trailing stop
        original_trailing_stop = self.bot.trailing_stop_percent
        
        # Mock the ML optimizer with a different trailing stop
        optimized_trailing_stop = 0.04
        with patch.object(self.bot, 'optimize_parameters_ml') as mock_optimize:
            mock_optimize.return_value = (
                {'BOT_TRAILING_STOP_PERCENT': optimized_trailing_stop},
                0.72
            )
            
            # Mock alert system to avoid side effects
            with patch.object(self.bot.alert_system, 'send_alert'):
                # Mock AI response
                ai_response = {'error': 'test'}
                
                # Call apply_ai_suggestions with auto_apply=True
                self.bot.apply_ai_suggestions(ai_response, auto_apply=True)
                
                # Verify trailing stop was updated
                self.assertEqual(self.bot.trailing_stop_percent, optimized_trailing_stop)
                print(f"✓ ML-optimized parameter applied: {original_trailing_stop:.3f} -> {optimized_trailing_stop:.3f}")
    
    def test_apply_ai_suggestions_logs_ml_optimization_info(self):
        """Test that ML optimization logs appropriate information"""
        # Set up bot with low win rate
        self.bot.track_record['win_rate'] = 0.55
        self.bot.track_record['total_trades'] = 20
        
        # Mock the ML optimizer
        with patch.object(self.bot, 'optimize_parameters_ml') as mock_optimize:
            mock_optimize.return_value = (
                {'BOT_TRAILING_STOP_PERCENT': 0.04},
                0.72
            )
            
            # Capture log output
            with patch('main.logger') as mock_logger:
                # Mock AI response
                ai_response = {'error': 'test'}
                
                # Call apply_ai_suggestions
                self.bot.apply_ai_suggestions(ai_response, auto_apply=False)
                
                # Verify appropriate log messages were created
                log_calls = [str(call) for call in mock_logger.info.call_args_list]
                
                # Check that win rate auto-tune messages were logged
                win_rate_logs = [call for call in log_calls if 'WIN RATE AUTO-TUNE' in call]
                self.assertGreater(len(win_rate_logs), 0, "Expected WIN RATE AUTO-TUNE log messages")
                print(f"✓ ML optimization logged {len(win_rate_logs)} win rate auto-tune messages")


def run_tests():
    """Run all tests and print results"""
    print("="*60)
    print("WIN RATE AUTO-TUNING TEST SUITE")
    print("="*60)
    print(f"Target Win Rate: {WIN_RATE_TARGET:.0%}")
    print("="*60 + "\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWinRateAutoTuning)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
