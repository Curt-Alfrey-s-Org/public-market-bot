# Adaptive Learning Guide - market-pie5-bot

## Overview

The **Adaptive Learning Module** implements reinforcement learning and adaptive models that evolve based on real-world trading performance. Unlike static ML models that require manual retraining, adaptive learning continuously improves the bot's decision-making through experience.

**Status**: Production-Ready ✅

## Key Features

### 1. Q-Learning Strategy Selector
- **What it does**: Learns which trading strategy works best in different market conditions
- **How it learns**: Uses Q-Learning (reinforcement learning) to build a policy for strategy selection
- **Benefit**: Automatically adapts to changing market regimes without manual intervention

### 2. Multi-Armed Bandit
- **What it does**: Dynamically allocates resources to strategies based on their performance
- **How it works**: Uses Thompson Sampling (Bayesian approach) to balance exploration and exploitation
- **Benefit**: Quickly identifies and favors winning strategies while still exploring alternatives

### 3. Adaptive Parameter Tuner
- **What it does**: Automatically adjusts strategy parameters (trailing stop, risk threshold, etc.) based on recent performance
- **How it works**: Uses hill climbing with sliding window performance monitoring
- **Benefit**: No need to manually tune parameters - the bot optimizes itself

### 4. Online Learning Manager
- **What it does**: Continuously updates ML models as new trade data becomes available
- **How it works**: Accumulates new training samples and triggers retraining when threshold is reached
- **Benefit**: Models stay current with recent market conditions without manual intervention

## Quick Start

### Basic Usage

```python
from adaptive_learning import AdaptiveLearningOrchestrator

# Initialize with your strategies
strategies = ['SMA', 'RSI', 'MACD', 'BollingerBands', 'Momentum']

# Define parameter ranges for adaptive tuning
parameter_ranges = {
    'trailing_stop': (0.02, 0.10),      # 2% to 10%
    'risk_threshold': (0.03, 0.15),     # 3% to 15%
    'min_confidence': (0.50, 0.80)      # 50% to 80%
}

# Create orchestrator
orchestrator = AdaptiveLearningOrchestrator(
    strategies=strategies,
    parameter_ranges=parameter_ranges,
    use_qlearning=True,
    use_bandit=True,
    use_param_tuning=True,
    use_online_learning=True
)

# Select strategy based on market conditions
market_data = {
    'rsi': 35,              # Oversold
    'volatility': 0.025,    # Medium volatility
    'trend': 0.03,          # Uptrend
    'volume_ratio': 1.2     # Above average volume
}

strategy = orchestrator.select_strategy(market_data, method='qlearning')
print(f"Selected strategy: {strategy}")

# After executing trade, update the learning system
profit = 1.50  # Example profit
orchestrator.update_from_trade(strategy, profit, market_data)

# Get adaptive parameters
params = orchestrator.get_parameters()
print(f"Current trailing stop: {params['trailing_stop']:.3f}")
print(f"Current risk threshold: {params['risk_threshold']:.3f}")
```

### Integration with Trading Bot

```python
# In main.py or your trading script

from adaptive_learning import AdaptiveLearningOrchestrator
from strategies import SMAStrategy, RSIStrategy, MACDStrategy

# Initialize adaptive learning
orchestrator = AdaptiveLearningOrchestrator(
    strategies=['SMA', 'RSI', 'MACD'],
    parameter_ranges={
        'trailing_stop': (0.02, 0.10),
        'risk_threshold': (0.03, 0.15)
    }
)

# Load previous learning state if available
if os.path.exists('models/adaptive_learning'):
    orchestrator.load('models/adaptive_learning')
    print("Loaded previous learning state")

# Main trading loop
while trading:
    # Get market data
    market_data = get_market_indicators(symbol)
    
    # Let adaptive learning select the strategy
    selected_strategy_name = orchestrator.select_strategy(
        market_data, 
        method='qlearning'  # or 'bandit'
    )
    
    # Get adaptive parameters
    params = orchestrator.get_parameters()
    
    # Apply parameters to bot
    bot.trailing_stop_percent = params['trailing_stop']
    bot.risk_threshold = params['risk_threshold']
    
    # Execute trade with selected strategy
    strategy = strategy_map[selected_strategy_name]
    signal = strategy.generate_signal(price_data)
    
    if signal != 'HOLD':
        # Execute trade
        profit = bot.execute_trade(symbol, signal)
        
        # Update adaptive learning with result
        orchestrator.update_from_trade(
            selected_strategy_name,
            profit,
            market_data,
            trade_data={'signal': signal, 'price': price}
        )
    
    # Check if models should be retrained
    if orchestrator.should_retrain_model():
        print("Retraining ML models with new data...")
        training_data, labels = orchestrator.get_training_data_for_retrain()
        
        # Retrain your ML models here
        ml_filter.train(training_data, labels)
        
        # Clear buffer
        orchestrator.clear_training_buffer()
    
    # Periodically save learning state
    if trade_count % 100 == 0:
        orchestrator.save('models/adaptive_learning')

# Save final state
orchestrator.save('models/adaptive_learning')
```

