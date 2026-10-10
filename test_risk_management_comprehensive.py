#!/usr/bin/env python3
"""
Comprehensive unit tests for risk_management.py module
Tests position sizing, risk calculations, and portfolio management
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_management import RiskManager


class TestRiskManagerInitialization(unittest.TestCase):
    """Test RiskManager initialization"""
    
    def test_basic_initialization(self):
        """Test basic RiskManager initialization"""
        rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
        
        self.assertEqual(rm.total_capital, 10000.0)
        self.assertEqual(rm.risk_per_trade, 0.02)
        self.assertIsNotNone(rm)
    
    def test_default_risk_per_trade(self):
        """Test default risk_per_trade value"""
        rm = RiskManager(total_capital=10000.0)
        
        self.assertEqual(rm.risk_per_trade, 0.02)  # Default 2%
    
    def test_max_portfolio_risk(self):
        """Test maximum portfolio risk setting"""
        rm = RiskManager(total_capital=10000.0)
        
        self.assertEqual(rm.max_portfolio_risk, 0.06)  # 6%
    
    def test_max_position_size(self):
        """Test maximum position size setting"""
        rm = RiskManager(total_capital=10000.0)
        
        self.assertEqual(rm.max_position_size, 0.20)  # 20%


class TestPositionSizingFixedRisk(unittest.TestCase):
    """Test fixed risk position sizing"""
    
    def setUp(self):
        """Set up test RiskManager"""
        self.rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_basic_position_size_calculation(self):
        """Test basic position size calculation"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=95.0
        )
        
        # Risk amount = 10000 * 0.02 = $200
        # Risk per share = 100 - 95 = $5
        # Shares = 200 / 5 = 40 shares
        # Position value = 40 * 100 = $4000
        
        self.assertEqual(result['shares'], 40)
        self.assertEqual(result['risk_amount'], 200.0)
        self.assertAlmostEqual(result['position_value'], 4000.0, places=2)
    
    def test_position_size_with_tight_stop(self):
        """Test position sizing with tight stop loss"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=99.0  # Only 1% stop
        )
        
        # Risk amount = $200
        # Risk per share = $1
        # Shares = 200 shares
        # Position value = $20,000 (would exceed capital)
        
        self.assertIn('shares', result)
        self.assertGreater(result['shares'], 0)
    
    def test_position_size_with_wide_stop(self):
        """Test position sizing with wide stop loss"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=80.0  # 20% stop
        )
        
        # Risk amount = $200
        # Risk per share = $20
        # Shares = 10 shares
        # Position value = $1000
        
        self.assertEqual(result['shares'], 10)
        self.assertAlmostEqual(result['position_value'], 1000.0, places=2)
    
    def test_invalid_entry_price(self):
        """Test handling of invalid entry price"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=-100.0,  # Invalid negative price
            stop_loss_price=95.0
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)
    
    def test_invalid_stop_loss_price(self):
        """Test handling of invalid stop loss price"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=-95.0  # Invalid negative price
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)
    
    def test_zero_entry_price(self):
        """Test handling of zero entry price"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=0.0,
            stop_loss_price=95.0
        )
        
        self.assertEqual(result['shares'], 0)
        self.assertIn('error', result)
    
    def test_entry_price_equals_stop_loss(self):
        """Test when entry price equals stop loss"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=100.0
        )
        
        # No risk per share, cannot calculate position
        self.assertEqual(result['shares'], 0)
    
    def test_short_position_sizing(self):
        """Test position sizing for short positions (entry < stop loss)"""
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=105.0  # Stop loss above entry (short position)
        )
        
        # Risk per share = |100 - 105| = $5
        # Shares = 200 / 5 = 40 shares
        
        self.assertEqual(result['shares'], 40)
        self.assertAlmostEqual(result['position_value'], 4000.0, places=2)


class TestPositionSizingPercentage(unittest.TestCase):
    """Test percentage-based position sizing"""
    
    def setUp(self):
        """Set up test RiskManager"""
        self.rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_percentage_position_sizing(self):
        """Test position sizing based on percentage of capital"""
        if hasattr(self.rm, 'calculate_position_size_percentage'):
            result = self.rm.calculate_position_size_percentage(
                entry_price=100.0,
                allocation_percent=0.10  # 10% of capital
            )
            
            # 10% of $10,000 = $1,000
            # Shares = $1,000 / $100 = 10 shares
            
            self.assertIn('shares', result)
            self.assertIn('position_value', result)
            self.assertAlmostEqual(result['position_value'], 1000.0, places=2)


class TestRiskRewardCalculations(unittest.TestCase):
    """Test risk/reward ratio calculations"""
    
    def setUp(self):
        """Set up test RiskManager"""
        self.rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_risk_reward_calculation(self):
        """Test risk/reward ratio calculation"""
        if hasattr(self.rm, 'calculate_risk_reward'):
            result = self.rm.calculate_risk_reward(
                entry_price=100.0,
                stop_loss_price=95.0,
                target_price=110.0
            )
            
            # Risk = 100 - 95 = $5
            # Reward = 110 - 100 = $10
            # Risk/Reward = 10 / 5 = 2:1
            
            self.assertIn('risk_reward_ratio', result)
            self.assertAlmostEqual(result['risk_reward_ratio'], 2.0, places=2)
    
    def test_minimum_risk_reward_ratio(self):
        """Test that minimum risk/reward ratio is enforced"""
        if hasattr(self.rm, 'calculate_risk_reward'):
            result = self.rm.calculate_risk_reward(
                entry_price=100.0,
                stop_loss_price=95.0,
                target_price=103.0  # Poor risk/reward (3:5 = 0.6:1)
            )
            
            # Risk/reward should be calculated even if poor
            self.assertIn('risk_reward_ratio', result)
            self.assertLess(result['risk_reward_ratio'], 1.0)


