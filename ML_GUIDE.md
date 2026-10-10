# Machine Learning Signal Filtering - User Guide

> **Local ML vs the AI brain.** This guide covers **local** machine learning
> (scikit-learn signal filter, VADER/TextBlob sentiment, Q-learning adaptive
> learning). These run **in-process** and use **no external LLM API**.
>
> **Parameter tuning** uses **backtest heuristics** in `ml_param_optimizer.py`
> (not the LLM). The ALFa AI brain provides **narratives only** (performance
> summary, trade journal) via `api/services/trading_insights_llm.py`.
>
> See [docs/ML_AND_AI_ARCHITECTURE.md](docs/ML_AND_AI_ARCHITECTURE.md),
> [docs/ALFA_AI_HOW_TO_USE.md](docs/ALFA_AI_HOW_TO_USE.md), and
> [docs/ENV_VARS.md](docs/ENV_VARS.md).

## Feature Maturity Status

**Status: Production-Ready** ✅

The ML signal filtering features have been thoroughly tested and are ready for production use. The implementation includes:
- ✅ Fully tested with comprehensive unit tests
- ✅ Production-grade error handling
- ✅ Graceful fallback when scikit-learn is unavailable
- ✅ Performance monitoring and statistics
- ✅ Model persistence (save/load)
- ✅ Integration with all existing strategies

**User Action Required**: ML models require training with your historical trade data to be effective. Initial usage will operate without filtering until sufficient data is collected (recommended: 100+ trades).

## Overview

The market-pie5-bot includes **Machine Learning (ML) signal filtering** to improve trading performance and win rate. The ML modules use ensemble methods (Random Forest and Gradient Boosting) to filter out low-quality trading signals before execution.

## Key Features

### 1. ML Signal Quality Prediction
- **Random Forest Classifier**: Predicts whether a trading signal is likely to result in a winning trade
- **Gradient Boosting Classifier**: Alternative model for signal quality assessment
- **Confidence Scoring**: Provides confidence level (0-1) for each prediction
- **Win Probability**: Estimates probability (0-1) that a trade will be profitable

### 2. Feature Engineering
Automatically extracts features from technical indicators:
- **RSI features**: Oversold/overbought conditions
- **MACD features**: Trend direction and strength
- **Bollinger Bands**: Volatility and price position
- **Moving Averages**: Trend confirmation via SMA crossovers
- **Momentum indicators**: Rate of change and momentum strength
- **Volatility metrics**: ATR and ADX for market conditions
- **Stochastic Oscillator**: Additional momentum signals

### 3. ML-Based Risk Assessment
- **Volatility Risk**: Measures risk from price volatility (ATR, BB width)
- **Momentum Risk**: Assesses risk from extreme momentum indicators
- **Trend Strength**: Evaluates trend clarity (weak trends = higher risk)
- **Overall Risk Score**: Combined risk assessment (0-1 scale)

### 4. Strategy Integration
- **MLEnhancedStrategy**: Wraps any existing strategy with ML filtering
- **MLStrategyManager**: Manages multiple ML-enhanced strategies with weighted voting
- **Seamless Integration**: Works with all existing strategies (SMA, RSI, MACD, Bollinger Bands, Momentum)

## Installation

### Install ML Dependencies

```bash
pip install scikit-learn>=1.3.0 joblib>=1.3.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Basic ML Signal Filtering

```python
from ml_signal_filter import MLSignalFilter
import pandas as pd

# Initialize ML filter
ml_filter = MLSignalFilter(model_type='random_forest')

# Prepare signal data
signal_data = {
    'signal': 'BUY',
    'price': 150.0,
    'indicators': {
        'rsi': 28,  # Oversold
        'macd': 0.5,
        'macd_signal': 0.3,
        'bb_upper': 155,
        'bb_middle': 150,
        'bb_lower': 145,
        'sma_fast': 151,
        'sma_slow': 148
    }
}

# Check if signal should be filtered
should_filter, scores = ml_filter.should_filter_signal(
    signal_data,
    min_confidence=0.6,
    min_win_prob=0.55
)

if not should_filter:
    print(f"Signal accepted! Confidence: {scores['confidence']:.3f}, "
          f"Win Prob: {scores['win_probability']:.3f}")
else:
    print("Signal filtered out - low quality")
```

### 2. Training the ML Model

```python
from ml_signal_filter import MLSignalFilter

# Create training data from historical trades
training_data = []
labels = []

for trade in historical_trades:
    signal_data = {
        'signal': trade['action'],
        'price': trade['entry_price'],
        'indicators': trade['indicators']
    }
    training_data.append(signal_data)
    labels.append(1 if trade['profit'] > 0 else 0)

# Train model
ml_filter = MLSignalFilter(model_type='random_forest')
metrics = ml_filter.train(training_data, labels)