## Component Details

### Q-Learning Strategy Selector

**Use Case**: Learning which strategy performs best in different market conditions

**Configuration**:
```python
from adaptive_learning import QLearningStrategySelector

qlearner = QLearningStrategySelector(
    strategies=['SMA', 'RSI', 'MACD'],
    learning_rate=0.1,        # How fast to learn (0 to 1)
    discount_factor=0.95,     # Value of future rewards
    epsilon=0.2,              # Exploration rate (20%)
    epsilon_decay=0.995,      # Decay rate per episode
    min_epsilon=0.05          # Minimum exploration (5%)
)
```

**Learning Process**:
1. Observes market state (RSI, volatility, trend, volume)
2. Selects strategy using epsilon-greedy policy
3. Receives reward (profit/loss from trade)
4. Updates Q-values based on reward
5. Gradually shifts from exploration to exploitation

**Performance Tracking**:
```python
stats = qlearner.get_statistics()
print(f"Total episodes: {stats['total_episodes']}")
print(f"Average reward: {stats['average_reward']:.3f}")
print(f"Current exploration rate: {stats['epsilon']:.3f}")

# Per-strategy performance
for strategy, perf in stats['strategy_performance'].items():
    print(f"\n{strategy}:")
    print(f"  Count: {perf['count']}")
    print(f"  Avg Reward: {perf['avg_reward']:.3f}")
    print(f"  Win Rate: {perf['win_rate']:.2%}")
```

**Persistence**:
```python
# Save learned Q-values
qlearner.save('models/qlearning_state.pkl')

# Load in future sessions
qlearner.load('models/qlearning_state.pkl')
```

### Multi-Armed Bandit

**Use Case**: Quickly identifying and favoring winning strategies

**Configuration**:
```python
from adaptive_learning import MultiArmedBandit

bandit = MultiArmedBandit(strategies=['SMA', 'RSI', 'MACD'])
```

**Usage**:
```python
# Select strategy using Thompson Sampling
strategy = bandit.select_strategy()

# Execute trade
profit = execute_trade(strategy)

# Update bandit with result
success = profit > 0
bandit.update_from_result(strategy, success, reward=profit)
```

**Statistics**:
```python
stats = bandit.get_statistics()

for strategy, perf in stats['strategy_performance'].items():
    print(f"{strategy}:")
    print(f"  Win Rate: {perf['win_rate']:.2%}")
    print(f"  Expected Value: {perf['expected_value']:.3f}")
    print(f"  Avg Reward: {perf['avg_reward']:.3f}")
```

**Comparison with Q-Learning**:
- **Bandit**: Faster to converge, simpler, no market state awareness
- **Q-Learning**: Considers market state, more sophisticated, slower to converge
- **Recommendation**: Use bandit for quick adaptation, Q-Learning for long-term optimization

### Adaptive Parameter Tuner

**Use Case**: Automatically optimizing strategy parameters

**Configuration**:
```python
from adaptive_learning import AdaptiveParameterTuner

tuner = AdaptiveParameterTuner(
    parameter_ranges={
        'trailing_stop': (0.02, 0.10),
        'risk_threshold': (0.03, 0.15),
        'min_confidence': (0.50, 0.80)
    },
    window_size=50,           # Look at last 50 trades
    adaptation_rate=0.1       # How aggressively to adjust
)
```

**Usage**:
```python
# Get current parameters
params = tuner.get_parameters()
bot.trailing_stop = params['trailing_stop']

# After trade, update with performance
profit = execute_trade()
tuner.update_from_performance(profit)

# Parameters automatically adjust based on performance trend
```

**Adaptation Strategy**:
- Monitors recent performance (sliding window)
- If performance declining: moves toward best known parameters
- If performance good: explores nearby parameter space
- Always keeps parameters within valid bounds

### Online Learning Manager

**Use Case**: Keeping ML models up-to-date with recent data

