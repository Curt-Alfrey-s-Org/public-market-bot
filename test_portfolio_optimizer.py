#!/usr/bin/env python3
"""
Tests for portfolio optimizer module
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_optimizer import PortfolioOptimizer

# Test constants
FLOATING_POINT_TOLERANCE = 1e-10  # Tolerance for floating point comparisons


class TestPortfolioOptimizer(unittest.TestCase):
    """Test portfolio optimizer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = PortfolioOptimizer(risk_free_rate=0.02)
        
        # Add sample price data for multiple symbols
        self.symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Generate sample price data (correlated)
        np.random.seed(42)
        n_points = 100
        
        # AAPL: trending up
        self.optimizer.add_price_data('AAPL', list(100 + np.cumsum(np.random.normal(0.1, 1, n_points))))
        
        # MSFT: trending up (correlated with AAPL)
        self.optimizer.add_price_data('MSFT', list(200 + np.cumsum(np.random.normal(0.1, 1.2, n_points))))
        
        # GOOGL: more volatile
        self.optimizer.add_price_data('GOOGL', list(150 + np.cumsum(np.random.normal(0.05, 2, n_points))))
    
    def test_initialization(self):
        """Test optimizer initialization"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.risk_free_rate, 0.02)
        self.assertIsInstance(self.optimizer.price_history, dict)
    
    def test_add_price_data(self):
        """Test adding price data"""
        optimizer = PortfolioOptimizer()
        prices = [100, 101, 102, 103]
        
        optimizer.add_price_data('TEST', prices)
        
        self.assertIn('TEST', optimizer.price_history)
        self.assertEqual(optimizer.price_history['TEST'], prices)
    
    def test_calculate_returns(self):
        """Test calculating returns from prices"""
        prices = [100, 102, 101, 103]
        returns = self.optimizer.calculate_returns(prices)
        
        self.assertEqual(len(returns), 3)  # n-1 returns
        self.assertAlmostEqual(returns[0], 0.02, places=4)  # (102-100)/100
        self.assertAlmostEqual(returns[1], -0.0098, places=4)  # (101-102)/102
    
    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data"""
        prices = [100]
        returns = self.optimizer.calculate_returns(prices)
        
        self.assertEqual(len(returns), 0)
    
    def test_calculate_covariance_matrix(self):
        """Test covariance matrix calculation"""
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        self.assertIsNotNone(cov_matrix)
        self.assertEqual(cov_matrix.shape, (3, 3))
        
        # Matrix should be symmetric
        np.testing.assert_array_almost_equal(cov_matrix, cov_matrix.T)
        
        # Diagonal elements (variances) should be positive
        for i in range(3):
            self.assertGreater(cov_matrix[i, i], 0)
    
    def test_calculate_correlation_matrix(self):
        """Test correlation matrix calculation"""
        corr_matrix = self.optimizer.calculate_correlation_matrix(self.symbols)
        
        self.assertIsNotNone(corr_matrix)
        self.assertEqual(corr_matrix.shape, (3, 3))
        
        # Diagonal should be 1 (perfect self-correlation)
        for i in range(3):
            self.assertAlmostEqual(corr_matrix[i, i], 1.0, places=5)
        
        # All correlations should be between -1 and 1 (with small tolerance for floating point)
        for i in range(3):
            for j in range(3):
                self.assertGreaterEqual(corr_matrix[i, j], -1.0)
                self.assertLessEqual(corr_matrix[i, j], 1.0 + FLOATING_POINT_TOLERANCE)
    
    def test_calculate_expected_returns(self):
        """Test expected returns calculation"""
        expected_returns = self.optimizer.calculate_expected_returns(self.symbols)
        
        self.assertIsNotNone(expected_returns)
        self.assertEqual(len(expected_returns), 3)
        self.assertIsInstance(expected_returns, np.ndarray)
    
    def test_portfolio_performance(self):
        """Test portfolio performance calculation"""
        weights = np.array([0.33, 0.33, 0.34])
        expected_returns = self.optimizer.calculate_expected_returns(self.symbols)
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        ret, vol, sharpe = self.optimizer.portfolio_performance(
            weights, expected_returns, cov_matrix
        )
        
        self.assertIsInstance(ret, float)
        self.assertIsInstance(vol, float)
        self.assertIsInstance(sharpe, float)
        
        # Volatility should be positive
        self.assertGreater(vol, 0)
    
    def test_optimize_sharpe_ratio(self):
        """Test Sharpe ratio optimization"""
        expected_returns = self.optimizer.calculate_expected_returns(self.symbols)
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        weights = self.optimizer.optimize_sharpe_ratio(expected_returns, cov_matrix)
        
        if weights is not None:  # Only if scipy is available
            self.assertEqual(len(weights), 3)
            
            # Weights should sum to 1
            self.assertAlmostEqual(np.sum(weights), 1.0, places=4)
            
            # All weights should be non-negative
            for w in weights:
                self.assertGreaterEqual(w, 0)
    
    def test_optimize_minimum_variance(self):
        """Test minimum variance optimization"""
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        weights = self.optimizer.optimize_minimum_variance(cov_matrix)
        
        if weights is not None:  # Only if scipy is available
            self.assertEqual(len(weights), 3)
            
            # Weights should sum to 1
            self.assertAlmostEqual(np.sum(weights), 1.0, places=4)
            
            # All weights should be non-negative
            for w in weights:
                self.assertGreaterEqual(w, 0)
    
    def test_calculate_risk_parity_weights(self):
        """Test risk parity weights calculation"""
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        weights = self.optimizer.calculate_risk_parity_weights(cov_matrix)
        
        if weights is not None:  # Only if scipy is available
            self.assertEqual(len(weights), 3)
            
            # Weights should sum to 1
            self.assertAlmostEqual(np.sum(weights), 1.0, places=4)
            
            # All weights should be positive (risk parity avoids zeros)
            for w in weights:
                self.assertGreater(w, 0)
    
    def test_get_optimal_allocation_equal(self):
        """Test equal allocation method"""
        total_capital = 10000
        allocations = self.optimizer.get_optimal_allocation(
            self.symbols, total_capital, method='equal'
        )
        
        self.assertIsNotNone(allocations)
        self.assertEqual(len(allocations), 3)
        
        # Each symbol should get equal allocation
        expected_per_symbol = total_capital / 3
        for symbol in self.symbols:
            self.assertAlmostEqual(allocations[symbol], expected_per_symbol, places=2)
    
    def test_get_optimal_allocation_sharpe(self):
        """Test Sharpe ratio allocation method"""
        total_capital = 10000
        allocations = self.optimizer.get_optimal_allocation(
            self.symbols, total_capital, method='sharpe'
        )
        
        self.assertIsNotNone(allocations)
        self.assertEqual(len(allocations), 3)
        
        # Total allocation should equal capital
        total_allocated = sum(allocations.values())
        self.assertAlmostEqual(total_allocated, total_capital, places=0)
        
        # All allocations should be non-negative
        for amount in allocations.values():
            self.assertGreaterEqual(amount, 0)
    
    def test_get_optimal_allocation_min_variance(self):
        """Test minimum variance allocation method"""
        total_capital = 10000
        allocations = self.optimizer.get_optimal_allocation(
            self.symbols, total_capital, method='min_variance'
        )
        
        self.assertIsNotNone(allocations)
        self.assertEqual(len(allocations), 3)
        
        # Total allocation should equal capital
        total_allocated = sum(allocations.values())
        self.assertAlmostEqual(total_allocated, total_capital, places=0)
    
    def test_get_optimal_allocation_risk_parity(self):
        """Test risk parity allocation method"""
        total_capital = 10000
        allocations = self.optimizer.get_optimal_allocation(
            self.symbols, total_capital, method='risk_parity'
        )
        
        self.assertIsNotNone(allocations)
        self.assertEqual(len(allocations), 3)
        
        # Total allocation should equal capital
        total_allocated = sum(allocations.values())
        self.assertAlmostEqual(total_allocated, total_capital, places=0)
    
    def test_get_optimal_allocation_invalid_method(self):
        """Test allocation with invalid method"""
        total_capital = 10000
        allocations = self.optimizer.get_optimal_allocation(
            self.symbols, total_capital, method='invalid'
        )
        
        self.assertIsNone(allocations)
    
    def test_calculate_diversification_score(self):
        """Test diversification score calculation"""
        score = self.optimizer.calculate_diversification_score(self.symbols)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_calculate_diversification_score_single_symbol(self):
        """Test diversification score with single symbol"""
        score = self.optimizer.calculate_diversification_score(['AAPL'])
        
        self.assertEqual(score, 0.0)  # No diversification possible
    
    def test_suggest_rebalancing_no_change(self):
        """Test rebalancing with minimal deviation"""
        current = {'AAPL': 3333, 'MSFT': 3333, 'GOOGL': 3334}
        target = {'AAPL': 3333, 'MSFT': 3333, 'GOOGL': 3334}
        
        trades = self.optimizer.suggest_rebalancing(current, target, threshold=0.05)
        
        self.assertEqual(len(trades), 0)  # No rebalancing needed
    
    def test_suggest_rebalancing_with_deviation(self):
        """Test rebalancing with significant deviation"""
        current = {'AAPL': 5000, 'MSFT': 3000, 'GOOGL': 2000}
        target = {'AAPL': 3333, 'MSFT': 3333, 'GOOGL': 3334}
        
        trades = self.optimizer.suggest_rebalancing(current, target, threshold=0.05)
        
        # Should suggest trades to rebalance
        self.assertGreater(len(trades), 0)
        
        # Check that AAPL needs to be sold (current > target)
        if 'AAPL' in trades:
            self.assertLess(trades['AAPL'], 0)
        
        # Check that GOOGL needs to be bought (current < target)
        if 'GOOGL' in trades:
            self.assertGreater(trades['GOOGL'], 0)
    
    def test_suggest_rebalancing_custom_threshold(self):
        """Test rebalancing with custom threshold"""
        current = {'AAPL': 3400, 'MSFT': 3333, 'GOOGL': 3267}
        target = {'AAPL': 3333, 'MSFT': 3333, 'GOOGL': 3334}
        
        # With 5% threshold, no rebalancing
        trades_5pct = self.optimizer.suggest_rebalancing(current, target, threshold=0.05)
        
        # With 1% threshold, should rebalance
        trades_1pct = self.optimizer.suggest_rebalancing(current, target, threshold=0.01)
        
        # 1% threshold should have more trades
        self.assertGreaterEqual(len(trades_1pct), len(trades_5pct))


class TestPortfolioOptimizerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_covariance_with_missing_symbol(self):
        """Test covariance calculation with missing symbol"""
        optimizer = PortfolioOptimizer()
        optimizer.add_price_data('AAPL', [100, 101, 102])
        
        cov_matrix = optimizer.calculate_covariance_matrix(['AAPL', 'MISSING'])
        
        self.assertIsNone(cov_matrix)
    
    def test_covariance_with_insufficient_data(self):
        """Test covariance with insufficient price data"""
        optimizer = PortfolioOptimizer()
        optimizer.add_price_data('AAPL', [100, 101])  # Only 2 prices
        optimizer.add_price_data('MSFT', [200, 201])
        
        cov_matrix = optimizer.calculate_covariance_matrix(['AAPL', 'MSFT'])
        
        # Should return None or handle gracefully
        # (depends on implementation - need at least 20 points)
        self.assertIsNone(cov_matrix)
    
    def test_expected_returns_with_missing_symbol(self):
        """Test expected returns with missing symbol"""
        optimizer = PortfolioOptimizer()
        optimizer.add_price_data('AAPL', [100, 101, 102])
        
        returns = optimizer.calculate_expected_returns(['AAPL', 'MISSING'])
        
        self.assertIsNone(returns)
    
    def test_allocation_with_no_price_data(self):
        """Test allocation with no price data"""
        optimizer = PortfolioOptimizer()
        
        allocations = optimizer.get_optimal_allocation(['AAPL', 'MSFT'], 10000)
        
        # Should fall back to equal allocation
        self.assertIsNotNone(allocations)
        self.assertAlmostEqual(allocations['AAPL'], 5000, places=0)
        self.assertAlmostEqual(allocations['MSFT'], 5000, places=0)