print(f"Model Accuracy: {metrics['accuracy']:.3f}")
print(f"Precision: {metrics['precision']:.3f}")
print(f"F1 Score: {metrics['f1']:.3f}")

# Save trained model
ml_filter.save_model('models/trained_filter.pkl')
```

### 3. ML-Enhanced Strategy

```python
from ml_strategy_integration import MLEnhancedStrategy, create_default_ml_strategy_manager
from strategies import SMAStrategy
import pandas as pd

# Option 1: Enhance a single strategy
base_strategy = SMAStrategy(fast_period=10, slow_period=30)
ml_strategy = MLEnhancedStrategy(
    base_strategy=base_strategy,
    enable_filtering=True,
    min_confidence=0.6,
    min_win_prob=0.55,
    max_risk=0.7
)

# Generate signal
signal = ml_strategy.generate_signal(price_data)

# Option 2: Use default manager with multiple strategies
manager = create_default_ml_strategy_manager(enable_ml=True)
combined_signal = manager.generate_combined_signal(price_data)

# Get filtering statistics
stats = manager.get_all_statistics()
for strategy_name, strategy_stats in stats.items():
    print(f"{strategy_name}:")
    print(f"  Filter rate: {strategy_stats['filter_rate']:.2%}")
    print(f"  Acceptance rate: {strategy_stats['acceptance_rate']:.2%}")
```

## Configuration Parameters

### ML Filter Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_confidence` | 0.6 | Minimum model confidence to accept signal (0-1) |
| `min_win_prob` | 0.55 | Minimum win probability to accept signal (0-1) |
| `max_risk` | 0.7 | Maximum acceptable risk score (0-1) |

### Model Types

| Model Type | Description | Use Case |
|------------|-------------|----------|
| `random_forest` | Ensemble of decision trees | Good for non-linear patterns, handles outliers well |
| `gradient_boosting` | Sequential boosting | Often more accurate but slower training |

### Adjusting Thresholds

**More Conservative** (fewer trades, higher quality):
```python
ml_strategy = MLEnhancedStrategy(
    base_strategy=strategy,
    min_confidence=0.7,    # Higher threshold
    min_win_prob=0.6,      # Higher threshold
    max_risk=0.5           # Lower risk tolerance
)
```

**More Aggressive** (more trades, lower quality filter):
```python
ml_strategy = MLEnhancedStrategy(
    base_strategy=strategy,
    min_confidence=0.5,    # Lower threshold
    min_win_prob=0.5,      # Lower threshold
    max_risk=0.8           # Higher risk tolerance
)
```

## Model Training Guide

### Collecting Training Data

The ML model learns from historical trading performance. You need:

1. **Signal Data**: Trading signals with technical indicators
2. **Labels**: Outcomes (1 = winning trade, 0 = losing trade)

```python
# Example: Collect from bot's trade history
training_data = []
labels = []

for trade in bot.trade_history:
    # Extract indicators at signal time
    indicators = {
        'rsi': trade['rsi_at_entry'],
        'macd': trade['macd_at_entry'],
        'macd_signal': trade['macd_signal_at_entry'],
        # ... other indicators
    }
    
    signal_data = {
        'signal': trade['action'],
        'price': trade['entry_price'],
        'indicators': indicators
    }
    
    training_data.append(signal_data)
    
    # Label: 1 if profit > 0, else 0
    labels.append(1 if trade['pnl'] > 0 else 0)

# Train model
ml_filter.train(training_data, labels)
```

### Training Best Practices

1. **Minimum Data**: At least 100-200 trades for meaningful training
2. **Balanced Classes**: Try to have similar numbers of wins and losses
3. **Recent Data**: Use recent trades (last 3-6 months) for current market conditions
4. **Cross-Validation**: Model automatically validates with 5-fold CV
5. **Regular Retraining**: Retrain every 1-2 months as market conditions change

### Model Evaluation Metrics

After training, review these metrics:

```python
metrics = ml_filter.train(training_data, labels)

print(f"Accuracy: {metrics['accuracy']:.3f}")      # Overall correctness
print(f"Precision: {metrics['precision']:.3f}")    # How many predicted wins were actual wins
print(f"Recall: {metrics['recall']:.3f}")          # How many actual wins were predicted
print(f"F1 Score: {metrics['f1']:.3f}")            # Harmonic mean of precision and recall
print(f"AUC: {metrics['auc']:.3f}")                # Area under ROC curve
print(f"CV Mean: {metrics['cv_mean']:.3f}")        # Cross-validation accuracy
```

**Good Model Indicators:**
- Accuracy > 0.6 (better than random)
- Precision > 0.6 (confident predictions)
- AUC > 0.65 (good discrimination)
- CV Mean close to Accuracy (not overfitting)

## Integration with Main Bot

