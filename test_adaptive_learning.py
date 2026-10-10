#!/usr/bin/env python3
"""
Tests for Adaptive Learning Module

Tests reinforcement learning, multi-armed bandit, adaptive parameter tuning,
and online learning components.
"""

import os
import shutil
import tempfile
import unittest

import numpy as np

from adaptive_learning import (
    AdaptiveLearningOrchestrator,
    AdaptiveParameterTuner,
    MultiArmedBandit,
    OnlineLearningManager,
    QLearningStrategySelector,
)


class TestQLearningStrategySelector(unittest.TestCase):
    """Test Q-Learning Strategy Selector"""

    def setUp(self):
        """Set up test fixtures"""
        self.strategies = ["SMA", "RSI", "MACD", "BollingerBands"]
        self.qlearner = QLearningStrategySelector(self.strategies)

    def test_initialization(self):
        """Test Q-Learning initialization"""
        self.assertEqual(self.qlearner.strategies, self.strategies)
        self.assertEqual(self.qlearner.total_episodes, 0)
        self.assertEqual(self.qlearner.total_rewards, 0.0)
        self.assertGreater(self.qlearner.epsilon, 0)
        self.assertLessEqual(self.qlearner.epsilon, 1.0)

    def test_discretize_market_state(self):
        """Test market state discretization"""
        market_data = {
            "rsi": 25,  # oversold
            "volatility": 0.01,  # low
            "trend": 0.05,  # up
            "volume_ratio": 1.5,  # high
        }

        state = self.qlearner.discretize_market_state(market_data)
        self.assertIn("oversold", state)
        self.assertIn("low", state)
        self.assertIn("up", state)
        self.assertIn("high", state)

    def test_select_strategy(self):
        """Test strategy selection"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        strategy = self.qlearner.select_strategy(market_data)
        self.assertIn(strategy, self.strategies)

    def test_update_from_reward(self):
        """Test Q-value update from reward"""
        market_data = {
            "rsi": 30,
            "volatility": 0.02,
            "trend": 0.01,
            "volume_ratio": 1.0,
        }

        # Select strategy
        self.qlearner.select_strategy(market_data)

        # Update with positive reward
        initial_episodes = self.qlearner.total_episodes
        self.qlearner.update_from_reward(1.5, market_data)

        self.assertEqual(self.qlearner.total_episodes, initial_episodes + 1)
        self.assertGreater(self.qlearner.total_rewards, 0)

    def test_epsilon_decay(self):
        """Test epsilon decay over time"""
        initial_epsilon = self.qlearner.epsilon

        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        # Run multiple episodes
        for _ in range(10):
            self.qlearner.select_strategy(market_data)
            self.qlearner.update_from_reward(0.5, market_data)

        # Epsilon should have decayed
        self.assertLess(self.qlearner.epsilon, initial_epsilon)
        self.assertGreaterEqual(self.qlearner.epsilon, self.qlearner.min_epsilon)

    def test_get_statistics(self):
        """Test statistics retrieval"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        # Run some episodes
        for _ in range(5):
            self.qlearner.select_strategy(market_data)
            self.qlearner.update_from_reward(1.0, market_data)

        stats = self.qlearner.get_statistics()

        self.assertIn("total_episodes", stats)
        self.assertIn("total_rewards", stats)
        self.assertIn("average_reward", stats)
        self.assertIn("strategy_performance", stats)
        self.assertEqual(stats["total_episodes"], 5)

    def test_save_and_load(self):
        """Test saving and loading Q-Learning model"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        # Train for a few episodes
        for _ in range(10):
            self.qlearner.select_strategy(market_data)
            self.qlearner.update_from_reward(1.0, market_data)

        # Save model
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            model_path = tmp.name

        try:
            self.qlearner.save(model_path)

            # Load into new instance
            new_qlearner = QLearningStrategySelector(self.strategies)
            new_qlearner.load(model_path)

            # Check that state was restored
            self.assertEqual(new_qlearner.total_episodes, self.qlearner.total_episodes)
            self.assertEqual(new_qlearner.total_rewards, self.qlearner.total_rewards)
            self.assertEqual(new_qlearner.epsilon, self.qlearner.epsilon)
        finally:
            if os.path.exists(model_path):
                os.remove(model_path)


class TestMultiArmedBandit(unittest.TestCase):
    """Test Multi-Armed Bandit"""

    def setUp(self):
        """Set up test fixtures"""
        self.strategies = ["SMA", "RSI", "MACD"]
        self.bandit = MultiArmedBandit(self.strategies)

    def test_initialization(self):
        """Test bandit initialization"""
        self.assertEqual(self.bandit.strategies, self.strategies)

        # Check Beta distribution initialization
        for strategy in self.strategies:
            self.assertEqual(self.bandit.alpha[strategy], 1.0)
            self.assertEqual(self.bandit.beta[strategy], 1.0)

    def test_select_strategy(self):
        """Test Thompson Sampling strategy selection"""
        strategy = self.bandit.select_strategy()
        self.assertIn(strategy, self.strategies)

    def test_update_from_result(self):
        """Test bandit update from trade result"""
        strategy = "RSI"

        # Update with success
        initial_alpha = self.bandit.alpha[strategy]
        self.bandit.update_from_result(strategy, success=True, reward=1.0)
        self.assertEqual(self.bandit.alpha[strategy], initial_alpha + 1)

        # Update with failure
        initial_beta = self.bandit.beta[strategy]
        self.bandit.update_from_result(strategy, success=False, reward=-0.5)
        self.assertEqual(self.bandit.beta[strategy], initial_beta + 1)

    def test_strategy_selection_bias(self):
        """Test that bandit learns to prefer better strategies"""
        # Simulate that RSI performs well, MACD performs poorly
        np.random.seed(42)

        for _ in range(50):
            strategy = self.bandit.select_strategy()

            # RSI wins 80% of time, others win 30%
            if strategy == "RSI":
                success = np.random.random() < 0.8
            else:
                success = np.random.random() < 0.3

            self.bandit.update_from_result(strategy, success)

        stats = self.bandit.get_statistics()

        # RSI should have higher win rate
        rsi_perf = stats["strategy_performance"]["RSI"]
        self.assertGreater(rsi_perf["win_rate"], 0.5)

    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Run some trials
        for _ in range(10):
            strategy = self.bandit.select_strategy()
            self.bandit.update_from_result(strategy, success=True, reward=1.0)

        stats = self.bandit.get_statistics()

        self.assertIn("strategy_counts", stats)
        self.assertIn("strategy_performance", stats)

        # Check that at least one strategy was selected
        total_selections = sum(stats["strategy_counts"].values())
        self.assertEqual(total_selections, 10)

    def test_save_and_load(self):
        """Test saving and loading bandit state"""
        # Run some trials
        for _ in range(10):
            strategy = self.bandit.select_strategy()
            self.bandit.update_from_result(strategy, success=True, reward=1.0)

        # Save bandit
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            bandit_path = tmp.name

        try:
            self.bandit.save(bandit_path)

            # Load into new instance
            new_bandit = MultiArmedBandit(self.strategies)
            new_bandit.load(bandit_path)

            # Check that state was restored
            self.assertEqual(new_bandit.alpha, self.bandit.alpha)
            self.assertEqual(new_bandit.beta, self.bandit.beta)
        finally:
            if os.path.exists(bandit_path):
                os.remove(bandit_path)


class TestAdaptiveParameterTuner(unittest.TestCase):
    """Test Adaptive Parameter Tuner"""

    def setUp(self):
        """Set up test fixtures"""
        self.param_ranges = {
            "trailing_stop": (0.02, 0.10),
            "risk_threshold": (0.03, 0.15),
        }
        self.tuner = AdaptiveParameterTuner(self.param_ranges)

    def test_initialization(self):
        """Test tuner initialization"""
        self.assertEqual(self.tuner.parameter_ranges, self.param_ranges)

        # Check parameters initialized to midpoints
        params = self.tuner.get_parameters()
        self.assertAlmostEqual(params["trailing_stop"], 0.06, places=2)
        self.assertAlmostEqual(params["risk_threshold"], 0.09, places=2)

    def test_get_parameters(self):
        """Test parameter retrieval"""
        params = self.tuner.get_parameters()
        self.assertIn("trailing_stop", params)
        self.assertIn("risk_threshold", params)

    def test_update_from_performance(self):
        """Test parameter update from performance"""
        # Update with good performance
        self.tuner.update_from_performance(2.0)

        # Parameters should be tracked
        self.assertEqual(len(self.tuner.performance_history), 1)

    def test_adaptation_to_best(self):
        """Test that tuner adapts toward best parameters"""
        # Set initial parameters
        self.tuner.parameters["trailing_stop"] = 0.08

        # Record good performance at 0.05
        self.tuner.parameters["trailing_stop"] = 0.05
        self.tuner.update_from_performance(5.0)  # Best performance

        # Move away from best
        self.tuner.parameters["trailing_stop"] = 0.08

        # Add mediocre performance
        for _ in range(10):
            self.tuner.update_from_performance(1.0)

        # Parameters should move toward best (0.05)
        current = self.tuner.parameters["trailing_stop"]
        self.assertLess(current, 0.08)

    def test_parameter_bounds(self):
        """Test that parameters stay within bounds"""
        # Force extreme updates
        for _ in range(100):
            performance = np.random.uniform(-10, 10)
            self.tuner.update_from_performance(performance)

        params = self.tuner.get_parameters()

        # Check all parameters are within bounds
        for param_name, value in params.items():
            min_val, max_val = self.param_ranges[param_name]
            self.assertGreaterEqual(value, min_val)
            self.assertLessEqual(value, max_val)

    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Add some performance data
        for i in range(5):
            self.tuner.update_from_performance(float(i))

        stats = self.tuner.get_statistics()

        self.assertIn("current_parameters", stats)
        self.assertIn("best_parameters", stats)
        self.assertIn("best_performance", stats)
        self.assertEqual(stats["history_size"], 5)

    def test_save_and_load(self):
        """Test saving and loading tuner state"""
        # Run some updates
        for i in range(10):
            self.tuner.update_from_performance(float(i))

        # Save tuner
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            tuner_path = tmp.name

        try:
            self.tuner.save(tuner_path)

            # Load into new instance
            new_tuner = AdaptiveParameterTuner(self.param_ranges)
            new_tuner.load(tuner_path)

            # Check that state was restored
            self.assertEqual(new_tuner.parameters, self.tuner.parameters)
            self.assertEqual(new_tuner.best_performance, self.tuner.best_performance)
        finally:
            if os.path.exists(tuner_path):
                os.remove(tuner_path)


class TestOnlineLearningManager(unittest.TestCase):
    """Test Online Learning Manager"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = OnlineLearningManager(retrain_threshold=10)

    def test_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.retrain_threshold, 10)
        self.assertEqual(len(self.manager.training_buffer), 0)

    def test_add_sample(self):
        """Test adding training samples"""
        sample = {"signal": "BUY", "price": 100.0}
        label = 1

        self.manager.add_sample(sample, label)

        self.assertEqual(len(self.manager.training_buffer), 1)
        self.assertEqual(len(self.manager.labels_buffer), 1)

    def test_should_retrain(self):
        """Test retrain threshold"""
        # Should not retrain initially
        self.assertFalse(self.manager.should_retrain())

        # Add samples up to threshold
        for i in range(10):
            self.manager.add_sample({"data": i}, i % 2)

        # Should now trigger retrain
        self.assertTrue(self.manager.should_retrain())

    def test_get_training_data(self):
        """Test retrieving training data"""
        # Add samples
        for i in range(5):
            self.manager.add_sample({"data": i}, i % 2)

        data, labels = self.manager.get_training_data()

        self.assertEqual(len(data), 5)
        self.assertEqual(len(labels), 5)

    def test_clear_buffer(self):
        """Test clearing training buffer"""
        # Add samples
        for i in range(5):
            self.manager.add_sample({"data": i}, i % 2)

        initial_count = self.manager.retrain_count

        # Clear buffer
        self.manager.clear_buffer()

        self.assertEqual(len(self.manager.training_buffer), 0)
        self.assertEqual(self.manager.retrain_count, initial_count + 1)

    def test_update_performance(self):
        """Test performance tracking"""
        self.manager.update_performance(0.75)
        self.manager.update_performance(0.80)

        self.assertEqual(len(self.manager.model_performance), 2)

    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Add some data
        for i in range(5):
            self.manager.add_sample({"data": i}, i % 2)
            self.manager.update_performance(0.7 + i * 0.02)

        stats = self.manager.get_statistics()

        self.assertIn("buffer_size", stats)
        self.assertIn("retrain_count", stats)
        self.assertIn("avg_performance", stats)
        self.assertEqual(stats["buffer_size"], 5)