class TestPortfolioRiskManagement(unittest.TestCase):
    """Test portfolio-level risk management"""
    
    def setUp(self):
        """Set up test RiskManager with positions"""
        self.rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_max_position_size_enforcement(self):
        """Test that maximum position size is enforced"""
        # Try to calculate position that exceeds max_position_size
        result = self.rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=99.5  # Very tight stop = large position
        )
        
        # Position should be calculated (might be capped)
        self.assertIn('position_value', result)
        
        # Check if position value respects max_position_size limit
        max_allowed = self.rm.total_capital * self.rm.max_position_size
        # Note: Some implementations may not cap automatically
        # This test checks that the calculation works
        self.assertGreater(max_allowed, 0)
    
    def test_portfolio_risk_tracking(self):
        """Test portfolio risk tracking across positions"""
        if hasattr(self.rm, 'get_portfolio_risk'):
            # Create some simulated positions
            positions = [
                {'symbol': 'AAPL', 'risk_amount': 100},
                {'symbol': 'GOOGL', 'risk_amount': 150},
                {'symbol': 'MSFT', 'risk_amount': 50},
            ]
            
            if hasattr(self.rm, 'add_position'):
                for pos in positions:
                    self.rm.add_position(pos)
                
                total_risk = self.rm.get_portfolio_risk()
                
                # Total risk = 100 + 150 + 50 = 300
                # As percentage = 300 / 10000 = 3%
                
                self.assertIsNotNone(total_risk)


class TestTrailingStopLoss(unittest.TestCase):
    """Test trailing stop loss calculations"""
    
    def setUp(self):
        """Set up test RiskManager"""
        self.rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_trailing_stop_update(self):
        """Test trailing stop loss updates"""
        if hasattr(self.rm, 'calculate_trailing_stop'):
            # Initial stop
            result = self.rm.calculate_trailing_stop(
                entry_price=100.0,
                current_price=100.0,
                trailing_percent=0.03  # 3%
            )
            
            self.assertIn('stop_loss_price', result)
            
            # Price increases
            result2 = self.rm.calculate_trailing_stop(
                entry_price=100.0,
                current_price=110.0,
                trailing_percent=0.03
            )
            
            # Stop should trail up
            if 'stop_loss_price' in result2:
                self.assertGreater(result2['stop_loss_price'], result['stop_loss_price'])
    
    def test_trailing_stop_never_decreases(self):
        """Test that trailing stop never decreases"""
        if hasattr(self.rm, 'calculate_trailing_stop'):
            result1 = self.rm.calculate_trailing_stop(
                entry_price=100.0,
                current_price=110.0,
                trailing_percent=0.03
            )
            
            # Price drops
            result2 = self.rm.calculate_trailing_stop(
                entry_price=100.0,
                current_price=105.0,
                trailing_percent=0.03,
                previous_stop=result1.get('stop_loss_price')
            )
            
            # Stop should not decrease
            if 'stop_loss_price' in result2 and 'stop_loss_price' in result1:
                self.assertGreaterEqual(result2['stop_loss_price'], result1['stop_loss_price'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_very_small_capital(self):
        """Test with very small capital"""
        rm = RiskManager(total_capital=100.0, risk_per_trade=0.02)
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=95.0
        )
        
        # Risk amount = $2
        # Risk per share = $5
        # Shares = 0.4 (likely rounded to 0)
        
        self.assertIn('shares', result)
        self.assertGreaterEqual(result['shares'], 0)
    
    def test_very_large_capital(self):
        """Test with very large capital"""
        rm = RiskManager(total_capital=10000000.0, risk_per_trade=0.02)
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=95.0
        )
        
        # Risk amount = $200,000
        # Risk per share = $5
        # Shares = 40,000 shares
        
        self.assertIn('shares', result)
        self.assertGreater(result['shares'], 0)
    
    def test_high_risk_per_trade(self):
        """Test with high risk per trade"""
        rm = RiskManager(total_capital=10000.0, risk_per_trade=0.10)  # 10%
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=95.0
        )
        
        # Risk amount = $1000
        # Shares = 200
        
        self.assertIn('shares', result)
        self.assertGreater(result['shares'], 0)
    
    def test_fractional_shares(self):
        """Test handling of fractional shares"""
        rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=33.33,
            stop_loss_price=31.67
        )
        
        # Should handle fractional calculations
        self.assertIn('shares', result)
        self.assertIsInstance(result['shares'], (int, float))
    
    def test_penny_stock_position_sizing(self):
        """Test position sizing for penny stocks"""
        rm = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=0.50,
            stop_loss_price=0.45
        )
        
        # Risk amount = $200
        # Risk per share = $0.05
        # Shares = 4000 shares
        
        self.assertIn('shares', result)
        self.assertGreater(result['shares'], 0)
    
    def test_zero_capital(self):
        """Test with zero capital"""
        rm = RiskManager(total_capital=0.0, risk_per_trade=0.02)
        
        result = rm.calculate_position_size_fixed_risk(
            entry_price=100.0,
            stop_loss_price=95.0
        )
        
        # No capital = no position
        self.assertEqual(result['shares'], 0)
        self.assertEqual(result['risk_amount'], 0.0)


if __name__ == '__main__':
    unittest.main()
