#!/usr/bin/env python3
"""
Unit tests for Monte Carlo Simulator module
"""

import unittest
import numpy as np
import pandas as pd
from monte_carlo_simulator import MonteCarloSimulator, MonteCarloResults


class TestMonteCarloSimulator(unittest.TestCase):
    """Test suite for Monte Carlo simulation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use fixed seed for reproducibility
        self.mc = MonteCarloSimulator(num_simulations=1000, random_seed=42)
    
    def test_initialization(self):
        """Test MonteCarloSimulator initialization"""
        mc = MonteCarloSimulator(num_simulations=5000, random_seed=123)
        self.assertEqual(mc.num_simulations, 5000)
        self.assertEqual(mc.random_seed, 123)
    
    def test_simulate_price_paths_shape(self):
        """Test price path simulation returns correct shape"""
        paths = self.mc.simulate_price_paths(
            initial_price=100.0,
            days=30,
            drift=0.0005,
            volatility=0.02,
            num_paths=100
        )
        
        # Should return (num_paths, days+1) because we include initial price
        self.assertEqual(paths.shape, (100, 31))
    
    def test_simulate_price_paths_initial_price(self):
        """Test that all paths start at initial price"""
        initial_price = 150.0
        paths = self.mc.simulate_price_paths(
            initial_price=initial_price,
            days=30,
            drift=0.0,
            volatility=0.02,
            num_paths=50
        )
        
        # First column should all be initial price
        np.testing.assert_array_equal(paths[:, 0], np.full(50, initial_price))
    
    def test_simulate_price_paths_positive(self):
        """Test that simulated prices remain positive"""
        paths = self.mc.simulate_price_paths(
            initial_price=100.0,
            days=252,
            drift=0.0005,
            volatility=0.02,
            num_paths=100
        )
        
        # All prices should be positive (GBM property)
        self.assertTrue(np.all(paths > 0))
    
    def test_simulate_portfolio_returns_empty(self):
        """Test portfolio simulation with no positions (cash only)"""
        initial_capital = 10000.0
        results = self.mc.simulate_portfolio_returns(
            initial_capital=initial_capital,
            positions=[],
            days=30
        )
        
        # With no positions, all outcomes should equal initial capital
        self.assertEqual(results.mean, initial_capital)
        self.assertEqual(results.std_dev, 0.0)
    
    def test_simulate_portfolio_returns_single_position(self):
        """Test portfolio simulation with single position"""
        positions = [
            {'symbol': 'AAPL', 'shares': 10, 'current_price': 150.0}
        ]
        
        results = self.mc.simulate_portfolio_returns(
            initial_capital=10000.0,
            positions=positions,
            drift=0.001,
            volatility=0.02,
            days=30
        )
        
        # Results should have reasonable values
        self.assertIsInstance(results, MonteCarloResults)
        self.assertGreater(results.mean, 0)
        self.assertGreater(results.std_dev, 0)
        self.assertEqual(len(results.simulations), 1000)
    
    def test_simulate_portfolio_returns_multiple_positions(self):
        """Test portfolio simulation with multiple positions"""
        positions = [
            {'symbol': 'AAPL', 'shares': 10, 'current_price': 150.0},
            {'symbol': 'GOOGL', 'shares': 5, 'current_price': 140.0},
            {'symbol': 'MSFT', 'shares': 8, 'current_price': 300.0}
        ]
        
        results = self.mc.simulate_portfolio_returns(
            initial_capital=15000.0,
            positions=positions,
            drift=0.0005,
            volatility=0.02,
            days=60
        )
        
        # Check results structure
        self.assertIsInstance(results, MonteCarloResults)
        self.assertGreater(results.std_dev, 0)
        self.assertIn('p5', results.percentiles)
        self.assertIn('p95', results.percentiles)
    
    def test_simulate_var_cvar(self):
        """Test VaR and CVaR calculation"""
        var, cvar = self.mc.simulate_var_cvar(
            initial_capital=10000.0,
            expected_return=0.0005,
            volatility=0.02,
            days=1,
            confidence_level=0.95
        )
        
        # VaR should be positive (loss amount)
        self.assertGreater(var, 0)
        
        # CVaR should be >= VaR (tail risk is worse)
        self.assertGreaterEqual(cvar, var)
        
        # Both should be reasonable (not more than capital)
        self.assertLess(var, 10000.0)
        self.assertLess(cvar, 10000.0)
    
    def test_simulate_var_cvar_different_confidence(self):
        """Test VaR with different confidence levels"""
        var_95, cvar_95 = self.mc.simulate_var_cvar(
            initial_capital=10000.0,
            expected_return=0.0005,
            volatility=0.02,
            days=1,
            confidence_level=0.95
        )
        
        var_99, cvar_99 = self.mc.simulate_var_cvar(
            initial_capital=10000.0,
            expected_return=0.0005,
            volatility=0.02,
            days=1,
            confidence_level=0.99
        )
        
        # Higher confidence should give higher VaR
        self.assertGreater(var_99, var_95)
    
    def test_simulate_drawdown_distribution(self):
        """Test drawdown distribution simulation"""
        dd_results = self.mc.simulate_drawdown_distribution(
            initial_capital=10000.0,
            expected_return=0.0005,
            volatility=0.02,
            days=252
        )
        
        # Check all required keys
        required_keys = [
            'mean_max_drawdown',
            'median_max_drawdown',
            'worst_drawdown_95',
            'worst_drawdown_99',
            'best_drawdown',
            'prob_drawdown_over_20pct'
        ]
        
        for key in required_keys:
            self.assertIn(key, dd_results)
        
        # Drawdowns should be negative or zero
        self.assertLessEqual(dd_results['mean_max_drawdown'], 0)
        self.assertLessEqual(dd_results['median_max_drawdown'], 0)
        
        # Worst drawdowns should be more negative than mean
        self.assertLessEqual(dd_results['worst_drawdown_95'], dd_results['mean_max_drawdown'])
        self.assertLessEqual(dd_results['worst_drawdown_99'], dd_results['worst_drawdown_95'])
        
        # Probability should be between 0 and 1
        self.assertGreaterEqual(dd_results['prob_drawdown_over_20pct'], 0)
        self.assertLessEqual(dd_results['prob_drawdown_over_20pct'], 1)
    
    def test_simulate_trade_outcomes(self):
        """Test trade outcome simulation"""
        results = self.mc.simulate_trade_outcomes(
            win_rate=0.55,
            avg_win=200.0,
            avg_loss=-150.0,
            num_trades=100
        )
        
        self.assertIsInstance(results, MonteCarloResults)
        self.assertEqual(len(results.simulations), 1000)
        
        # With positive expectancy, mean should be positive
        # Expectancy = (0.55 * 200) + (0.45 * -150) = 110 - 67.5 = 42.5 per trade
        expected_total = 42.5 * 100  # 4250
        
        # Mean should be close to expected (within 20% tolerance)
        self.assertGreater(results.mean, expected_total * 0.8)
        self.assertLess(results.mean, expected_total * 1.2)
    
    def test_simulate_trade_outcomes_negative_expectancy(self):
        """Test trade outcomes with negative expectancy"""
        results = self.mc.simulate_trade_outcomes(
            win_rate=0.40,  # Low win rate
            avg_win=100.0,
            avg_loss=-150.0,
            num_trades=50
        )
        
        # Expectancy = (0.40 * 100) + (0.60 * -150) = 40 - 90 = -50 per trade
        expected_total = -50 * 50  # -2500
        
        # Mean should be negative
        self.assertLess(results.mean, 0)
        
        # Success rate should be low
        self.assertLess(results.success_rate, 0.5)
    
    def test_simulate_strategy_robustness(self):
        """Test strategy robustness analysis"""
        
        # Simple strategy: buy and hold
        def simple_strategy(price_path):
            # P&L = final price - initial price
            return price_path[-1] - price_path[0]
        
        robustness = self.mc.simulate_strategy_robustness(
            strategy_func=simple_strategy,
            initial_price=100.0,
            days=30,
            drift_range=(-0.001, 0.002),
            volatility_range=(0.01, 0.03),
            num_scenarios=100
        )
        
        # Check required keys
        required_keys = [
            'mean_pnl',
            'median_pnl',
            'std_pnl',
            'positive_scenarios',
            'max_pnl',
            'min_pnl',
            'sharpe_ratio',
            'scenarios_tested'
        ]
        
        for key in required_keys:
            self.assertIn(key, robustness)
        
        # Should have tested requested number of scenarios
        self.assertEqual(robustness['scenarios_tested'], 100)
        
        # Positive scenarios should be between 0 and 1
        self.assertGreaterEqual(robustness['positive_scenarios'], 0)
        self.assertLessEqual(robustness['positive_scenarios'], 1)
    
    def test_parameter_sensitivity_analysis(self):
        """Test parameter sensitivity analysis"""
        
        base_params = {
            'lookback': 20,
            'threshold': 0.02
        }
        
        param_ranges = {
            'lookback': (10, 50),
            'threshold': (0.01, 0.05)
        }
        
        # Simple evaluation function
        def evaluate(params):
            # Mock performance based on parameters
            return params['lookback'] * params['threshold']
        
        df = self.mc.parameter_sensitivity_analysis(
            base_params=base_params,
            param_ranges=param_ranges,
            evaluation_func=evaluate,
            num_samples=50
        )
        
        # Should return DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        
        # Should have requested number of samples
        self.assertEqual(len(df), 50)
        
        # Should have parameter columns and performance
        self.assertIn('lookback', df.columns)
        self.assertIn('threshold', df.columns)
        self.assertIn('performance', df.columns)
        
        # Parameters should be within ranges
        self.assertTrue(df['lookback'].between(10, 50).all())
        self.assertTrue(df['threshold'].between(0.01, 0.05).all())
    
    def test_monte_carlo_results_structure(self):
        """Test MonteCarloResults dataclass structure"""
        simulations = np.random.normal(10000, 500, 1000)
        results = self.mc._create_results(simulations)
        
        # Check all attributes exist
        self.assertTrue(hasattr(results, 'simulations'))
        self.assertTrue(hasattr(results, 'mean'))
        self.assertTrue(hasattr(results, 'median'))
        self.assertTrue(hasattr(results, 'std_dev'))
        self.assertTrue(hasattr(results, 'percentiles'))
        self.assertTrue(hasattr(results, 'var_95'))
        self.assertTrue(hasattr(results, 'cvar_95'))
        self.assertTrue(hasattr(results, 'max_value'))
        self.assertTrue(hasattr(results, 'min_value'))
        self.assertTrue(hasattr(results, 'success_rate'))
        
        # Check percentiles dictionary
        self.assertIn('p5', results.percentiles)
        self.assertIn('p25', results.percentiles)
        self.assertIn('p50', results.percentiles)
        self.assertIn('p75', results.percentiles)
        self.assertIn('p95', results.percentiles)
    
    def test_generate_report(self):
        """Test report generation"""
        simulations = np.random.normal(10000, 500, 1000)
        results = self.mc._create_results(simulations)
        
        report = self.mc.generate_report(results, "Test Report")
        
        # Report should be a string
        self.assertIsInstance(report, str)
        
        # Should contain key information
        self.assertIn("Test Report", report)
        self.assertIn("Expected Value", report)
        self.assertIn("Value at Risk", report)
        self.assertIn("Success Rate", report)
        
        # Should contain numeric values
        self.assertIn("1,000", report)  # Number of simulations
    
    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same seed"""
        # Test reproducibility with two instances using same seed
        mc1 = MonteCarloSimulator(num_simulations=100, random_seed=42)
        mc2 = MonteCarloSimulator(num_simulations=100, random_seed=42)
        
        paths1 = mc1.simulate_price_paths(100.0, 10, 0.001, 0.02, num_paths=10)
        paths2 = mc2.simulate_price_paths(100.0, 10, 0.001, 0.02, num_paths=10)
        
        # Should be identical with same seed
        np.testing.assert_array_almost_equal(paths1, paths2)
    
    def test_percentiles_ordering(self):
        """Test that percentiles are correctly ordered"""
        simulations = np.random.normal(10000, 1000, 1000)
        results = self.mc._create_results(simulations)
        
        # Percentiles should be in ascending order
        self.assertLessEqual(results.percentiles['p5'], results.percentiles['p25'])
        self.assertLessEqual(results.percentiles['p25'], results.percentiles['p50'])
        self.assertLessEqual(results.percentiles['p50'], results.percentiles['p75'])
        self.assertLessEqual(results.percentiles['p75'], results.percentiles['p95'])
        
        # Median should equal 50th percentile
        self.assertAlmostEqual(results.median, results.percentiles['p50'], places=2)
    
    def test_zero_volatility(self):
        """Test simulation with zero volatility (deterministic)"""
        paths = self.mc.simulate_price_paths(
            initial_price=100.0,
            days=30,
            drift=0.001,
            volatility=0.0,  # No randomness
            num_paths=10
        )
        
        # With zero volatility, all paths should be identical
        for i in range(1, paths.shape[0]):
            np.testing.assert_array_almost_equal(paths[0], paths[i], decimal=5)
    
    def test_high_win_rate_success(self):
        """Test that high win rate produces high success rate"""
        results = self.mc.simulate_trade_outcomes(
            win_rate=0.80,  # 80% win rate
            avg_win=100.0,
            avg_loss=-50.0,
            num_trades=50
        )
        
        # Success rate should be high (most simulations end positive)
        self.assertGreater(results.success_rate, 0.7)
    
    def test_edge_case_zero_simulations(self):
        """Test handling of edge case with minimal simulations"""
        mc = MonteCarloSimulator(num_simulations=1)
        
        results = mc.simulate_trade_outcomes(
            win_rate=0.5,
            avg_win=100.0,
            avg_loss=-100.0,
            num_trades=10
        )
        
        # Should still produce valid results
        self.assertIsInstance(results, MonteCarloResults)
        self.assertEqual(len(results.simulations), 1)