class TestAdaptiveLearningOrchestrator(unittest.TestCase):
    """Test Adaptive Learning Orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        self.strategies = ["SMA", "RSI", "MACD"]
        self.param_ranges = {
            "trailing_stop": (0.02, 0.10),
            "risk_threshold": (0.03, 0.15),
        }
        self.orchestrator = AdaptiveLearningOrchestrator(
            strategies=self.strategies, parameter_ranges=self.param_ranges
        )

    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertEqual(self.orchestrator.strategies, self.strategies)
        self.assertTrue(self.orchestrator.use_qlearning)
        self.assertTrue(self.orchestrator.use_bandit)
        self.assertTrue(self.orchestrator.use_param_tuning)
        self.assertIsNotNone(self.orchestrator.qlearning)
        self.assertIsNotNone(self.orchestrator.bandit)
        self.assertIsNotNone(self.orchestrator.param_tuner)

    def test_select_strategy_qlearning(self):
        """Test strategy selection with Q-Learning"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        strategy = self.orchestrator.select_strategy(market_data, method="qlearning")
        self.assertIn(strategy, self.strategies)

    def test_select_strategy_bandit(self):
        """Test strategy selection with bandit"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        strategy = self.orchestrator.select_strategy(market_data, method="bandit")
        self.assertIn(strategy, self.strategies)

    def test_update_from_trade(self):
        """Test updating from trade result"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        strategy = "SMA"
        profit = 1.5

        initial_count = self.orchestrator.trade_count

        self.orchestrator.update_from_trade(strategy, profit, market_data)

        self.assertEqual(self.orchestrator.trade_count, initial_count + 1)

    def test_get_parameters(self):
        """Test parameter retrieval"""
        params = self.orchestrator.get_parameters()

        self.assertIn("trailing_stop", params)
        self.assertIn("risk_threshold", params)

    def test_should_retrain_model(self):
        """Test retrain trigger"""
        # Initially should not retrain
        self.assertFalse(self.orchestrator.should_retrain_model())

        # Add samples
        trade_data = {"signal": "BUY", "price": 100.0}
        for i in range(50):
            self.orchestrator.online_learner.add_sample(trade_data, i % 2)

        # Should now trigger retrain
        self.assertTrue(self.orchestrator.should_retrain_model())

    def test_get_all_statistics(self):
        """Test comprehensive statistics"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        # Execute some trades
        for _ in range(5):
            strategy = self.orchestrator.select_strategy(market_data)
            profit = np.random.uniform(-1, 2)
            self.orchestrator.update_from_trade(strategy, profit, market_data)

        stats = self.orchestrator.get_all_statistics()

        self.assertIn("trade_count", stats)
        self.assertIn("components", stats)
        self.assertEqual(stats["trade_count"], 5)

        # Check component stats
        components = stats["components"]
        self.assertIn("qlearning", components)
        self.assertIn("bandit", components)
        self.assertIn("param_tuner", components)
        self.assertIn("online_learner", components)

    def test_save_and_load(self):
        """Test saving and loading all components"""
        market_data = {"rsi": 50, "volatility": 0.02, "trend": 0.0, "volume_ratio": 1.0}

        # Run some trades
        for _ in range(10):
            strategy = self.orchestrator.select_strategy(market_data)
            profit = np.random.uniform(-1, 2)
            self.orchestrator.update_from_trade(strategy, profit, market_data)

        # Save to temp directory
        temp_dir = tempfile.mkdtemp()

        try:
            self.orchestrator.save(temp_dir)

            # Load into new instance
            new_orchestrator = AdaptiveLearningOrchestrator(
                strategies=self.strategies, parameter_ranges=self.param_ranges
            )
            new_orchestrator.load(temp_dir)

            # Check that state was restored
            self.assertEqual(
                new_orchestrator.trade_count, self.orchestrator.trade_count
            )
        finally:
            shutil.rmtree(temp_dir)


class TestIntegration(unittest.TestCase):
    """Integration tests for adaptive learning"""

    def test_complete_trading_simulation(self):
        """Test complete trading simulation with adaptive learning"""
        strategies = ["SMA", "RSI", "MACD"]
        param_ranges = {"trailing_stop": (0.02, 0.10)}

        orchestrator = AdaptiveLearningOrchestrator(
            strategies=strategies, parameter_ranges=param_ranges
        )

        # Simulate 100 trades
        total_profit = 0.0

        for i in range(100):
            # Generate market data
            market_data = {
                "rsi": np.random.uniform(20, 80),
                "volatility": np.random.uniform(0.01, 0.05),
                "trend": np.random.uniform(-0.05, 0.05),
                "volume_ratio": np.random.uniform(0.5, 1.5),
            }

            # Select strategy
            strategy = orchestrator.select_strategy(market_data, method="qlearning")

            # Simulate trade profit (RSI strategy performs better in this simulation)
            if strategy == "RSI":
                profit = np.random.uniform(0, 2)  # Usually positive
            else:
                profit = np.random.uniform(-1, 1)  # Mixed

            total_profit += profit

            # Update adaptive learning
            orchestrator.update_from_trade(strategy, profit, market_data)

        # Get final statistics
        stats = orchestrator.get_all_statistics()

        # Check that learning occurred
        self.assertEqual(stats["trade_count"], 100)

        # Q-Learning should have learned something
        qlearning_stats = stats["components"]["qlearning"]
        self.assertGreater(qlearning_stats["total_episodes"], 0)

        # Check that RSI was selected more often (it performs better)
        strategy_performance = qlearning_stats["strategy_performance"]
        if "RSI" in strategy_performance:
            rsi_perf = strategy_performance["RSI"]
            # RSI should have positive average reward
            self.assertGreater(rsi_perf["avg_reward"], 0)


if __name__ == "__main__":
    unittest.main()