class TestEfficientFrontier(unittest.TestCase):
    """Test efficient frontier calculation"""
    
    def setUp(self):
        """Set up test fixtures with adequate data"""
        self.optimizer = PortfolioOptimizer()
        
        # Generate adequate price data
        np.random.seed(42)
        n_points = 100
        
        self.optimizer.add_price_data('AAPL', list(100 + np.cumsum(np.random.normal(0.1, 1, n_points))))
        self.optimizer.add_price_data('MSFT', list(200 + np.cumsum(np.random.normal(0.1, 1.2, n_points))))
        self.optimizer.add_price_data('GOOGL', list(150 + np.cumsum(np.random.normal(0.05, 2, n_points))))
        
        self.symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    def test_calculate_efficient_frontier(self):
        """Test efficient frontier calculation"""
        expected_returns = self.optimizer.calculate_expected_returns(self.symbols)
        cov_matrix = self.optimizer.calculate_covariance_matrix(self.symbols)
        
        frontier = self.optimizer.calculate_efficient_frontier(
            expected_returns, cov_matrix, num_points=10
        )
        
        if frontier is not None:  # Only if scipy is available
            self.assertGreater(len(frontier), 0)
            self.assertIn('return', frontier.columns)
            self.assertIn('volatility', frontier.columns)
            self.assertIn('sharpe_ratio', frontier.columns)
            
            # All volatilities should be positive
            self.assertTrue((frontier['volatility'] > 0).all())


if __name__ == '__main__':
    unittest.main()
