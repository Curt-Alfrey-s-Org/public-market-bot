#!/usr/bin/env python3
"""
Test suite for risk_management.py fixes
Tests validation completeness, PDT integration, and Kelly Criterion edge cases
"""

import unittest
import logging
from unittest.mock import MagicMock, patch
from risk_management import RiskManager


class TestValidateTradeCompleteness(unittest.TestCase):
    """Test that validate_trade returns complete validation results"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_validate_trade_collects_all_reasons(self):
        """Test that validation collects all failure reasons, not just the first one"""
        # Create multiple conditions that would fail
        # 1. Invalid entry price (causes position sizing error)
        # 2. Portfolio risk exceeded
        
        # First test: invalid price with portfolio risk
        current_positions = {
            'AAPL': {'risk_amount': 700},  # 7% risk
            'MSFT': {'risk_amount': 300}   # 3% risk (total 10% exceeds 6% max)
        }
        
        validation = self.risk_mgr.validate_trade(
            entry_price=-100.0,  # Invalid price
            stop_loss_price=95.0,
            current_positions=current_positions
        )
        
        # Should collect position sizing error
        self.assertFalse(validation['is_valid'])
        self.assertIn('reasons', validation)
        self.assertGreater(len(validation['reasons']), 0)
        
        # Check that error message is captured
        self.assertTrue(any('positive' in reason.lower() for reason in validation['reasons']))
    
    def test_validate_trade_continues_after_position_error(self):
        """Test that validation continues checking even after position sizing error"""
        # Portfolio risk that exceeds max
        current_positions = {
            'AAPL': {'risk_amount': 700},  # 7% risk (exceeds 6% max)
        }
        
        validation = self.risk_mgr.validate_trade(
            entry_price=-50.0,  # Invalid entry price
            stop_loss_price=45.0,
            current_positions=current_positions
        )
        
        # Should have collected both the position error AND portfolio risk error
        self.assertFalse(validation['is_valid'])
        self.assertGreaterEqual(len(validation['reasons']), 1)
        
        # Summary should contain all reasons
        self.assertIn('summary', validation)
    
    def test_validate_trade_warnings_present(self):
        """Test that warnings are collected properly"""
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            target_price=153.0  # Only 1:1 risk/reward (unfavorable)
        )
        
        # Should have warning about unfavorable risk/reward
        self.assertIn('warnings', validation)
        self.assertGreater(len(validation['warnings']), 0)
        self.assertTrue(any('unfavorable' in warning.lower() for warning in validation['warnings']))
        
        # Summary should mention warnings
        self.assertIn('warning', validation['summary'].lower())


class TestPDTIntegration(unittest.TestCase):
    """Test PDT compliance integration in validate_trade"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_validate_trade_with_pdt_checker_passing(self):
        """Test that PDT checker is called and passing allows trade"""
        # Mock PDT checker that passes
        pdt_checker = MagicMock(return_value=(True, "PDT OK: 0/3 day trades"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='BUY',
            pdt_checker=pdt_checker
        )
        
        # PDT checker should be called
        pdt_checker.assert_called_once()
        
        # Validation should pass
        self.assertTrue(validation['is_valid'])
        self.assertEqual(len(validation['reasons']), 0)
    
    def test_validate_trade_with_pdt_checker_failing(self):
        """Test that PDT checker failure blocks trade"""
        # Mock PDT checker that fails
        pdt_checker = MagicMock(return_value=(False, "PDT Limit Reached: 3/3 day trades"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='BUY',
            pdt_checker=pdt_checker
        )
        
        # PDT checker should be called
        pdt_checker.assert_called_once()
        
        # Validation should fail
        self.assertFalse(validation['is_valid'])
        self.assertGreater(len(validation['reasons']), 0)
        self.assertTrue(any('pdt' in reason.lower() for reason in validation['reasons']))
    
    def test_validate_trade_pdt_not_checked_for_sell(self):
        """Test that PDT checker is not called for SELL actions"""
        # Mock PDT checker
        pdt_checker = MagicMock(return_value=(True, "PDT OK"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='SELL',
            pdt_checker=pdt_checker
        )
        
        # PDT checker should NOT be called for SELL
        pdt_checker.assert_not_called()
        # Validation result should still be a proper dictionary and not blocked by PDT
        self.assertIsInstance(validation, dict)
        self.assertIn('is_valid', validation)
    
    def test_validate_trade_pdt_checker_exception_handling(self):
        """Test that PDT checker exceptions are handled gracefully"""
        # Mock PDT checker that raises exception
        pdt_checker = MagicMock(side_effect=Exception("PDT check error"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='BUY',
            pdt_checker=pdt_checker
        )
        
        # Should still return validation with warning
        self.assertIsInstance(validation, dict)
        self.assertIn('warnings', validation)
        # Error should be in warnings, not block the trade entirely
        self.assertTrue(any('pdt check failed' in warning.lower() for warning in validation['warnings']))


class TestHoldingPeriodIntegration(unittest.TestCase):
    """Test holding period integration in validate_trade"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_validate_trade_with_holding_checker_passing(self):
        """Test that holding period checker passing allows trade"""
        # Mock holding checker that passes
        holding_checker = MagicMock(return_value=(True, "Holding period met: 25h held"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='SELL',
            holding_period_checker=holding_checker
        )
        
        # Holding checker should be called with symbol and action
        holding_checker.assert_called_once_with('AAPL', 'SELL')
        
        # Validation should pass
        self.assertTrue(validation['is_valid'])
        self.assertEqual(len(validation['reasons']), 0)
    
    def test_validate_trade_with_holding_checker_failing(self):
        """Test that holding period checker failure blocks trade"""
        # Mock holding checker that fails
        holding_checker = MagicMock(return_value=(False, "Holding period not met: 5h held, 24h required"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='SELL',
            holding_period_checker=holding_checker
        )
        
        # Holding checker should be called
        holding_checker.assert_called_once_with('AAPL', 'SELL')
        
        # Validation should fail
        self.assertFalse(validation['is_valid'])
        self.assertGreater(len(validation['reasons']), 0)
        self.assertTrue(any('holding period' in reason.lower() for reason in validation['reasons']))
    
    def test_validate_trade_holding_not_checked_for_buy(self):
        """Test that holding checker is not called for BUY actions"""
        holding_checker = MagicMock(return_value=(True, "Holding OK"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='BUY',
            holding_period_checker=holding_checker
        )
        
        # Holding checker should NOT be called for BUY
        holding_checker.assert_not_called()
    
    def test_validate_trade_holding_checker_exception_handling(self):
        """Test that holding checker exceptions are handled gracefully"""
        # Mock holding checker that raises exception
        holding_checker = MagicMock(side_effect=Exception("Holding check error"))
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            symbol='AAPL',
            action='SELL',
            holding_period_checker=holding_checker
        )
        
        # Should still return validation with warning
        self.assertIsInstance(validation, dict)
        self.assertIn('warnings', validation)
        # Error should be in warnings
        self.assertTrue(any('holding period check failed' in warning.lower() for warning in validation['warnings']))


class TestCombinedValidation(unittest.TestCase):
    """Test combined validation scenarios"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_validate_trade_multiple_failures(self):
        """Test that multiple validation failures are all captured"""
        # Mock checkers that both fail
        pdt_checker = MagicMock(return_value=(False, "PDT limit reached"))
        holding_checker = MagicMock(return_value=(False, "Holding period not met"))
        
        # Portfolio risk exceeded
        current_positions = {
            'MSFT': {'risk_amount': 700}  # 7% risk (exceeds 6% max)
        }
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            pdt_checker=pdt_checker,
            holding_checker=holding_checker,
            action='BUY',
            current_positions=current_positions,
        )
        
        
        # Should have multiple failure reasons
        self.assertFalse(validation['is_valid'])
        self.assertGreaterEqual(len(validation['reasons']), 2)
        
        # Should have both PDT and portfolio risk reasons
        reasons_text = ' '.join(validation['reasons']).lower()
        self.assertIn('pdt', reasons_text)
        self.assertIn('portfolio', reasons_text)


class TestKellyCriterionEdgeCases(unittest.TestCase):
    """Test Kelly Criterion error handling improvements"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    @patch('risk_management.logger')
    def test_kelly_criterion_zero_avg_loss_logs_error(self, mock_logger):
        """Test that zero avg_loss logs ERROR not just WARNING"""
        result = self.risk_mgr.calculate_kelly_criterion(
            win_rate=0.60,
            avg_win=300,
            avg_loss=0.0
        )
        
        # Should return 0
        self.assertEqual(result, 0.0)
        
        # Should log ERROR, not WARNING
        mock_logger.error.assert_called_once()
        # Check that the error message contains useful info
        error_call = mock_logger.error.call_args[0][0]
        self.assertIn('Kelly Criterion', error_call)
        self.assertIn('Invalid', error_call)
    
    @patch('risk_management.logger')
    def test_kelly_criterion_negative_avg_loss_logs_error(self, mock_logger):
        """Test that negative avg_loss logs ERROR"""
        result = self.risk_mgr.calculate_kelly_criterion(
            win_rate=0.60,
            avg_win=300,
            avg_loss=-100
        )
        
        # Should return 0
        self.assertEqual(result, 0.0)
        
        # Should log ERROR
        mock_logger.error.assert_called_once()
    
    def test_kelly_criterion_valid_input_still_works(self):
        """Test that valid inputs still work correctly"""
        result = self.risk_mgr.calculate_kelly_criterion(
            win_rate=0.60,
            avg_win=300,
            avg_loss=200
        )
        
        # Should return a valid percentage
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, self.risk_mgr.max_position_size)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that changes maintain backward compatibility"""
    
    def setUp(self):
        """Set up risk manager"""
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_validate_trade_without_optional_params(self):
        """Test that validate_trade works without new optional parameters"""
        # Call without new parameters (backward compatible)
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0
        )
        
        # Should work as before
        self.assertIsInstance(validation, dict)
        self.assertIn('is_valid', validation)
        self.assertIn('reasons', validation)
        self.assertIn('warnings', validation)
        self.assertIn('summary', validation)
    
    def test_validate_trade_with_only_target(self):
        """Test backward compatibility with target_price only"""
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            target_price=159.0
        )
        
        # Should work as before
        self.assertTrue(validation['is_valid'])
        self.assertIsInstance(validation['warnings'], list)
    
    def test_validate_trade_with_positions_only(self):
        """Test backward compatibility with current_positions only"""
        current_positions = {
            'AAPL': {'risk_amount': 100, 'position_value': 1000}
        }
        
        validation = self.risk_mgr.validate_trade(
            entry_price=150.0,
            stop_loss_price=147.0,
            current_positions=current_positions
        )
        
        # Should work as before
        self.assertIsInstance(validation, dict)
        self.assertIn('is_valid', validation)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.ERROR)
    
    # Run tests
    unittest.main()