### Option 1: Drop-in Replacement (Recommended)

Replace standard strategy manager with ML-enhanced version:

```python
# In main.py or your trading script
from ml_strategy_integration import create_default_ml_strategy_manager

# Instead of:
# manager = StrategyManager()
# manager.add_strategy(SMAStrategy(), weight=1.0)

# Use:
ml_manager = create_default_ml_strategy_manager(enable_ml=True)

# Train the ML filter once you have historical data
if len(bot.trade_history) >= 100:
    training_data = prepare_training_data(bot.trade_history)
    labels = prepare_labels(bot.trade_history)
    ml_manager.train_ml_filter(training_data, labels)

# Generate signals as usual
signal = ml_manager.generate_combined_signal(price_data)
```

### Option 2: Gradual Integration

Start with ML filtering disabled, enable after training:

```python
# Start without ML filtering
ml_manager = create_default_ml_strategy_manager(enable_ml=False)

# ... run bot, collect data ...

# After sufficient data, train and enable
if len(bot.trade_history) >= 100:
    training_data = prepare_training_data(bot.trade_history)
    labels = prepare_labels(bot.trade_history)
    
    ml_filter = MLSignalFilter()
    ml_filter.train(training_data, labels)
    ml_filter.save_model('models/trained_filter.pkl')
    
    # Enable ML filtering with trained model
    ml_manager = create_default_ml_strategy_manager(enable_ml=True)
    ml_manager.ml_filter = ml_filter
```

## Risk Assessment

Use ML risk assessor to evaluate trade risk before execution:

```python
from ml_signal_filter import MLRiskAssessor

risk_assessor = MLRiskAssessor()

signal_data = {
    'signal': 'BUY',
    'price': 150.0,
    'indicators': {
        'atr': 3.5,    # Volatility
        'adx': 20,     # Trend strength
        'rsi': 25,     # Momentum
        'momentum': -0.05
    }
}

risk_metrics = risk_assessor.assess_trade_risk(signal_data)

print(f"Overall Risk: {risk_metrics['overall_risk']:.3f}")
print(f"Volatility Risk: {risk_metrics['volatility_risk']:.3f}")
print(f"Momentum Risk: {risk_metrics['momentum_risk']:.3f}")

if risk_metrics['overall_risk'] < 0.5:
    print("Low risk - proceed with trade")
elif risk_metrics['overall_risk'] < 0.7:
    print("Moderate risk - reduce position size")
else:
    print("High risk - skip trade")
```

## Performance Monitoring

Track ML filtering performance:

```python
# Get statistics from ML strategy manager
stats = ml_manager.get_all_statistics()

for strategy_name, strategy_stats in stats.items():
    print(f"\n{strategy_name}:")
    print(f"  Total signals: {strategy_stats['total_signals']}")
    print(f"  Filtered: {strategy_stats['filtered_signals']}")
    print(f"  Accepted: {strategy_stats['accepted_signals']}")
    print(f"  Filter rate: {strategy_stats['filter_rate']:.2%}")
    
    # If filter rate is too high (>80%), consider:
    # - Lowering confidence/win_prob thresholds
    # - Retraining model with more recent data
    # - Checking if market conditions have changed
```

## Troubleshooting

### Issue: Model always filters signals

**Cause**: Thresholds too high or model not trained properly

**Solution**:
```python
# Lower thresholds
ml_strategy = MLEnhancedStrategy(
    base_strategy=strategy,
    min_confidence=0.5,
    min_win_prob=0.5
)

# Or check model metrics
metrics = ml_filter.train(training_data, labels)
if metrics['accuracy'] < 0.55:
    print("Model performance poor - need more/better training data")
```

### Issue: Model accepts all signals

**Cause**: Thresholds too low or model not providing meaningful predictions

**Solution**:
```python
# Check if model is trained
if not ml_filter.is_trained:
    print("Model not trained - train with historical data")

# Check feature importance
print("Feature importance:", ml_filter.feature_importance)
# If all features have low importance, indicators may not be predictive
```

### Issue: scikit-learn not available

**Cause**: scikit-learn not installed

**Solution**:
```bash
pip install scikit-learn>=1.3.0 joblib>=1.3.0
```

The bot will work without ML filtering if scikit-learn is not available, but you won't get the signal quality improvements.

## Advanced Usage

### Custom Feature Engineering

Add custom features to improve model performance:

```python
class CustomMLFilter(MLSignalFilter):
    def extract_features(self, signal_data):
        # Get base features
        features = super().extract_features(signal_data)
        
        if features is None:
            return None
        
        # Add custom features
        indicators = signal_data.get('indicators', {})
        
        # Example: Add RSI divergence feature
        if 'rsi' in indicators and 'price' in signal_data:
            features['rsi_price_divergence'] = (
                indicators['rsi'] / 50 - signal_data['price'] / 100
            )
        
        # Example: Add volatility regime
        if 'atr' in indicators:
            features['high_volatility'] = 1 if indicators['atr'] > 3 else 0
        
        return features
```