class TestRiskManagerMonteCarloIntegration(unittest.TestCase):
    """Test suite for RiskManager Monte Carlo integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        from risk_management import RiskManager
        self.risk_mgr = RiskManager(total_capital=10000.0, risk_per_trade=0.02)
    
    def test_calculate_monte_carlo_var_with_simulator(self):
        """Test VaR calculation when Monte Carlo is available"""
        if not self.risk_mgr.mc_simulator:
            self.skipTest("Monte Carlo simulator not available")
        
        result = self.risk_mgr.calculate_monte_carlo_var(
            expected_return=0.0005,
            volatility=0.02,
            days=1,
            confidence_level=0.95
        )
        
        self.assertIsNotNone(result)
        var, cvar = result
        
        # VaR and CVaR should be positive (loss amounts)
        self.assertGreater(var, 0)
        self.assertGreater(cvar, 0)
        
        # CVaR should be >= VaR (tail risk is worse)
        self.assertGreaterEqual(cvar, var)
    
    def test_simulate_portfolio_risk_with_positions(self):
        """Test portfolio risk simulation with positions"""
        if not self.risk_mgr.mc_simulator:
            self.skipTest("Monte Carlo simulator not available")
        
        positions = [
            {'symbol': 'AAPL', 'shares': 10, 'current_price': 150.0},
            {'symbol': 'MSFT', 'shares': 5, 'current_price': 200.0}
        ]
        
        results = self.risk_mgr.simulate_portfolio_risk(
            positions=positions,
            drift=0.0005,
            volatility=0.02,
            days=30
        )
        
        self.assertIsNotNone(results)
        self.assertIn('mean', results)
        self.assertIn('median', results)
        self.assertIn('var_95_loss', results)
        self.assertIn('cvar_95_loss', results)
        
        # Loss-based VaR/CVaR should be non-negative
        self.assertGreaterEqual(results['var_95_loss'], 0)
        self.assertGreaterEqual(results['cvar_95_loss'], 0)
    
    def test_estimate_drawdown_risk(self):
        """Test drawdown risk estimation"""
        if not self.risk_mgr.mc_simulator:
            self.skipTest("Monte Carlo simulator not available")
        
        dd_results = self.risk_mgr.estimate_drawdown_risk(
            expected_return=0.0005,
            volatility=0.02,
            days=252
        )
        
        self.assertIsNotNone(dd_results)
        self.assertIn('mean_max_drawdown', dd_results)
        self.assertIn('worst_drawdown_95', dd_results)
        
        # Drawdowns should be negative
        self.assertLessEqual(dd_results['mean_max_drawdown'], 0)
        self.assertLessEqual(dd_results['worst_drawdown_95'], 0)


if __name__ == '__main__':
    unittest.main()