**Configuration**:
```python
from adaptive_learning import OnlineLearningManager

online_learner = OnlineLearningManager(
    retrain_threshold=50,           # Retrain after 50 new samples
    performance_window=100,          # Monitor last 100 trades
    min_performance_improvement=0.01 # Require 1% improvement
)
```

**Usage**:
```python
# Add training sample after each trade
trade_data = {
    'signal': 'BUY',
    'price': 150.0,
    'indicators': {...}
}
label = 1 if profit > 0 else 0
online_learner.add_sample(trade_data, label)

# Check if should retrain
if online_learner.should_retrain():
    # Get accumulated training data
    training_data, labels = online_learner.get_training_data()
    
    # Retrain ML models
    ml_filter.train(training_data, labels)
    
    # Clear buffer
    online_learner.clear_buffer()
```

## Advanced Topics

### Exploration vs Exploitation

The Q-Learning component balances exploration (trying new strategies) and exploitation (using known good strategies) through epsilon-greedy policy:

- **High epsilon (0.3-0.5)**: More exploration, good for discovering new patterns
- **Low epsilon (0.05-0.1)**: More exploitation, good for stable profitable trading
- **Decay**: Epsilon naturally decreases over time (995 decay rate = slow, 0.99 = fast)

**Recommendations**:
- **New bot**: Start with epsilon=0.3, decay=0.995 to learn quickly
- **Established bot**: Use epsilon=0.1, decay=0.999 to maintain stability
- **Changing markets**: Temporarily increase epsilon to re-explore

### Market State Discretization

Q-Learning discretizes continuous market data into states:

```python
# Continuous
{'rsi': 28.5, 'volatility': 0.023, 'trend': 0.018, 'volume_ratio': 1.15}

# Discretized
"oversold_medium_up_normal"
```

**Current discretization**:
- **RSI**: oversold (<30), neutral (30-70), overbought (>70)
- **Volatility**: low (<1.5%), medium (1.5-3%), high (>3%)
- **Trend**: down (<-2%), sideways (-2% to 2%), up (>2%)
- **Volume**: low (<80%), normal (80-120%), high (>120%)

**Customization**: Modify `discretize_market_state()` method to add more granular states or additional indicators.

### Combining Multiple Methods

For best results, use multiple adaptive learning methods together:

```python
orchestrator = AdaptiveLearningOrchestrator(
    strategies=['SMA', 'RSI', 'MACD'],
    parameter_ranges={...},
    use_qlearning=True,      # Long-term learning
    use_bandit=True,         # Quick adaptation
    use_param_tuning=True,   # Auto-optimization
    use_online_learning=True # Keep models current
)

# Use Q-Learning for strategy selection (considers market state)
strategy = orchestrator.select_strategy(market_data, method='qlearning')

# Or use bandit (faster, simpler)
strategy = orchestrator.select_strategy(market_data, method='bandit')

# Both methods update from the same trade results
orchestrator.update_from_trade(strategy, profit, market_data)
```

### Performance Monitoring

Track adaptive learning effectiveness:

```python
# Get comprehensive statistics
all_stats = orchestrator.get_all_statistics()

print(f"Total trades: {all_stats['trade_count']}")

# Q-Learning stats
qlearning_stats = all_stats['components']['qlearning']
print(f"Average reward: {qlearning_stats['average_reward']:.3f}")

# Check which strategies are being favored
for strategy, perf in qlearning_stats['strategy_performance'].items():
    print(f"{strategy}: {perf['win_rate']:.2%} win rate")

# Bandit stats
bandit_stats = all_stats['components']['bandit']
# ... similar analysis

# Parameter tuner stats
param_stats = all_stats['components']['param_tuner']
print(f"Best performance: {param_stats['best_performance']:.3f}")
print(f"Current parameters: {param_stats['current_parameters']}")
```

## Best Practices

### 1. Start Simple
- Begin with just Q-Learning or just bandit
- Add parameter tuning after 100+ trades
- Enable online learning once you have stable performance

### 2. Monitor and Validate
- Check statistics regularly (every 50-100 trades)
- Verify that learning is improving performance
- Watch for overfitting (good recent performance but poor overall)

### 3. Persist State
- Save adaptive learning state frequently (every 100 trades)
- Keep backups of well-performing states
- Test loading/saving in paper trading mode first

### 4. Parameter Ranges
- Use realistic parameter ranges based on your risk tolerance
- Don't allow parameters to go into dangerous territory
- Consider market conditions when setting ranges