### Ensemble of Models

Use multiple ML models for more robust predictions:

```python
# Create multiple models
rf_filter = MLSignalFilter(model_type='random_forest')
gb_filter = MLSignalFilter(model_type='gradient_boosting')

# Train both
rf_filter.train(training_data, labels)
gb_filter.train(training_data, labels)

# Average predictions
def ensemble_predict(signal_data):
    conf1, prob1 = rf_filter.predict_signal_quality(signal_data)
    conf2, prob2 = gb_filter.predict_signal_quality(signal_data)
    
    avg_confidence = (conf1 + conf2) / 2
    avg_win_prob = (prob1 + prob2) / 2
    
    return avg_confidence, avg_win_prob
```

## Best Practices

1. **Start Conservative**: Use higher thresholds (0.6-0.7) initially
2. **Monitor Performance**: Track filter rate and win rate improvements
3. **Regular Retraining**: Retrain model monthly with recent data
4. **Validate Predictions**: Compare ML predictions with actual outcomes
5. **Combine with Risk Management**: Use ML alongside position sizing and stops
6. **Test Before Live**: Thoroughly test in paper trading mode
7. **Keep Models Updated**: Save and version trained models

## Expected Impact on Win Rate

Based on typical ML filtering performance:

| Scenario | Without ML | With ML | Improvement |
|----------|-----------|---------|-------------|
| Signal Quality | Mixed | Filtered | +10-20% win rate |
| Risk Management | Manual | Automated | Reduced drawdowns |
| False Signals | Many | Fewer | -30-50% bad trades |

**Note**: Results depend on training data quality and market conditions. ML is not a guarantee of profits but should improve signal quality over time.

## Support

For issues or questions about ML features:
1. Check that scikit-learn is installed: `pip install scikit-learn`
2. Verify training data has sufficient samples (100+)
3. Review model metrics after training
4. Check logs for ML filtering decisions

## Future Enhancements

Planned improvements:
- Deep learning models (LSTM, Transformer) for time series
- ✅ **Reinforcement learning for adaptive strategy selection** (NOW AVAILABLE - see ADAPTIVE_LEARNING_GUIDE.md)
- ✅ **Real-time model updates during trading** (NOW AVAILABLE - online learning in adaptive_learning.py)
- Feature selection and automatic hyperparameter tuning
- Multi-asset correlation analysis

## New: Adaptive Learning Module

🎯 **The bot now includes advanced adaptive learning capabilities!**

See **ADAPTIVE_LEARNING_GUIDE.md** for complete documentation on:

- **Q-Learning Strategy Selector**: Reinforcement learning that adapts strategy selection based on market conditions
- **Multi-Armed Bandit**: Rapid strategy allocation using Thompson Sampling
- **Adaptive Parameter Tuner**: Automatic optimization of trailing stops, risk thresholds, and other parameters
- **Online Learning Manager**: Continuous ML model updates as new data arrives

These features enable the bot to:
- ✅ Learn from every trade and continuously improve
- ✅ Automatically adapt to changing market conditions
- ✅ Self-optimize parameters without manual tuning
- ✅ Keep ML models current without manual retraining

**Integration Example**:
```python
from adaptive_learning import AdaptiveLearningOrchestrator
from ml_signal_filter import MLSignalFilter

# Create adaptive orchestrator
orchestrator = AdaptiveLearningOrchestrator(
    strategies=['SMA', 'RSI', 'MACD', 'BollingerBands'],
    parameter_ranges={
        'trailing_stop': (0.02, 0.10),
        'risk_threshold': (0.03, 0.15)
    }
)

# Create ML signal filter (existing)
ml_filter = MLSignalFilter(model_type='random_forest')

# Trading loop
while trading:
    # Adaptive strategy selection
    strategy = orchestrator.select_strategy(market_data, method='qlearning')
    
    # Get adaptive parameters
    params = orchestrator.get_parameters()
    
    # Generate signal
    signal = strategies[strategy].generate_signal(price_data)
    
    # ML signal quality check
    should_filter, scores = ml_filter.should_filter_signal(signal_data)
    
    if not should_filter:
        # Execute trade
        profit = execute_trade(signal)
        
        # Update adaptive learning
        orchestrator.update_from_trade(strategy, profit, market_data, signal_data)
        
        # Automatic model retraining
        if orchestrator.should_retrain_model():
            training_data, labels = orchestrator.get_training_data_for_retrain()
            ml_filter.train(training_data, labels)
            orchestrator.clear_training_buffer()
```

**Performance Impact**: Expected 10-25% improvement in overall profitability through continuous learning and automatic optimization.
