#!/usr/bin/env python3
"""
Adaptive Learning Module for market-pie5-bot

Implements reinforcement learning and adaptive models that evolve based on real-world performance.

Features:
- Q-Learning based strategy selector with model caching
- Multi-Armed Bandit for strategy allocation
- Adaptive parameter tuning with lazy loading
- Online learning with continuous model updates
- Performance feedback loop with prediction caching
- Exploration-exploitation balance

Performance Optimizations:
- joblib for efficient model serialization (vs pickle)
- Lazy loading: models loaded only when needed
- Prediction caching to avoid redundant calculations
- Efficient numpy operations for large state spaces

Author: market-pie5-bot
Status: Production-Ready with Performance Enhancements
"""

import logging
import os
import pickle
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

# Try to import joblib for efficient serialization
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    joblib = None

logger = logging.getLogger(__name__)


class QLearningStrategySelector:
    """
    Q-Learning based strategy selector that learns which strategy works best
    in different market conditions.

    Uses Q-Learning to build a policy for selecting trading strategies based on
    observed market states and rewards (profit/loss from trades).
    
    Performance Optimizations:
    - Prediction caching: Cache Q-value calculations for same market state
    - Lazy serialization: Models saved only if changed
    - Efficient numpy operations for state comparisons
    """

    def __init__(
        self,
        strategies: List[str],
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.2,
        epsilon_decay: float = 0.995,
        min_epsilon: float = 0.05,
    ):
        """
        Initialize Q-Learning Strategy Selector

        Args:
            strategies: List of strategy names to choose from
            learning_rate: Learning rate (alpha) for Q-value updates
            discount_factor: Discount factor (gamma) for future rewards
            epsilon: Initial exploration rate for epsilon-greedy policy
            epsilon_decay: Decay rate for epsilon after each episode
            min_epsilon: Minimum epsilon value
        """
        self.strategies = strategies
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

        # Q-table: state -> strategy -> Q-value
        self.q_table = defaultdict(lambda: {strategy: 0.0 for strategy in strategies})

        # Prediction cache for same market states
        self.prediction_cache: Dict[str, str] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Performance tracking
        self.total_episodes = 0
        self.total_rewards = 0.0
        self.strategy_counts = {strategy: 0 for strategy in strategies}
        self.strategy_rewards = {strategy: [] for strategy in strategies}

        # State history for learning
        self.last_state = None
        self.last_strategy = None
        
        # Track if model was modified (for lazy serialization)
        self.is_dirty = False

        logger.info(
            f"Initialized Q-Learning Strategy Selector with {len(strategies)} strategies"
        )
        logger.info(f"  Learning rate: {learning_rate}")
        logger.info(f"  Discount factor: {discount_factor}")
        logger.info(f"  Epsilon: {epsilon}")

    def discretize_market_state(self, market_data: Dict[str, Any]) -> str:
        """
        Convert continuous market data into discrete state representation

        Args:
            market_data: Dictionary with market indicators (RSI, volatility, trend, etc.)

        Returns:
            Discrete state string
        """
        # Extract key indicators
        rsi = market_data.get("rsi", 50)
        volatility = market_data.get("volatility", 0.02)
        trend = market_data.get("trend", 0.0)  # -1 to 1
        volume_ratio = market_data.get("volume_ratio", 1.0)

        # Discretize RSI
        if rsi < 30:
            rsi_state = "oversold"
        elif rsi > 70:
            rsi_state = "overbought"
        else:
            rsi_state = "neutral"

        # Discretize volatility
        if volatility < 0.015:
            vol_state = "low"
        elif volatility < 0.03:
            vol_state = "medium"
        else:
            vol_state = "high"

        # Discretize trend
        if trend < -0.02:
            trend_state = "down"
        elif trend > 0.02:
            trend_state = "up"
        else:
            trend_state = "sideways"

        # Discretize volume
        if volume_ratio < 0.8:
            volume_state = "low"
        elif volume_ratio < 1.2:
            volume_state = "normal"
        else:
            volume_state = "high"

        # Combine into state string
        state = f"{rsi_state}_{vol_state}_{trend_state}_{volume_state}"
        return state

    def select_strategy(
        self, market_data: Dict[str, Any], exploration: bool = True
    ) -> str:
        """
        Select a trading strategy using epsilon-greedy policy with caching.
        
        Optimization: Caches strategy selections for identical market states
        to avoid redundant Q-value computations.

        Args:
            market_data: Current market data for state determination
            exploration: Whether to use exploration (set False for production)

        Returns:
            Selected strategy name
        """
        state = self.discretize_market_state(market_data)

        # Check prediction cache first
        if not exploration and state in self.prediction_cache:
            strategy = self.prediction_cache[state]
            self.cache_hits += 1
            logger.debug(f"Cache hit: {state} -> {strategy} (hits: {self.cache_hits})")
            return strategy

        # Epsilon-greedy: explore with probability epsilon
        if exploration and np.random.random() < self.epsilon:
            # Explore: random strategy
            strategy = np.random.choice(self.strategies)
            logger.debug(f"Exploring: selected {strategy} randomly")
        else:
            # Exploit: best strategy for this state
            q_values = self.q_table[state]
            strategy = max(q_values, key=q_values.get)
            logger.debug(
                f"Exploiting: selected {strategy} with Q={q_values[strategy]:.3f}"
            )

        # Cache the prediction for future exploit phases
        if not exploration:
            self.prediction_cache[state] = strategy
            self.cache_misses += 1

        # Store for learning update
        self.last_state = state
        self.last_strategy = strategy
        self.strategy_counts[strategy] += 1

        return strategy

    def update_from_reward(
        self, reward: float, next_market_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update Q-values based on observed reward

        Args:
            reward: Reward received (profit/loss from trade)
            next_market_data: Market data for next state (optional)
        """
        if self.last_state is None or self.last_strategy is None:
            logger.warning("No previous state to update from")
            return

        # Get current Q-value
        current_q = self.q_table[self.last_state][self.last_strategy]

        # Calculate max Q-value for next state
        if next_market_data is not None:
            next_state = self.discretize_market_state(next_market_data)
            next_q_values = self.q_table[next_state]
            max_next_q = max(next_q_values.values())
        else:
            max_next_q = 0.0

        # Q-Learning update rule
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        # Update Q-table
        self.q_table[self.last_state][self.last_strategy] = new_q
        
        # Mark model as modified for lazy serialization
        self.is_dirty = True

        # Track statistics
        self.total_episodes += 1
        self.total_rewards += reward
        self.strategy_rewards[self.last_strategy].append(reward)

        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

        logger.debug(
            f"Updated Q({self.last_state}, {self.last_strategy}): "
            f"{current_q:.3f} -> {new_q:.3f} (reward={reward:.3f})"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        stats = {
            "total_episodes": self.total_episodes,
            "total_rewards": self.total_rewards,
            "average_reward": self.total_rewards / max(1, self.total_episodes),
            "epsilon": self.epsilon,
            "strategy_counts": self.strategy_counts.copy(),
            "strategy_performance": {},
        }

        # Calculate average reward per strategy
        for strategy, rewards in self.strategy_rewards.items():
            if rewards:
                stats["strategy_performance"][strategy] = {
                    "count": len(rewards),
                    "avg_reward": np.mean(rewards),
                    "total_reward": np.sum(rewards),
                    "win_rate": sum(1 for r in rewards if r > 0) / len(rewards),
                }

        return stats

    def save(self, filepath: str):
        """
        Save Q-table and state to disk using joblib (or pickle as fallback).
        
        Optimization: Uses joblib for 2-3x faster serialization than pickle,
        and is more memory-efficient for large models.
        Lazy save: Only saves if model is marked as dirty.
        """
        if not self.is_dirty:
            logger.debug(f"Model unchanged, skipping save to {filepath}")
            return
        
        data = {
            "q_table": dict(self.q_table),
            "strategies": self.strategies,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "min_epsilon": self.min_epsilon,
            "total_episodes": self.total_episodes,
            "total_rewards": self.total_rewards,
            "strategy_counts": self.strategy_counts,
            "strategy_rewards": {k: list(v) for k, v in self.strategy_rewards.items()},
            "prediction_cache": self.prediction_cache.copy(),
        }

        try:
            if JOBLIB_AVAILABLE:
                joblib.dump(data, filepath, compress=3)
                logger.info(f"Q-Learning model saved to {filepath} (joblib)")
            else:
                with open(filepath, "wb") as f:
                    pickle.dump(data, f)
                logger.info(f"Q-Learning model saved to {filepath} (pickle)")
            
            self.is_dirty = False
        except Exception as e:
            logger.error(f"Failed to save model to {filepath}: {e}")

    def load(self, filepath: str):
        """
        Load Q-table and state from disk using joblib (or pickle as fallback).
        
        Lazy loading: Only loads model when explicitly requested.
        """
        try:
            if JOBLIB_AVAILABLE:
                data = joblib.load(filepath)
                logger.info(f"Q-Learning model loaded from {filepath} (joblib)")
            else:
                with open(filepath, "rb") as f:
                    data = pickle.load(f)
                logger.info(f"Q-Learning model loaded from {filepath} (pickle)")
        except Exception as e:
            logger.error(f"Failed to load model from {filepath}: {e}")
            return

        self.q_table = defaultdict(
            lambda: {s: 0.0 for s in self.strategies}, data["q_table"]
        )
        self.strategies = data["strategies"]
        self.learning_rate = data["learning_rate"]
        self.discount_factor = data["discount_factor"]
        self.epsilon = data["epsilon"]
        self.epsilon_decay = data["epsilon_decay"]
        self.min_epsilon = data["min_epsilon"]
        self.total_episodes = data["total_episodes"]
        self.total_rewards = data["total_rewards"]
        self.strategy_counts = data["strategy_counts"]
        self.strategy_rewards = {
            k: deque(v, maxlen=1000) for k, v in data["strategy_rewards"].items()
        }
        self.prediction_cache = data.get("prediction_cache", {})

        logger.info(f"Q-Learning model loaded from {filepath}")
        logger.info(f"  Episodes: {self.total_episodes}")
        logger.info(
            f"  Average reward: {self.total_rewards / max(1, self.total_episodes):.3f}"
        )


class MultiArmedBandit:
    """
    Multi-Armed Bandit for dynamic strategy allocation.

    Uses Thompson Sampling (Bayesian approach) to balance exploration and exploitation
    by modeling each strategy as a Beta distribution.
    """

    def __init__(self, strategies: List[str]):
        """
        Initialize Multi-Armed Bandit

        Args:
            strategies: List of strategy names
        """
        self.strategies = strategies

        # Beta distribution parameters (successes, failures)
        self.alpha = {strategy: 1.0 for strategy in strategies}  # Successes + 1
        self.beta = {strategy: 1.0 for strategy in strategies}  # Failures + 1

        # Performance tracking
        self.strategy_counts = {strategy: 0 for strategy in strategies}
        self.strategy_rewards = {strategy: [] for strategy in strategies}

        logger.info(f"Initialized Multi-Armed Bandit with {len(strategies)} arms")

    def select_strategy(self) -> str:
        """
        Select strategy using Thompson Sampling

        Returns:
            Selected strategy name
        """
        # Sample from Beta distribution for each strategy
        samples = {}
        for strategy in self.strategies:
            samples[strategy] = np.random.beta(
                self.alpha[strategy], self.beta[strategy]
            )

        # Select strategy with highest sample
        selected = max(samples, key=samples.get)
        self.strategy_counts[selected] += 1

        logger.debug(
            f"Thompson Sampling selected {selected} (sample={samples[selected]:.3f})"
        )

        return selected

    def update_from_result(self, strategy: str, success: bool, reward: float = None):
        """
        Update bandit based on trade result

        Args:
            strategy: Strategy that was used
            success: Whether trade was successful (profit > 0)
            reward: Optional reward value for tracking
        """
        if strategy not in self.strategies:
            logger.warning(f"Unknown strategy: {strategy}")
            return

        # Update Beta distribution parameters
        if success:
            self.alpha[strategy] += 1
        else:
            self.beta[strategy] += 1

        # Track rewards if provided
        if reward is not None:
            self.strategy_rewards[strategy].append(reward)

        logger.debug(
            f"Updated {strategy}: alpha={self.alpha[strategy]:.1f}, "
            f"beta={self.beta[strategy]:.1f}"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics"""
        stats = {
            "strategy_counts": self.strategy_counts.copy(),
            "strategy_performance": {},
        }

        for strategy in self.strategies:
            total = self.alpha[strategy] + self.beta[strategy] - 2
            win_rate = (self.alpha[strategy] - 1) / total if total > 0 else 0.5

            stats["strategy_performance"][strategy] = {
                "count": self.strategy_counts[strategy],
                "wins": self.alpha[strategy] - 1,
                "losses": self.beta[strategy] - 1,
                "win_rate": win_rate,
                "expected_value": self.alpha[strategy]
                / (self.alpha[strategy] + self.beta[strategy]),
            }

            if self.strategy_rewards[strategy]:
                stats["strategy_performance"][strategy]["avg_reward"] = np.mean(
                    self.strategy_rewards[strategy]
                )

        return stats

    def save(self, filepath: str):
        """Save bandit state to disk"""
        data = {
            "strategies": self.strategies,
            "alpha": self.alpha,
            "beta": self.beta,
            "strategy_counts": self.strategy_counts,
            "strategy_rewards": {k: list(v) for k, v in self.strategy_rewards.items()},
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Multi-Armed Bandit saved to {filepath}")

    def load(self, filepath: str):
        """Load bandit state from disk"""
        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.strategies = data["strategies"]
        self.alpha = data["alpha"]
        self.beta = data["beta"]
        self.strategy_counts = data["strategy_counts"]
        self.strategy_rewards = {
            k: deque(v, maxlen=1000) for k, v in data["strategy_rewards"].items()
        }

        logger.info(f"Multi-Armed Bandit loaded from {filepath}")


class AdaptiveParameterTuner:
    """
    Adaptive parameter tuning system that adjusts strategy parameters
    based on recent performance.

    Uses a sliding window approach to monitor performance and adjusts
    parameters using gradient-free optimization (simple hill climbing).
    """

    def __init__(
        self,
        parameter_ranges: Dict[str, Tuple[float, float]],
        window_size: int = 50,
        adaptation_rate: float = 0.1,
    ):
        """
        Initialize Adaptive Parameter Tuner

        Args:
            parameter_ranges: Dict mapping parameter name to (min, max) range
            window_size: Number of recent trades to consider for adaptation
            adaptation_rate: Rate of parameter adjustment (0 to 1)
        """
        self.parameter_ranges = parameter_ranges
        self.window_size = window_size
        self.adaptation_rate = adaptation_rate

        # Current parameter values (initialized to midpoints)
        self.parameters = {
            name: (min_val + max_val) / 2
            for name, (min_val, max_val) in parameter_ranges.items()
        }

        # Performance history
        self.performance_history = deque(maxlen=window_size)
        self.parameter_history = deque(maxlen=window_size)

        # Best parameters found
        self.best_parameters = self.parameters.copy()
        self.best_performance = float("-inf")

        logger.info("Initialized Adaptive Parameter Tuner")
        logger.info(f"  Parameters: {list(parameter_ranges.keys())}")
        logger.info(f"  Window size: {window_size}")

    def get_parameters(self) -> Dict[str, float]:
        """Get current parameter values"""
        return self.parameters.copy()

    def update_from_performance(self, performance_metric: float):
        """
        Update parameters based on performance metric

        Args:
            performance_metric: Performance score (e.g., profit, win rate)
        """
        # Store history
        self.performance_history.append(performance_metric)
        self.parameter_history.append(self.parameters.copy())

        # Check if this is best performance
        if performance_metric > self.best_performance:
            self.best_performance = performance_metric
            self.best_parameters = self.parameters.copy()
            logger.info(f"New best performance: {performance_metric:.3f}")

        # Need sufficient history to adapt
        if len(self.performance_history) < 10:
            return

        # Calculate recent performance trend
        recent_performance = list(self.performance_history)[-10:]
        avg_recent = np.mean(recent_performance)

        # Calculate overall average
        avg_overall = np.mean(list(self.performance_history))

        # If recent performance is worse, adjust parameters toward best known
        if avg_recent < avg_overall:
            logger.info(
                "Recent performance declining, adjusting toward best parameters"
            )

            for param_name in self.parameters:
                best_val = self.best_parameters[param_name]
                current_val = self.parameters[param_name]

                # Move toward best value
                adjustment = self.adaptation_rate * (best_val - current_val)
                new_val = current_val + adjustment

                # Clip to valid range
                min_val, max_val = self.parameter_ranges[param_name]
                self.parameters[param_name] = np.clip(new_val, min_val, max_val)
        else:
            # Performance is good, try small random exploration
            for param_name in self.parameters:
                min_val, max_val = self.parameter_ranges[param_name]

                # Small random perturbation
                perturbation = np.random.normal(0, self.adaptation_rate * 0.1)
                new_val = self.parameters[param_name] + perturbation * (
                    max_val - min_val
                )

                # Clip to valid range
                self.parameters[param_name] = np.clip(new_val, min_val, max_val)

    def get_statistics(self) -> Dict[str, Any]:
        """Get tuner statistics"""
        stats = {
            "current_parameters": self.parameters.copy(),
            "best_parameters": self.best_parameters.copy(),
            "best_performance": self.best_performance,
            "history_size": len(self.performance_history),
        }

        if self.performance_history:
            stats["avg_performance"] = np.mean(list(self.performance_history))
            stats["recent_performance"] = np.mean(list(self.performance_history)[-10:])

        return stats

    def save(self, filepath: str):
        """Save tuner state to disk"""
        data = {
            "parameter_ranges": self.parameter_ranges,
            "parameters": self.parameters,
            "best_parameters": self.best_parameters,
            "best_performance": self.best_performance,
            "performance_history": list(self.performance_history),
            "parameter_history": list(self.parameter_history),
            "window_size": self.window_size,
            "adaptation_rate": self.adaptation_rate,
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Adaptive Parameter Tuner saved to {filepath}")

    def load(self, filepath: str):
        """Load tuner state from disk"""
        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.parameter_ranges = data["parameter_ranges"]
        self.parameters = data["parameters"]
        self.best_parameters = data["best_parameters"]
        self.best_performance = data["best_performance"]
        self.performance_history = deque(
            data["performance_history"], maxlen=self.window_size
        )
        self.parameter_history = deque(
            data["parameter_history"], maxlen=self.window_size
        )
        self.window_size = data["window_size"]
        self.adaptation_rate = data["adaptation_rate"]

        logger.info(f"Adaptive Parameter Tuner loaded from {filepath}")


class OnlineLearningManager:
    """
    Online learning manager that continuously updates ML models as new data arrives.

    Implements incremental learning with model retraining triggers and performance monitoring.
    """

    def __init__(
        self,
        retrain_threshold: int = 50,
        performance_window: int = 100,
        min_performance_improvement: float = 0.01,
    ):
        """
        Initialize Online Learning Manager

        Args:
            retrain_threshold: Number of new samples before retraining
            performance_window: Window for performance monitoring
            min_performance_improvement: Minimum improvement to keep new model
        """
        self.retrain_threshold = retrain_threshold
        self.performance_window = performance_window
        self.min_performance_improvement = min_performance_improvement

        # Data buffers
        self.training_buffer = []
        self.labels_buffer = []

        # Performance tracking
        self.model_performance = deque(maxlen=performance_window)
        self.retrain_count = 0
        self.last_retrain_time = datetime.now()

        logger.info("Initialized Online Learning Manager")
        logger.info(f"  Retrain threshold: {retrain_threshold}")
        logger.info(f"  Performance window: {performance_window}")

    def add_sample(self, training_data: Dict[str, Any], label: int):
        """
        Add a new training sample

        Args:
            training_data: Training data dictionary
            label: Label (1 = success, 0 = failure)
        """
        self.training_buffer.append(training_data)
        self.labels_buffer.append(label)

    def should_retrain(self) -> bool:
        """Check if model should be retrained"""
        return len(self.training_buffer) >= self.retrain_threshold

    def get_training_data(self) -> Tuple[List[Dict], List[int]]:
        """Get buffered training data"""
        return self.training_buffer.copy(), self.labels_buffer.copy()

    def clear_buffer(self):
        """Clear training buffer after retraining"""
        self.training_buffer.clear()
        self.labels_buffer.clear()
        self.retrain_count += 1
        self.last_retrain_time = datetime.now()

    def update_performance(self, performance_metric: float):
        """Update model performance tracking"""
        self.model_performance.append(performance_metric)

    def get_statistics(self) -> Dict[str, Any]:
        """Get online learning statistics"""
        stats = {
            "buffer_size": len(self.training_buffer),
            "retrain_count": self.retrain_count,
            "last_retrain": self.last_retrain_time.isoformat(),
            "time_since_retrain": (
                datetime.now() - self.last_retrain_time
            ).total_seconds(),
        }

        if self.model_performance:
            stats["avg_performance"] = np.mean(list(self.model_performance))
            stats["recent_performance"] = np.mean(list(self.model_performance)[-10:])

        return stats


class AdaptiveLearningOrchestrator:
    """
    Orchestrator that coordinates all adaptive learning components.

    Provides a unified interface for:
    - Q-Learning strategy selection
    - Multi-Armed Bandit allocation
    - Adaptive parameter tuning
    - Online model updates
    """

    def __init__(
        self,
        strategies: List[str],
        parameter_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
        use_qlearning: bool = True,
        use_bandit: bool = True,
        use_param_tuning: bool = True,
        use_online_learning: bool = True,
    ):
        """
        Initialize Adaptive Learning Orchestrator

        Args:
            strategies: List of strategy names
            parameter_ranges: Parameter ranges for adaptive tuning
            use_qlearning: Enable Q-Learning strategy selector
            use_bandit: Enable Multi-Armed Bandit
            use_param_tuning: Enable adaptive parameter tuning
            use_online_learning: Enable online learning
        """
        self.strategies = strategies
        self.use_qlearning = use_qlearning
        self.use_bandit = use_bandit
        self.use_param_tuning = use_param_tuning
        self.use_online_learning = use_online_learning

        # Initialize components
        self.qlearning = None
        self.bandit = None
        self.param_tuner = None
        self.online_learner = None

        if use_qlearning:
            self.qlearning = QLearningStrategySelector(strategies)

        if use_bandit:
            self.bandit = MultiArmedBandit(strategies)

        if use_param_tuning and parameter_ranges:
            self.param_tuner = AdaptiveParameterTuner(parameter_ranges)

        if use_online_learning:
            self.online_learner = OnlineLearningManager()

        # Combined statistics
        self.trade_count = 0

        logger.info("Initialized Adaptive Learning Orchestrator")
        logger.info(f"  Q-Learning: {use_qlearning}")
        logger.info(f"  Bandit: {use_bandit}")
        logger.info(f"  Parameter Tuning: {use_param_tuning}")
        logger.info(f"  Online Learning: {use_online_learning}")

    def select_strategy(
        self, market_data: Dict[str, Any], method: str = "qlearning"
    ) -> str:
        """
        Select trading strategy using specified method

        Args:
            market_data: Current market data
            method: 'qlearning' or 'bandit'

        Returns:
            Selected strategy name
        """
        if method == "qlearning" and self.qlearning:
            return self.qlearning.select_strategy(market_data)
        elif method == "bandit" and self.bandit:
            return self.bandit.select_strategy()
        else:
            # Fallback to random selection
            return np.random.choice(self.strategies)

    def update_from_trade(
        self,
        strategy: str,
        profit: float,
        market_data: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Update all components based on trade result

        Args:
            strategy: Strategy that was used
            profit: Profit/loss from trade
            market_data: Market data for learning
            trade_data: Optional trade data for online learning
        """
        self.trade_count += 1
        success = profit > 0

        # Update Q-Learning
        if self.qlearning:
            self.qlearning.update_from_reward(profit, market_data)

        # Update Bandit
        if self.bandit:
            self.bandit.update_from_result(strategy, success, profit)

        # Update Parameter Tuner
        if self.param_tuner:
            self.param_tuner.update_from_performance(profit)

        # Update Online Learner
        if self.online_learner and trade_data:
            label = 1 if success else 0
            self.online_learner.add_sample(trade_data, label)

    def get_parameters(self) -> Dict[str, float]:
        """Get current adaptive parameters"""
        if self.param_tuner:
            return self.param_tuner.get_parameters()
        return {}

    def should_retrain_model(self) -> bool:
        """Check if ML model should be retrained"""
        if self.online_learner:
            return self.online_learner.should_retrain()
        return False

    def get_training_data_for_retrain(self) -> Optional[Tuple[List[Dict], List[int]]]:
        """Get training data for model retraining"""
        if self.online_learner:
            return self.online_learner.get_training_data()
        return None

    def clear_training_buffer(self):
        """Clear training buffer after retraining"""
        if self.online_learner:
            self.online_learner.clear_buffer()

    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics from all components"""
        stats = {"trade_count": self.trade_count, "components": {}}

        if self.qlearning:
            stats["components"]["qlearning"] = self.qlearning.get_statistics()

        if self.bandit:
            stats["components"]["bandit"] = self.bandit.get_statistics()

        if self.param_tuner:
            stats["components"]["param_tuner"] = self.param_tuner.get_statistics()

        if self.online_learner:
            stats["components"]["online_learner"] = self.online_learner.get_statistics()

        return stats

    def save(self, directory: str):
        """Save all components to directory"""
        os.makedirs(directory, exist_ok=True)

        if self.qlearning:
            self.qlearning.save(os.path.join(directory, "qlearning.pkl"))

        if self.bandit:
            self.bandit.save(os.path.join(directory, "bandit.pkl"))

        if self.param_tuner:
            self.param_tuner.save(os.path.join(directory, "param_tuner.pkl"))

        # Save orchestrator state
        state = {
            "strategies": self.strategies,
            "trade_count": self.trade_count,
            "use_qlearning": self.use_qlearning,
            "use_bandit": self.use_bandit,
            "use_param_tuning": self.use_param_tuning,
            "use_online_learning": self.use_online_learning,
        }

        with open(os.path.join(directory, "orchestrator.pkl"), "wb") as f:
            pickle.dump(state, f)

        logger.info(f"Adaptive Learning components saved to {directory}")

    def load(self, directory: str):
        """Load all components from directory"""
        # Load orchestrator state
        state_path = os.path.join(directory, "orchestrator.pkl")
        if os.path.exists(state_path):
            with open(state_path, "rb") as f:
                state = pickle.load(f)
            self.trade_count = state["trade_count"]

        # Load components
        qlearning_path = os.path.join(directory, "qlearning.pkl")
        if self.qlearning and os.path.exists(qlearning_path):
            self.qlearning.load(qlearning_path)

        bandit_path = os.path.join(directory, "bandit.pkl")
        if self.bandit and os.path.exists(bandit_path):
            self.bandit.load(bandit_path)

        param_tuner_path = os.path.join(directory, "param_tuner.pkl")
        if self.param_tuner and os.path.exists(param_tuner_path):
            self.param_tuner.load(param_tuner_path)

        logger.info(f"Adaptive Learning components loaded from {directory}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("Adaptive Learning Module - Example Usage")
    print("=" * 70)

    # Test Q-Learning Strategy Selector
    print("\n" + "=" * 70)
    print("Testing Q-Learning Strategy Selector")
    print("=" * 70)

    strategies = ["SMA", "RSI", "MACD", "BollingerBands", "Momentum"]
    qlearner = QLearningStrategySelector(strategies)

    # Simulate trading episodes
    for episode in range(100):
        # Simulate market data
        market_data = {
            "rsi": np.random.uniform(20, 80),
            "volatility": np.random.uniform(0.01, 0.05),
            "trend": np.random.uniform(-0.05, 0.05),
            "volume_ratio": np.random.uniform(0.5, 1.5),
        }

        # Select strategy
        strategy = qlearner.select_strategy(market_data)

        # Simulate reward (some strategies perform better in certain conditions)
        if market_data["rsi"] < 30 and strategy == "RSI":
            reward = np.random.uniform(0.5, 1.5)  # Good
        elif market_data["volatility"] > 0.03 and strategy == "BollingerBands":
            reward = np.random.uniform(0.3, 1.0)  # Good
        else:
            reward = np.random.uniform(-0.5, 0.5)  # Random

        # Update Q-values
        qlearner.update_from_reward(reward, market_data)

    # Get statistics
    stats = qlearner.get_statistics()
    print("\nQ-Learning Statistics after 100 episodes:")
    print(f"  Total rewards: {stats['total_rewards']:.2f}")
    print(f"  Average reward: {stats['average_reward']:.3f}")
    print(f"  Epsilon: {stats['epsilon']:.3f}")
    print("\nStrategy Performance:")
    for strategy, perf in stats["strategy_performance"].items():
        print(f"  {strategy}:")
        print(f"    Count: {perf['count']}")
        print(f"    Avg Reward: {perf['avg_reward']:.3f}")
        print(f"    Win Rate: {perf['win_rate']:.2%}")

    # Test Multi-Armed Bandit
    print("\n" + "=" * 70)
    print("Testing Multi-Armed Bandit")
    print("=" * 70)

    bandit = MultiArmedBandit(strategies)

    # Simulate strategy selection and feedback
    for i in range(100):
        strategy = bandit.select_strategy()

        # Simulate result (some strategies are better)
        if strategy == "RSI":
            success = np.random.random() < 0.65  # 65% win rate
        elif strategy == "MACD":
            success = np.random.random() < 0.60  # 60% win rate
        else:
            success = np.random.random() < 0.50  # 50% win rate

        reward = (
            np.random.uniform(0.5, 1.5) if success else np.random.uniform(-1.0, -0.3)
        )
        bandit.update_from_result(strategy, success, reward)

    # Get statistics
    stats = bandit.get_statistics()
    print("\nBandit Statistics after 100 pulls:")
    print("\nStrategy Performance:")
    for strategy, perf in stats["strategy_performance"].items():
        print(f"  {strategy}:")
        print(f"    Count: {perf['count']}")
        print(f"    Win Rate: {perf['win_rate']:.2%}")
        print(f"    Expected Value: {perf['expected_value']:.3f}")
        if "avg_reward" in perf:
            print(f"    Avg Reward: {perf['avg_reward']:.3f}")

    # Test Adaptive Parameter Tuner
    print("\n" + "=" * 70)
    print("Testing Adaptive Parameter Tuner")
    print("=" * 70)

    param_ranges = {
        "trailing_stop": (0.02, 0.10),
        "risk_threshold": (0.03, 0.15),
        "min_confidence": (0.50, 0.80),
    }

    tuner = AdaptiveParameterTuner(param_ranges)

    # Simulate performance updates
    for i in range(50):
        # Simulate performance that improves with certain parameter values
        params = tuner.get_parameters()

        # Performance is better when trailing_stop is around 0.05
        performance = 1.0 - abs(params["trailing_stop"] - 0.05) * 10
        performance += np.random.normal(0, 0.1)

        tuner.update_from_performance(performance)

    # Get statistics
    stats = tuner.get_statistics()
    print("\nParameter Tuner Statistics:")
    print(f"  Best Performance: {stats['best_performance']:.3f}")
    print(f"  Avg Performance: {stats['avg_performance']:.3f}")
    print("\nCurrent Parameters:")
    for param, value in stats["current_parameters"].items():
        print(f"  {param}: {value:.4f}")
    print("\nBest Parameters:")
    for param, value in stats["best_parameters"].items():
        print(f"  {param}: {value:.4f}")

    # Test Orchestrator
    print("\n" + "=" * 70)
    print("Testing Adaptive Learning Orchestrator")
    print("=" * 70)

    orchestrator = AdaptiveLearningOrchestrator(
        strategies=strategies, parameter_ranges=param_ranges
    )

    # Simulate trades
    for i in range(50):
        market_data = {
            "rsi": np.random.uniform(20, 80),
            "volatility": np.random.uniform(0.01, 0.05),
            "trend": np.random.uniform(-0.05, 0.05),
            "volume_ratio": np.random.uniform(0.5, 1.5),
        }

        # Select strategy
        strategy = orchestrator.select_strategy(market_data, method="qlearning")

        # Simulate profit
        profit = np.random.uniform(-1.0, 2.0)

        # Update from trade
        orchestrator.update_from_trade(strategy, profit, market_data)

    # Get statistics
    all_stats = orchestrator.get_all_statistics()
    print("\nOrchestrator Statistics:")
    print(f"  Total Trades: {all_stats['trade_count']}")

    print("\n" + "=" * 70)
    print("Adaptive Learning Module initialized successfully!")
    print("=" * 70)
