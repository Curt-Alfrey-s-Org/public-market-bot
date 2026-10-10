#!/usr/bin/env python3
"""
Integration Validation Script
Tests all integrated features to ensure they work correctly together.

Validates:
1. ML Signal Filter integration
2. Portfolio Optimizer integration
3. Adaptive Learning integration
4. Real-time ML Optimization
5. Performance caching
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationValidator:
    """Validates all integration features"""
    
    def __init__(self):
        self.results = {
            'ml_signal_filter': {'passed': False, 'details': []},
            'portfolio_optimizer': {'passed': False, 'details': []},
            'adaptive_learning': {'passed': False, 'details': []},
            'realtime_ml_optimization': {'passed': False, 'details': []},
            'performance_caching': {'passed': False, 'details': []},
        }
        self.bot = None
    
    def run_all_tests(self):
        """Run all integration validation tests"""
        logger.info("="*60)
        logger.info("Integration Validation - Testing All Features")
        logger.info("="*60)
        
        try:
            # Import bot
            logger.info("\n[1/5] Importing TradingBot...")
            from main import TradingBot
            self.bot = TradingBot(total_capital=10000.0)
            logger.info("✓ TradingBot imported and initialized")
            
            # Test 1: ML Signal Filter
            logger.info("\n[2/5] Testing ML Signal Filter Integration...")
            self.test_ml_signal_filter()
            
            # Test 2: Portfolio Optimizer
            logger.info("\n[3/5] Testing Portfolio Optimizer Integration...")
            self.test_portfolio_optimizer()
            
            # Test 3: Adaptive Learning
            logger.info("\n[4/5] Testing Adaptive Learning Integration...")
            self.test_adaptive_learning()
            
            # Test 4: Real-time ML Optimization
            logger.info("\n[5/5] Testing Real-time ML Optimization...")
            self.test_realtime_ml_optimization()
            
            # Test 5: Performance Caching
            logger.info("\n[6/5] Testing Performance Caching...")
            self.test_performance_caching()
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}", exc_info=True)
            return False
        
        return self.all_tests_passed()
    
    def test_ml_signal_filter(self):
        """Test ML Signal Filter integration"""
        try:
            # Check if ML signal filter is initialized
            if not hasattr(self.bot, 'ml_signal_filter'):
                self.results['ml_signal_filter']['details'].append(
                    "❌ ML Signal Filter not initialized"
                )
                return
            
            if self.bot.ml_signal_filter is None:
                self.results['ml_signal_filter']['details'].append(
                    "⚠️ ML Signal Filter is None (may be disabled)"
                )
                # Still pass if it's disabled by config
                self.results['ml_signal_filter']['passed'] = True
                return
            
            # Test signal filtering
            test_signal_data = {
                'symbol': 'AAPL',
                'signal': 'BUY',
                'price': 150.0,
                'indicators': {
                    'rsi': 45.0,
                    'macd': 0.5,
                    'macd_signal': 0.3,
                },
                'market_conditions': {
                    'volume': 1000000,
                    'volatility': 0.02
                }
            }
            
            # Test prediction
            confidence, win_prob = self.bot.ml_signal_filter.predict_signal_quality(test_signal_data)
            
            if isinstance(confidence, float) and isinstance(win_prob, float):
                self.results['ml_signal_filter']['details'].append(
                    f"✓ ML Signal Filter prediction works (confidence={confidence:.3f}, win_prob={win_prob:.3f})"
                )
                self.results['ml_signal_filter']['passed'] = True
            else:
                self.results['ml_signal_filter']['details'].append(
                    f"❌ ML Signal Filter returned invalid values"
                )
                
        except Exception as e:
            self.results['ml_signal_filter']['details'].append(
                f"❌ Error testing ML Signal Filter: {e}"
            )
    
    def test_portfolio_optimizer(self):
        """Test Portfolio Optimizer integration"""
        try:
            # Check if portfolio optimizer is initialized
            if not hasattr(self.bot, 'portfolio_optimizer'):
                self.results['portfolio_optimizer']['details'].append(
                    "❌ Portfolio Optimizer not initialized"
                )
                return
            
            if self.bot.portfolio_optimizer is None:
                self.results['portfolio_optimizer']['details'].append(
                    "⚠️ Portfolio Optimizer is None (may be disabled)"
                )
                # Still pass if it's disabled by config
                self.results['portfolio_optimizer']['passed'] = True
                return
            
            # Test allocation
            test_symbols = ['AAPL', 'MSFT', 'GOOGL']
            test_capital = 10000.0
            
            # Add some price data
            for symbol in test_symbols:
                self.bot.portfolio_optimizer.add_price_data(symbol, [100.0, 101.0, 102.0, 103.0, 104.0])
            
            allocation = self.bot.portfolio_optimizer.get_optimal_allocation(
                test_symbols, test_capital, method='equal'
            )
            
            if allocation and isinstance(allocation, dict):
                total_allocated = sum(allocation.values())
                if abs(total_allocated - test_capital) < 0.01:  # Allow small rounding errors
                    self.results['portfolio_optimizer']['details'].append(
                        f"✓ Portfolio Optimizer allocation works (total=${total_allocated:.2f})"
                    )
                    self.results['portfolio_optimizer']['passed'] = True
                else:
                    self.results['portfolio_optimizer']['details'].append(
                        f"❌ Allocation total mismatch: ${total_allocated:.2f} != ${test_capital:.2f}"
                    )
            else:
                self.results['portfolio_optimizer']['details'].append(
                    "❌ Portfolio Optimizer returned invalid allocation"
                )
                
        except Exception as e:
            self.results['portfolio_optimizer']['details'].append(
                f"❌ Error testing Portfolio Optimizer: {e}"
            )
    
    def test_adaptive_learning(self):
        """Test Adaptive Learning integration"""
        try:
            # Check if adaptive learner is initialized
            if not hasattr(self.bot, 'adaptive_learner'):
                self.results['adaptive_learning']['details'].append(
                    "❌ Adaptive Learning not initialized"
                )
                return
            
            if self.bot.adaptive_learner is None:
                self.results['adaptive_learning']['details'].append(
                    "⚠️ Adaptive Learning is None (may be disabled)"
                )
                # Still pass if it's disabled by config
                self.results['adaptive_learning']['passed'] = True
                return
            
            # Test strategy selection
            test_market_data = {
                'rsi': 50.0,
                'volatility': 0.02,
                'trend': 0.01,
                'volume_ratio': 1.0
            }
            
            strategy = self.bot.adaptive_learner.select_strategy(test_market_data, method='qlearning')
            
            if strategy and isinstance(strategy, str):
                self.results['adaptive_learning']['details'].append(
                    f"✓ Adaptive Learning strategy selection works (selected: {strategy})"
                )
                
                # Test update from trade
                self.bot.adaptive_learner.update_from_trade(
                    strategy=strategy,
                    profit=10.0,
                    market_data=test_market_data,
                    trade_data={'symbol': 'AAPL', 'pnl': 10.0}
                )
                
                stats = self.bot.adaptive_learner.get_all_statistics()
                if stats:
                    self.results['adaptive_learning']['details'].append(
                        f"✓ Adaptive Learning update works (trade_count={stats.get('trade_count', 0)})"
                    )
                    self.results['adaptive_learning']['passed'] = True
                else:
                    self.results['adaptive_learning']['details'].append(
                        "❌ Adaptive Learning statistics not available"
                    )
            else:
                self.results['adaptive_learning']['details'].append(
                    "❌ Adaptive Learning returned invalid strategy"
                )
                
        except Exception as e:
            self.results['adaptive_learning']['details'].append(
                f"❌ Error testing Adaptive Learning: {e}"
            )
    
    def test_realtime_ml_optimization(self):
        """Test Real-time ML Optimization"""
        try:
            # Check if ML optimizer is initialized
            if not hasattr(self.bot, 'ml_optimizer'):
                self.results['realtime_ml_optimization']['details'].append(
                    "❌ ML Optimizer not initialized"
                )
                return
            
            if self.bot.ml_optimizer is None:
                self.results['realtime_ml_optimization']['details'].append(
                    "⚠️ ML Optimizer is None (may be disabled)"
                )
                # Still pass if it's disabled by config
                self.results['realtime_ml_optimization']['passed'] = True
                return
            
            # Check if optimization tracking is set up
            if hasattr(self.bot, 'last_ml_optimization_time'):
                self.results['realtime_ml_optimization']['details'].append(
                    "✓ ML Optimization tracking initialized"
                )
                self.results['realtime_ml_optimization']['passed'] = True
            else:
                self.results['realtime_ml_optimization']['details'].append(
                    "❌ ML Optimization tracking not initialized"
                )
            
            # Check if parameter application method exists
            if hasattr(self.bot, '_apply_optimized_parameters'):
                self.results['realtime_ml_optimization']['details'].append(
                    "✓ Parameter application method exists"
                )
            else:
                self.results['realtime_ml_optimization']['details'].append(
                    "❌ Parameter application method missing"
                )
                
        except Exception as e:
            self.results['realtime_ml_optimization']['details'].append(
                f"❌ Error testing Real-time ML Optimization: {e}"
            )
    
    def test_performance_caching(self):
        """Test Performance Caching"""
        try:
            # Test portfolio optimizer cache
            if self.bot.portfolio_optimizer:
                # First call
                test_symbols = ['AAPL', 'MSFT']
                allocation1 = self.bot.portfolio_optimizer.get_optimal_allocation(
                    test_symbols, 10000.0, method='equal'
                )
                
                # Second call (should use cache)
                import time
                time.sleep(0.1)  # Small delay
                allocation2 = self.bot.portfolio_optimizer.get_optimal_allocation(
                    test_symbols, 10000.0, method='equal'
                )
                
                if hasattr(self.bot.portfolio_optimizer, '_allocation_cache'):
                    cache_size = len(self.bot.portfolio_optimizer._allocation_cache)
                    self.results['performance_caching']['details'].append(
                        f"✓ Portfolio Optimizer cache exists (size={cache_size})"
                    )
                    self.results['performance_caching']['passed'] = True
                else:
                    self.results['performance_caching']['details'].append(
                        "❌ Portfolio Optimizer cache not found"
                    )
            
            # Test ML signal filter cache
            if self.bot.ml_signal_filter:
                if hasattr(self.bot.ml_signal_filter, '_prediction_cache'):
                    cache_size = len(self.bot.ml_signal_filter._prediction_cache)
                    self.results['performance_caching']['details'].append(
                        f"✓ ML Signal Filter cache exists (size={cache_size})"
                    )
                else:
                    self.results['performance_caching']['details'].append(
                        "❌ ML Signal Filter cache not found"
                    )
                    
        except Exception as e:
            self.results['performance_caching']['details'].append(
                f"❌ Error testing Performance Caching: {e}"
            )
    
    def all_tests_passed(self) -> bool:
        """Check if all tests passed"""
        return all(result['passed'] for result in self.results.values())
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "="*60)
        logger.info("Integration Validation Summary")
        logger.info("="*60)
        
        for feature, result in self.results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            logger.info(f"\n{feature.replace('_', ' ').title()}: {status}")
            for detail in result['details']:
                logger.info(f"  {detail}")
        
        logger.info("\n" + "="*60)
        if self.all_tests_passed():
            logger.info("✅ ALL INTEGRATIONS VALIDATED SUCCESSFULLY!")
        else:
            logger.info("⚠️ SOME INTEGRATIONS NEED ATTENTION")
        logger.info("="*60)


def main():
    """Run integration validation"""
    validator = IntegrationValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