### 5. Combine with Risk Management
- Adaptive learning optimizes decisions, not risk
- Always maintain position sizing and stop losses
- Use capital floor protection regardless of adaptive settings

### 6. Evaluation Period
- Give adaptive learning at least 100 trades to learn patterns
- Don't expect immediate improvements (exploration phase)
- Compare performance before/after enabling adaptive learning

## Expected Performance Impact

Based on reinforcement learning in trading systems:

| Metric | Without Adaptive Learning | With Adaptive Learning | Improvement |
|--------|---------------------------|------------------------|-------------|
| Strategy Selection | Fixed/Manual | Adapts to conditions | +5-15% win rate |
| Parameter Optimization | Manual tuning | Auto-optimized | +10-20% returns |
| Market Adaptation | Slow/Manual | Continuous | Better drawdown recovery |
| Model Currency | Manual retrain | Auto-retrain | Always current |

**Note**: Results depend on market conditions, strategy quality, and sufficient learning time (100+ trades).

## Troubleshooting

### Issue: Q-Learning always selects same strategy

**Cause**: Epsilon too low or learned Q-values strongly favor one strategy

**Solution**:
```python
# Increase exploration temporarily
qlearner.epsilon = 0.3

# Or reset Q-values for fresh start
qlearner = QLearningStrategySelector(strategies, epsilon=0.3)
```

### Issue: Adaptive parameters becoming extreme

**Cause**: Parameter bounds too wide or adaptation rate too high

**Solution**:
```python
# Narrow parameter ranges
parameter_ranges = {
    'trailing_stop': (0.03, 0.07),  # Narrower range
    'risk_threshold': (0.04, 0.10)
}

# Reduce adaptation rate
tuner = AdaptiveParameterTuner(
    parameter_ranges=parameter_ranges,
    adaptation_rate=0.05  # Slower adaptation
)
```

### Issue: Online learning retraining too frequently

**Cause**: Retrain threshold too low

**Solution**:
```python
# Increase threshold
online_learner = OnlineLearningManager(
    retrain_threshold=100  # Retrain less often
)
```

### Issue: Bandit not converging to best strategy

**Cause**: Not enough samples or all strategies similar performance

**Solution**:
- Run more trades (need 50+ per strategy minimum)
- Check if strategies actually have different performance
- Verify trade results are being correctly reported

## Integration with Existing ML Features

Adaptive learning complements existing ML signal filtering:

```python
from ml_signal_filter import MLSignalFilter
from adaptive_learning import AdaptiveLearningOrchestrator

# Existing ML signal filter
ml_filter = MLSignalFilter(model_type='random_forest')
ml_filter.train(historical_data, labels)

# New adaptive learning
orchestrator = AdaptiveLearningOrchestrator(strategies=[...])

# Use both together
strategy = orchestrator.select_strategy(market_data, method='qlearning')
signal = strategies[strategy].generate_signal(price_data)

# ML filter checks signal quality
should_filter, scores = ml_filter.should_filter_signal(signal_data)

if not should_filter:
    # Execute trade
    profit = execute_trade(signal)
    
    # Update adaptive learning
    orchestrator.update_from_trade(strategy, profit, market_data, signal_data)
    
    # Update online learning for ML filter
    if orchestrator.should_retrain_model():
        training_data, labels = orchestrator.get_training_data_for_retrain()
        ml_filter.train(training_data, labels)
        orchestrator.clear_training_buffer()
```

## Future Enhancements

Planned improvements:

- Deep Q-Network (DQN) for more complex state spaces
- Policy gradient methods (Actor-Critic)
- Multi-objective optimization (maximize return, minimize risk)
- Meta-learning for faster adaptation to new market regimes
- Ensemble of adaptive models with voting

## Support

For issues or questions about adaptive learning:

1. Check statistics to understand what the system is learning
2. Review logs for adaptive learning decisions
3. Verify market data quality (garbage in, garbage out)
4. Test in paper trading mode before live deployment

## Summary

The Adaptive Learning Module enables the market-pie5-bot to:

✅ **Learn from experience** - Continuously improves through real trades  
✅ **Adapt to markets** - Automatically adjusts to changing conditions  
✅ **Optimize parameters** - Self-tunes without manual intervention  
✅ **Stay current** - Models automatically retrain with new data  
✅ **Balance exploration** - Discovers new patterns while exploiting known strategies  

This creates a truly intelligent trading system that evolves and improves over time, rather than remaining static like traditional algorithmic trading bots.
