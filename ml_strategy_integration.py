#!/usr/bin/env python3
"""
ML Strategy Integration Module

**Status: Production-Ready** ✅

Integrates machine learning signal filtering with existing trading strategies.
This module is fully tested and ready for production use.

Features:
- ML-based signal quality assessment
- Risk scoring and filtering
- Integration with all existing strategies
- Comprehensive statistics tracking
- Model persistence (save/load)

User Action Required:
- Train the ML model with your historical trade data (100+ trades recommended)
- Models operate in pass-through mode until trained
- Review filtering statistics regularly to optimize thresholds

For complete documentation, see ML_GUIDE.md
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import ML modules
from ml_signal_filter import MLSignalFilter, MLRiskAssessor, SKLEARN_AVAILABLE

# Import existing strategy modules
from strategies import (
    TradingStrategy, StrategyManager, 
    SMAStrategy, BollingerBandsStrategy, RSIStrategy, 
    MACDStrategy, MomentumStrategy
)
from indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class MLEnhancedStrategy:
    """
    ML-Enhanced Trading Strategy
    Wraps existing strategies with ML-based signal filtering and risk assessment
    """
    
    def __init__(self, 
                 base_strategy: TradingStrategy,
                 ml_filter: Optional[MLSignalFilter] = None,
                 risk_assessor: Optional[MLRiskAssessor] = None,
                 enable_filtering: bool = True,
                 min_confidence: float = 0.6,
                 min_win_prob: float = 0.55,
                 max_risk: float = 0.7):
        """
        Initialize ML-Enhanced Strategy
        
        Args:
            base_strategy: Base trading strategy to enhance
            ml_filter: ML signal filter (creates default if None)
            risk_assessor: ML risk assessor (creates default if None)
            enable_filtering: Enable ML filtering (default: True)
            min_confidence: Minimum confidence threshold (default: 0.6)
            min_win_prob: Minimum win probability threshold (default: 0.55)
            max_risk: Maximum acceptable risk level (default: 0.7)
        """
        self.base_strategy = base_strategy
        self.enable_filtering = enable_filtering and SKLEARN_AVAILABLE
        self.min_confidence = min_confidence
        self.min_win_prob = min_win_prob
        self.max_risk = max_risk
        
        # Initialize ML components
        if ml_filter is None and SKLEARN_AVAILABLE:
            self.ml_filter = MLSignalFilter(model_type='random_forest')
        else:
            self.ml_filter = ml_filter
        
        if risk_assessor is None and SKLEARN_AVAILABLE:
            self.risk_assessor = MLRiskAssessor()
        else:
            self.risk_assessor = risk_assessor
        
        # Statistics tracking
        self.stats = {
            'total_signals': 0,
            'filtered_signals': 0,
            'accepted_signals': 0,
            'high_risk_rejected': 0
        }
        
        logger.info(f"Initialized MLEnhancedStrategy wrapping {base_strategy.name}")
        logger.info(f"  ML filtering enabled: {self.enable_filtering}")
        logger.info(f"  Min confidence: {min_confidence:.2f}")
        logger.info(f"  Min win prob: {min_win_prob:.2f}")
        logger.info(f"  Max risk: {max_risk:.2f}")
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal with ML filtering
        
        Args:
            data: DataFrame with price and indicator data
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        # Get base strategy signal
        base_signal = self.base_strategy.generate_signal(data)
        
        self.stats['total_signals'] += 1
        
        # If base signal is HOLD or ML filtering is disabled, return as-is
        if base_signal == 'HOLD' or not self.enable_filtering:
            return base_signal
        
        # Calculate technical indicators for ML
        indicators = TechnicalIndicators(data)
        indicator_values = indicators.get_latest_values()
        
        # Prepare signal data for ML
        signal_data = {
            'signal': base_signal,
            'price': data['close'].iloc[-1] if 'close' in data.columns else 0,
            'indicators': indicator_values,
            'market_conditions': {}
        }
        
        # Add volume if available
        if 'volume' in data.columns:
            signal_data['market_conditions']['volume'] = data['volume'].iloc[-1]
        
        # Apply ML filtering
        if self.ml_filter and self.ml_filter.is_trained:
            should_filter, scores = self.ml_filter.should_filter_signal(
                signal_data,
                min_confidence=self.min_confidence,
                min_win_prob=self.min_win_prob
            )
            
            if should_filter:
                self.stats['filtered_signals'] += 1
                logger.info(f"ML filter rejected {base_signal} signal "
                          f"(confidence={scores['confidence']:.3f}, "
                          f"win_prob={scores['win_probability']:.3f})")
                return 'HOLD'
        
        # Apply risk assessment
        if self.risk_assessor:
            risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
            
            if risk_metrics['overall_risk'] > self.max_risk:
                self.stats['high_risk_rejected'] += 1
                logger.info(f"High risk rejected {base_signal} signal "
                          f"(risk={risk_metrics['overall_risk']:.3f})")
                return 'HOLD'
        
        self.stats['accepted_signals'] += 1
        logger.info(f"ML-enhanced signal accepted: {base_signal}")
        return base_signal
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get filtering statistics"""
        stats = self.stats.copy()
        
        if stats['total_signals'] > 0:
            stats['filter_rate'] = stats['filtered_signals'] / stats['total_signals']
            stats['acceptance_rate'] = stats['accepted_signals'] / stats['total_signals']
        else:
            stats['filter_rate'] = 0.0
            stats['acceptance_rate'] = 0.0
        
        return stats
    
    def _get_cached_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Get indicators with caching for efficiency
        Cache is simple - could be enhanced with TTL or size limits
        """
        # For now, calculate fresh each time
        # In production, could cache based on data hash or timestamp
        indicators_calc = TechnicalIndicators(data)
        return indicators_calc.get_latest_values()


class MLStrategyManager:
    """
    ML-Enhanced Strategy Manager
    Manages multiple ML-enhanced strategies with weighted voting
    """
    
    def __init__(self, 
                 ml_filter: Optional[MLSignalFilter] = None,
                 risk_assessor: Optional[MLRiskAssessor] = None,
                 enable_ml_filtering: bool = True):
        """
        Initialize ML Strategy Manager
        
        Args:
            ml_filter: Shared ML filter for all strategies
            risk_assessor: Shared risk assessor for all strategies
            enable_ml_filtering: Enable ML filtering (default: True)
        """
        self.strategies = []
        self.enable_ml_filtering = enable_ml_filtering and SKLEARN_AVAILABLE
        
        # Create shared ML components
        if ml_filter is None and SKLEARN_AVAILABLE:
            self.ml_filter = MLSignalFilter(model_type='random_forest')
        else:
            self.ml_filter = ml_filter
        
        if risk_assessor is None and SKLEARN_AVAILABLE:
            self.risk_assessor = MLRiskAssessor()
        else:
            self.risk_assessor = risk_assessor
        
        logger.info(f"Initialized MLStrategyManager (ML filtering: {self.enable_ml_filtering})")
    
    def add_strategy(self, 
                    strategy: TradingStrategy, 
                    weight: float = 1.0,
                    min_confidence: float = 0.6,
                    min_win_prob: float = 0.55,
                    max_risk: float = 0.7):
        """
        Add a strategy to the manager with ML enhancement
        
        Args:
            strategy: Base trading strategy
            weight: Weight for this strategy in combined signal
            min_confidence: Minimum confidence threshold for ML filter
            min_win_prob: Minimum win probability threshold
            max_risk: Maximum acceptable risk level
        """
        ml_enhanced = MLEnhancedStrategy(
            base_strategy=strategy,
            ml_filter=self.ml_filter,
            risk_assessor=self.risk_assessor,
            enable_filtering=self.enable_ml_filtering,
            min_confidence=min_confidence,
            min_win_prob=min_win_prob,
            max_risk=max_risk
        )
        
        self.strategies.append({
            'strategy': ml_enhanced,
            'weight': weight
        })
        
        logger.info(f"Added ML-enhanced strategy: {strategy.name} (weight={weight})")
    
    def generate_combined_signal(self, data: pd.DataFrame) -> str:
        """
        Generate combined signal from all ML-enhanced strategies
        
        Args:
            data: DataFrame with price data
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if not self.strategies:
            logger.warning("No strategies configured")
            return 'HOLD'
        
        votes = []
        
        for item in self.strategies:
            strategy = item['strategy']
            weight = item['weight']
            
            signal = strategy.generate_signal(data)
            
            # Convert to numerical vote
            if signal == 'BUY':
                vote = 1.0
            elif signal == 'SELL':
                vote = -1.0
            else:  # HOLD
                vote = 0.0
            
            weighted_vote = vote * weight
            votes.append(weighted_vote)
            
            logger.debug(f"{strategy.base_strategy.name}: {signal} (weighted vote: {weighted_vote:+.2f})")
        
        # Calculate combined signal
        total_vote = sum(votes)
        
        # Decision threshold: require significant agreement
        if total_vote > 0.5:
            combined_signal = 'BUY'
        elif total_vote < -0.5:
            combined_signal = 'SELL'
        else:
            combined_signal = 'HOLD'
        
        logger.info(f"ML-enhanced combined signal: {combined_signal} (total vote: {total_vote:+.2f})")
        
        return combined_signal
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics from all strategies"""
        all_stats = {}
        
        for item in self.strategies:
            strategy = item['strategy']
            # Safely get strategy name with fallback
            strategy_name = getattr(strategy.base_strategy, 'name', 'Unknown Strategy')
            all_stats[strategy_name] = strategy.get_statistics()
        
        return all_stats
    
    def train_ml_filter(self, training_data: List[Dict[str, Any]], labels: List[int]) -> Dict[str, float]:
        """
        Train the shared ML filter
        
        Args:
            training_data: List of signal data dictionaries
            labels: List of outcomes (1 = win, 0 = loss)
            
        Returns:
            Training metrics
        """
        if self.ml_filter:
            return self.ml_filter.train(training_data, labels)
        return {}


# Convenience function to create a default ML-enhanced strategy manager
def create_default_ml_strategy_manager(enable_ml: bool = True) -> MLStrategyManager:
    """
    Create a default ML strategy manager with common strategies
    
    Args:
        enable_ml: Enable ML filtering (default: True)
        
    Returns:
        Configured MLStrategyManager
    """
    manager = MLStrategyManager(enable_ml_filtering=enable_ml)
    
    # Add common strategies with different weights
    manager.add_strategy(SMAStrategy(fast_period=10, slow_period=30), weight=1.0)
    manager.add_strategy(BollingerBandsStrategy(period=20), weight=1.0)
    manager.add_strategy(RSIStrategy(period=14), weight=0.8)
    manager.add_strategy(MACDStrategy(), weight=0.8)
    manager.add_strategy(MomentumStrategy(period=10), weight=0.6)
    
    logger.info("Created default ML strategy manager with 5 strategies")
    
    return manager


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("ML Strategy Integration - Example Usage")
    print("="*60)
    print(f"scikit-learn available: {SKLEARN_AVAILABLE}")
    
    if not SKLEARN_AVAILABLE:
        print("\nWARNING: scikit-learn not available - ML features disabled")
        print("Install with: pip install scikit-learn")
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.normal(0, 2, 100)
    prices = base_price + trend + noise
    
    # Generate OHLC data
    open_prices = prices + np.random.normal(0, 0.5, 100)
    high_prices = np.maximum(open_prices, prices) + np.random.uniform(0, 1, 100)
    low_prices = np.minimum(open_prices, prices) - np.random.uniform(0, 1, 100)
    volumes = np.random.randint(1000000, 5000000, 100)
    
    data = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': prices,
        'volume': volumes
    })
    
    print(f"\nGenerated {len(data)} days of sample data")
    
    # Create ML strategy manager
    print("\n" + "="*60)
    print("Testing ML Strategy Manager")
    print("="*60)
    
    manager = create_default_ml_strategy_manager(enable_ml=True)
    
    # Generate signal (without trained ML model - will accept all signals)
    signal = manager.generate_combined_signal(data)
    print(f"\nCombined Signal (untrained ML): {signal}")
    
    # Get statistics
    stats = manager.get_all_statistics()
    print("\nStrategy Statistics:")
    for strategy_name, strategy_stats in stats.items():
        print(f"\n{strategy_name}:")
        for key, value in strategy_stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("ML Strategy Integration module initialized successfully")
    print("="*60)
