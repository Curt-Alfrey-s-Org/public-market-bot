#!/usr/bin/env python3
"""
Train ML Signal Filter Model
Collects historical trade data and trains the ML model to filter signals.

Usage:
    python3 train_ml_signal_filter.py [--use-synthetic] [--model-path MODEL_PATH]
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_trade_data_from_bot(bot) -> tuple:
    """
    Collect trade data from bot's trade history
    
    Returns:
        Tuple of (training_data, labels)
    """
    training_data = []
    labels = []
    
    if not bot.trade_history:
        logger.warning("No trade history available in bot")
        return training_data, labels
    
    logger.info(f"Collecting data from {len(bot.trade_history)} trades...")
    
    for trade in bot.trade_history:
        try:
            # Extract trade information
            symbol = trade.get('symbol', 'UNKNOWN')
            action = trade.get('action', 'UNKNOWN')
            price = trade.get('price', 0.0)
            is_win = trade.get('is_win', False)
            pnl = trade.get('pnl', 0.0)
            
            # Determine signal from action
            if action in ('BUY', 'SHORT'):
                signal = 'BUY' if action == 'BUY' else 'SELL'
            else:
                continue  # Skip closing trades
            
            # Get indicators if available (would need to reconstruct from historical data)
            # For now, use placeholder - in real scenario, we'd fetch historical data
            indicators = {
                'rsi': 50.0,  # Would need to calculate from historical data
                'macd': 0.0,
                'macd_signal': 0.0,
            }
            
            # Create signal data
            signal_data = {
                'symbol': symbol,
                'signal': signal,
                'price': price,
                'indicators': indicators,
                'market_conditions': {
                    'volume': trade.get('volume', 1000000),
                    'volatility': 0.02  # Would need to calculate
                }
            }
            
            training_data.append(signal_data)
            labels.append(1 if is_win else 0)
            
        except Exception as e:
            logger.warning(f"Error processing trade: {e}")
            continue
    
    logger.info(f"Collected {len(training_data)} training samples ({sum(labels)} wins, {len(labels)-sum(labels)} losses)")
    return training_data, labels


def generate_synthetic_training_data(num_samples: int = 100) -> tuple:
    """
    Generate synthetic training data for initial model training
    
    This is useful when no historical trade data is available.
    The model can be retrained later with real data.
    
    Args:
        num_samples: Number of synthetic samples to generate
        
    Returns:
        Tuple of (training_data, labels)
    """
    import random
    import numpy as np
    
    logger.info(f"Generating {num_samples} synthetic training samples...")
    
    training_data = []
    labels = []
    
    for i in range(num_samples):
        # Generate realistic signal data
        signal = random.choice(['BUY', 'SELL', 'HOLD'])
        price = random.uniform(50.0, 200.0)
        
        # Generate indicators with some correlation to success
        rsi = random.uniform(20.0, 80.0)
        macd = random.uniform(-2.0, 2.0)
        macd_signal = random.uniform(-2.0, 2.0)
        
        # Determine label based on indicators (simplified logic)
        # In real scenario, this would be based on actual trade outcomes
        is_win = False
        if signal == 'BUY':
            # BUY signals more likely to win with:
            # - RSI in oversold range (20-40) or neutral (40-60)
            # - MACD above signal (bullish)
            if (rsi < 40 or (rsi < 60 and macd > macd_signal)):
                is_win = random.random() > 0.4  # 60% win rate for good signals
            else:
                is_win = random.random() > 0.7  # 30% win rate for poor signals
        elif signal == 'SELL':
            # SELL signals more likely to win with:
            # - RSI in overbought range (60-80)
            # - MACD below signal (bearish)
            if (rsi > 60 or (rsi > 40 and macd < macd_signal)):
                is_win = random.random() > 0.4  # 60% win rate for good signals
            else:
                is_win = random.random() > 0.7  # 30% win rate for poor signals
        else:
            is_win = random.random() > 0.5  # 50% for HOLD
        
        signal_data = {
            'symbol': f'STOCK{random.randint(1, 10)}',
            'signal': signal,
            'price': price,
            'indicators': {
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'macd_histogram': macd - macd_signal,
                'macd_bullish': 1 if macd > macd_signal else 0,
            },
            'market_conditions': {
                'volume': random.uniform(500000, 5000000),
                'volatility': random.uniform(0.01, 0.05)
            }
        }
        
        training_data.append(signal_data)
        labels.append(1 if is_win else 0)
    
    wins = sum(labels)
    logger.info(f"Generated {len(training_data)} synthetic samples ({wins} wins, {len(training_data)-wins} losses)")
    return training_data, labels


def train_model(use_synthetic: bool = False, model_path: str = None):
    """
    Train the ML Signal Filter model
    
    Args:
        use_synthetic: If True, use synthetic data instead of bot trade history
        model_path: Path to save the trained model (default: ml_signal_filter_model.pkl)
    """
    try:
        # Import bot
        logger.info("Initializing TradingBot...")
        from main import TradingBot
        from ml_signal_filter import MLSignalFilter
        
        bot = TradingBot(total_capital=10000.0)
        
        # Initialize ML filter
        if not bot.ml_signal_filter:
            logger.error("ML Signal Filter not initialized in bot")
            return False
        
        ml_filter = bot.ml_signal_filter
        
        # Collect training data
        if use_synthetic or not bot.trade_history:
            logger.info("Using synthetic training data...")
            training_data, labels = generate_synthetic_training_data(num_samples=200)
        else:
            logger.info("Using bot trade history...")
            training_data, labels = collect_trade_data_from_bot(bot)
            
            # If not enough data, supplement with synthetic
            if len(training_data) < 50:
                logger.info(f"Only {len(training_data)} real samples, supplementing with synthetic data...")
                synthetic_data, synthetic_labels = generate_synthetic_training_data(num_samples=150)
                training_data.extend(synthetic_data)
                labels.extend(synthetic_labels)
        
        if len(training_data) < 20:
            logger.error(f"Insufficient training data: {len(training_data)} samples (need at least 20)")
            return False
        
        # Train model
        logger.info(f"\n{'='*60}")
        logger.info("Training ML Signal Filter Model")
        logger.info(f"{'='*60}")
        logger.info(f"Training samples: {len(training_data)}")
        logger.info(f"Wins: {sum(labels)}, Losses: {len(labels)-sum(labels)}")
        logger.info(f"Win rate: {sum(labels)/len(labels):.1%}")
        
        metrics = ml_filter.train(training_data, labels)
        
        if not metrics:
            logger.error("Training failed - no metrics returned")
            return False
        
        # Print training results
        logger.info(f"\n{'='*60}")
        logger.info("Training Results")
        logger.info(f"{'='*60}")
        logger.info(f"Accuracy: {metrics.get('accuracy', 0):.4f}")
        logger.info(f"Precision: {metrics.get('precision', 0):.4f}")
        logger.info(f"Recall: {metrics.get('recall', 0):.4f}")
        logger.info(f"F1 Score: {metrics.get('f1', 0):.4f}")
        logger.info(f"AUC-ROC: {metrics.get('auc', 0):.4f}")
        logger.info(f"CV Mean: {metrics.get('cv_mean', 0):.4f} ± {metrics.get('cv_std', 0):.4f}")
        
        # Save model
        if model_path is None:
            model_path = 'ml_signal_filter_model.pkl'
        
        ml_filter.save_model(model_path)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Model trained and saved to: {model_path}")
        logger.info(f"{'='*60}")
        
        # Save training metadata
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        metadata = {
            'model_path': model_path,
            'training_date': datetime.now().isoformat(),
            'training_samples': len(training_data),
            'wins': sum(labels),
            'losses': len(labels) - sum(labels),
            'win_rate': sum(labels) / len(labels),
            'metrics': {k: float(v) for k, v in metrics.items()},
            'use_synthetic': use_synthetic,
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Training metadata saved to: {metadata_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        return False


def load_trained_model(model_path: str = None):
    """
    Load a trained model into the bot
    
    Args:
        model_path: Path to the trained model (default: ml_signal_filter_model.pkl)
    """
    try:
        from main import TradingBot
        
        if model_path is None:
            model_path = 'ml_signal_filter_model.pkl'
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return False
        
        bot = TradingBot()
        if not bot.ml_signal_filter:
            logger.error("ML Signal Filter not initialized")
            return False
        
        bot.ml_signal_filter.load_model(model_path)
        
        logger.info(f"✅ Model loaded from: {model_path}")
        logger.info(f"   Accuracy: {bot.ml_signal_filter.metrics.get('accuracy', 0):.4f}")
        logger.info(f"   Is trained: {bot.ml_signal_filter.is_trained}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Train ML Signal Filter Model')
    parser.add_argument('--use-synthetic', action='store_true',
                       help='Use synthetic training data instead of bot trade history')
    parser.add_argument('--model-path', type=str, default='ml_signal_filter_model.pkl',
                       help='Path to save/load the trained model')
    parser.add_argument('--load-only', action='store_true',
                       help='Only load existing model, do not train')
    
    args = parser.parse_args()
    
    if args.load_only:
        success = load_trained_model(args.model_path)
    else:
        success = train_model(use_synthetic=args.use_synthetic, model_path=args.model_path)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
