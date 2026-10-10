#!/usr/bin/env python3
"""
Trading strategies for market-pie5-bot

SWING TRADING FOCUS:
This bot is designed for swing trading with a minimum hold period of 1+ days
(configurable via SWING_MIN_HOLD_DAYS environment variable in .env file). 
All strategies prioritize multi-day timeframes and are optimized for positions 
held overnight or longer.

Swing trading strategies avoid intraday trading and focus on capturing larger
price movements over several days. The bot enforces minimum holding periods
to ensure compliance with the swing trading approach.

Implemented strategies:
- Simple Moving Average (SMA) Crossover (momentum trading, multi-day trends)
- Bollinger Bands (mean reversion trading, multi-day volatility)
- RSI (Relative Strength Index, multi-day momentum)
- MACD (Moving Average Convergence Divergence, multi-day trends)
- Momentum (multi-day rate of change)

All strategies use daily timeframes (not intraday) and generate signals that
align with the bot's swing trading philosophy of "buy today, sell tomorrow+".
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradingStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.signals = []
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on strategy
        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        raise NotImplementedError("Subclasses must implement generate_signal")
    
    def get_last_signal(self) -> Optional[str]:
        """Get the most recent signal"""
        return self.signals[-1] if self.signals else None


class SMAStrategy(TradingStrategy):
    """
    Simple Moving Average Crossover Strategy (Swing Trading - Multi-Day Momentum)
    
    This strategy is optimized for swing trading with positions held for multiple days.
    Uses daily price data to identify trend changes over longer timeframes.
    
    Strategy:
    - BUY when fast SMA crosses above slow SMA (bullish signal, uptrend begins)
    - SELL when fast SMA crosses below slow SMA (bearish signal, downtrend begins)
    
    Default parameters (20/50 days) are designed for swing trading:
    - 20-day fast SMA: Captures medium-term trend
    - 50-day slow SMA: Captures long-term trend
    - Crossovers signal multi-day trend reversals (not intraday noise)
    
    This is a momentum strategy that follows multi-day trends, ideal for
    the bot's "buy today, sell tomorrow+" swing trading approach.
    """
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        """
        Initialize SMA Crossover strategy
        
        Args:
            fast_period: Period for fast-moving average (default: 20)
            slow_period: Period for slow-moving average (default: 50)
        """
        super().__init__("SMA Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        logger.info(f"Initialized {self.name} strategy (fast={fast_period}, slow={slow_period})")
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on SMA crossover
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(data) < self.slow_period:
            logger.debug(f"Insufficient data for SMA strategy (need {self.slow_period}, have {len(data)})")
            return 'HOLD'
        
        # Calculate SMAs
        data['sma_fast'] = self.calculate_sma(data['close'], self.fast_period)
        data['sma_slow'] = self.calculate_sma(data['close'], self.slow_period)
        
        # Get last two periods for crossover detection
        if len(data) < 2:
            return 'HOLD'
        
        fast_prev = data['sma_fast'].iloc[-2]
        fast_curr = data['sma_fast'].iloc[-1]
        slow_prev = data['sma_slow'].iloc[-2]
        slow_curr = data['sma_slow'].iloc[-1]
        
        # Check if all values are valid
        if pd.isna(fast_prev) or pd.isna(fast_curr) or pd.isna(slow_prev) or pd.isna(slow_curr):
            return 'HOLD'
        
        # Detect crossover
        # Golden Cross: fast crosses above slow (BUY signal)
        if fast_prev <= slow_prev and fast_curr > slow_curr:
            signal = 'BUY'
            logger.info(f"SMA Golden Cross detected: fast={fast_curr:.2f} > slow={slow_curr:.2f}")
        # Death Cross: fast crosses below slow (SELL signal)
        elif fast_prev >= slow_prev and fast_curr < slow_curr:
            signal = 'SELL'
            logger.info(f"SMA Death Cross detected: fast={fast_curr:.2f} < slow={slow_curr:.2f}")
        else:
            signal = 'HOLD'
        
        self.signals.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'fast_sma': fast_curr,
            'slow_sma': slow_curr
        })
        
        return signal
    
    def get_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get current indicator values for analysis"""
        if len(data) < self.slow_period:
            return {}
        
        data['sma_fast'] = self.calculate_sma(data['close'], self.fast_period)
        data['sma_slow'] = self.calculate_sma(data['close'], self.slow_period)
        
        return {
            'sma_fast': data['sma_fast'].iloc[-1],
            'sma_slow': data['sma_slow'].iloc[-1],
            'fast_period': self.fast_period,
            'slow_period': self.slow_period
        }


class BollingerBandsStrategy(TradingStrategy):
    """
    Bollinger Bands Strategy (Mean Reversion Trading)
    
    Strategy:
    - BUY when price touches or crosses below lower band (oversold)
    - SELL when price touches or crosses above upper band (overbought)
    
    This is a mean reversion strategy assuming prices revert to the mean.
    """
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        """
        Initialize Bollinger Bands strategy
        
        Args:
            period: Period for moving average (default: 20)
            num_std: Number of standard deviations for bands (default: 2.0)
        """
        super().__init__("Bollinger Bands")
        self.period = period
        self.num_std = num_std
        logger.info(f"Initialized {self.name} strategy (period={period}, std={num_std})")
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Returns:
            Tuple of (middle_band, upper_band, lower_band)
        """
        # Middle band: SMA
        middle_band = prices.rolling(window=self.period).mean()
        
        # Standard deviation
        std_dev = prices.rolling(window=self.period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (std_dev * self.num_std)
        lower_band = middle_band - (std_dev * self.num_std)
        
        return middle_band, upper_band, lower_band
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on Bollinger Bands
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(data) < self.period:
            logger.debug(f"Insufficient data for Bollinger Bands (need {self.period}, have {len(data)})")
            return 'HOLD'
        
        # Calculate Bollinger Bands
        middle, upper, lower = self.calculate_bollinger_bands(data['close'])
        
        data['bb_middle'] = middle
        data['bb_upper'] = upper
        data['bb_lower'] = lower
        
        # Get current and previous values
        if len(data) < 2:
            return 'HOLD'
        
        price_prev = data['close'].iloc[-2]
        price_curr = data['close'].iloc[-1]
        lower_prev = data['bb_lower'].iloc[-2]
        lower_curr = data['bb_lower'].iloc[-1]
        upper_prev = data['bb_upper'].iloc[-2]
        upper_curr = data['bb_upper'].iloc[-1]
        middle_curr = data['bb_middle'].iloc[-1]
        
        # Check if all values are valid
        if any(pd.isna(v) for v in [price_prev, price_curr, lower_prev, lower_curr, 
                                     upper_prev, upper_curr, middle_curr]):
            return 'HOLD'
        
        # Generate signals
        # BUY: Price crosses below lower band (oversold)
        if price_prev >= lower_prev and price_curr < lower_curr:
            signal = 'BUY'
            logger.info(f"Bollinger Bands BUY signal: price={price_curr:.2f} crossed below lower={lower_curr:.2f}")
        # SELL: Price crosses above upper band (overbought)
        elif price_prev <= upper_prev and price_curr > upper_curr:
            signal = 'SELL'
            logger.info(f"Bollinger Bands SELL signal: price={price_curr:.2f} crossed above upper={upper_curr:.2f}")
        else:
            signal = 'HOLD'
        
        # Calculate band width (volatility indicator)
        band_width = (upper_curr - lower_curr) / middle_curr if middle_curr > 0 else 0
        
        self.signals.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'price': price_curr,
            'upper_band': upper_curr,
            'middle_band': middle_curr,
            'lower_band': lower_curr,
            'band_width': band_width
        })
        
        return signal
    
    def get_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get current indicator values for analysis"""
        if len(data) < self.period:
            return {}
        
        middle, upper, lower = self.calculate_bollinger_bands(data['close'])
        
        price_curr = data['close'].iloc[-1]
        middle_curr = middle.iloc[-1]
        upper_curr = upper.iloc[-1]
        lower_curr = lower.iloc[-1]
        
        # Calculate position within bands (0 = at lower, 1 = at upper)
        if upper_curr != lower_curr:
            position = (price_curr - lower_curr) / (upper_curr - lower_curr)
        else:
            position = 0.5
        
        # Calculate band width
        band_width = (upper_curr - lower_curr) / middle_curr if middle_curr > 0 else 0
        
        return {
            'price': price_curr,
            'upper_band': upper_curr,
            'middle_band': middle_curr,
            'lower_band': lower_curr,
            'band_width': band_width,
            'position_in_bands': position,
            'period': self.period,
            'num_std': self.num_std
        }


class RSIStrategy(TradingStrategy):
    """
    RSI (Relative Strength Index) Strategy
    
    Strategy:
    - BUY when RSI crosses below oversold threshold (default: 30)
    - SELL when RSI crosses above overbought threshold (default: 70)
    
    RSI measures momentum and identifies overbought/oversold conditions.
    """
    
    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        """
        Initialize RSI strategy
        
        Args:
            period: RSI calculation period (default: 14)
            oversold: Oversold threshold for BUY signals (default: 30)
                      Note: 30 is the industry-standard threshold in technical analysis
            overbought: Overbought threshold for SELL signals (default: 70)
                        Note: 70 is the industry-standard threshold in technical analysis
        """
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        logger.info(f"Initialized {self.name} strategy (period={period}, oversold={oversold}, overbought={overbought})")
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on RSI
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(data) < self.period + 1:
            logger.debug(f"Insufficient data for RSI strategy (need {self.period + 1}, have {len(data)})")
            return 'HOLD'
        
        # Calculate RSI
        data['rsi'] = self.calculate_rsi(data['close'])
        
        # Get current and previous RSI
        if len(data) < 2:
            return 'HOLD'
        
        rsi_prev = data['rsi'].iloc[-2]
        rsi_curr = data['rsi'].iloc[-1]
        
        # Check if values are valid
        if pd.isna(rsi_prev) or pd.isna(rsi_curr):
            return 'HOLD'
        
        # Generate signals
        # BUY: RSI crosses below oversold threshold
        if rsi_prev >= self.oversold and rsi_curr < self.oversold:
            signal = 'BUY'
            logger.info(f"RSI BUY signal: RSI={rsi_curr:.2f} crossed below {self.oversold}")
        # SELL: RSI crosses above overbought threshold
        elif rsi_prev <= self.overbought and rsi_curr > self.overbought:
            signal = 'SELL'
            logger.info(f"RSI SELL signal: RSI={rsi_curr:.2f} crossed above {self.overbought}")
        else:
            signal = 'HOLD'
        
        self.signals.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'rsi': rsi_curr
        })
        
        return signal
    
    def get_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get current indicator values for analysis"""
        if len(data) < self.period + 1:
            return {}
        
        rsi = self.calculate_rsi(data['close'])
        rsi_curr = rsi.iloc[-1]
        
        # Determine condition
        if rsi_curr < self.oversold:
            condition = 'oversold'
        elif rsi_curr > self.overbought:
            condition = 'overbought'
        else:
            condition = 'neutral'
        
        return {
            'rsi': rsi_curr,
            'condition': condition,
            'oversold': self.oversold,
            'overbought': self.overbought,
            'period': self.period
        }


class MACDStrategy(TradingStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy
    
    Strategy:
    - BUY when MACD line crosses above signal line (bullish crossover)
    - SELL when MACD line crosses below signal line (bearish crossover)
    
    MACD is a trend-following momentum indicator.
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        Initialize MACD strategy
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
        """
        super().__init__("MACD")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        logger.info(f"Initialized {self.name} strategy (fast={fast}, slow={slow}, signal={signal})")
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD line, signal line, and histogram
        
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate EMAs
        ema_fast = self.calculate_ema(prices, self.fast)
        ema_slow = self.calculate_ema(prices, self.slow)
        
        # MACD line = fast EMA - slow EMA
        macd_line = ema_fast - ema_slow
        
        # Signal line = EMA of MACD line
        signal_line = self.calculate_ema(macd_line, self.signal)
        
        # Histogram = MACD line - signal line
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on MACD
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(data) < self.slow + self.signal:
            logger.debug(f"Insufficient data for MACD strategy (need {self.slow + self.signal}, have {len(data)})")
            return 'HOLD'
        
        # Calculate MACD
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])
        
        data['macd'] = macd_line
        data['macd_signal'] = signal_line
        data['macd_histogram'] = histogram
        
        # Get current and previous values
        if len(data) < 2:
            return 'HOLD'
        
        macd_prev = data['macd'].iloc[-2]
        macd_curr = data['macd'].iloc[-1]
        signal_prev = data['macd_signal'].iloc[-2]
        signal_curr = data['macd_signal'].iloc[-1]
        
        # Check if values are valid
        if any(pd.isna(v) for v in [macd_prev, macd_curr, signal_prev, signal_curr]):
            return 'HOLD'
        
        # Generate signals based on crossover
        # BUY: MACD crosses above signal line
        if macd_prev <= signal_prev and macd_curr > signal_curr:
            signal = 'BUY'
            logger.info(f"MACD BUY signal: MACD={macd_curr:.4f} crossed above signal={signal_curr:.4f}")
        # SELL: MACD crosses below signal line
        elif macd_prev >= signal_prev and macd_curr < signal_curr:
            signal = 'SELL'
            logger.info(f"MACD SELL signal: MACD={macd_curr:.4f} crossed below signal={signal_curr:.4f}")
        else:
            signal = 'HOLD'
        
        histogram_curr = data['macd_histogram'].iloc[-1]
        
        self.signals.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'macd': macd_curr,
            'signal_line': signal_curr,
            'histogram': histogram_curr
        })
        
        return signal
    
    def get_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get current indicator values for analysis"""
        if len(data) < self.slow + self.signal:
            return {}
        
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])
        
        macd_curr = macd_line.iloc[-1]
        signal_curr = signal_line.iloc[-1]
        histogram_curr = histogram.iloc[-1]
        
        # Determine trend
        if macd_curr > signal_curr:
            trend = 'bullish'
        elif macd_curr < signal_curr:
            trend = 'bearish'
        else:
            trend = 'neutral'
        
        return {
            'macd': macd_curr,
            'signal_line': signal_curr,
            'histogram': histogram_curr,
            'trend': trend,
            'fast': self.fast,
            'slow': self.slow,
            'signal_period': self.signal
        }


class MomentumStrategy(TradingStrategy):
    """
    Momentum Strategy
    
    Strategy:
    - BUY when momentum turns positive (price > price N periods ago)
    - SELL when momentum turns negative (price < price N periods ago)
    
    Simple momentum strategy based on rate of change.
    """
    
    def __init__(self, period: int = 10, threshold: float = 0.02):
        """
        Initialize Momentum strategy
        
        Args:
            period: Lookback period for momentum calculation (default: 10)
            threshold: Minimum momentum change to generate signal (default: 0.02 = 2%)
        """
        super().__init__("Momentum")
        self.period = period
        self.threshold = threshold
        logger.info(f"Initialized {self.name} strategy (period={period}, threshold={threshold})")
    
    def calculate_momentum(self, prices: pd.Series) -> pd.Series:
        """
        Calculate momentum as percentage change over period
        
        Returns:
            Series with momentum values (as percentages)
        """
        return prices.pct_change(periods=self.period)
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate trading signal based on momentum
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(data) < self.period + 1:
            logger.debug(f"Insufficient data for Momentum strategy (need {self.period + 1}, have {len(data)})")
            return 'HOLD'
        
        # Calculate momentum
        data['momentum'] = self.calculate_momentum(data['close'])
        
        # Get current and previous momentum
        if len(data) < 2:
            return 'HOLD'
        
        momentum_prev = data['momentum'].iloc[-2]
        momentum_curr = data['momentum'].iloc[-1]
        
        # Check if values are valid
        if pd.isna(momentum_prev) or pd.isna(momentum_curr):
            return 'HOLD'
        
        # Generate signals based on momentum threshold
        # BUY: Momentum turns positive and exceeds threshold
        if momentum_prev <= self.threshold and momentum_curr > self.threshold:
            signal = 'BUY'
            logger.info(f"Momentum BUY signal: momentum={momentum_curr:.2%} crossed above {self.threshold:.2%}")
        # SELL: Momentum turns negative and falls below threshold
        elif momentum_prev >= -self.threshold and momentum_curr < -self.threshold:
            signal = 'SELL'
            logger.info(f"Momentum SELL signal: momentum={momentum_curr:.2%} crossed below {-self.threshold:.2%}")
        else:
            signal = 'HOLD'
        
        self.signals.append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'momentum': momentum_curr
        })
        
        return signal
    
    def get_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get current indicator values for analysis"""
        if len(data) < self.period + 1:
            return {}
        
        momentum = self.calculate_momentum(data['close'])
        momentum_curr = momentum.iloc[-1]
        
        # Determine condition
        if momentum_curr > self.threshold:
            condition = 'strong_positive'
        elif momentum_curr > 0:
            condition = 'weak_positive'
        elif momentum_curr > -self.threshold:
            condition = 'weak_negative'
        else:
            condition = 'strong_negative'
        
        return {
            'momentum': momentum_curr,
            'condition': condition,
            'threshold': self.threshold,
            'period': self.period
        }


class StrategyManager:
    """
    Manages multiple trading strategies and combines their signals
    """
    
    def __init__(self):
        self.strategies = []
        logger.info("Initialized StrategyManager")
    
    def add_strategy(self, strategy: TradingStrategy, weight: float = 1.0):
        """
        Add a strategy to the manager
        
        Args:
            strategy: TradingStrategy instance
            weight: Weight for this strategy in combined signal (default: 1.0)
        """
        self.strategies.append({
            'strategy': strategy,
            'weight': weight
        })
        logger.info(f"Added strategy: {strategy.name} (weight={weight})")
    
    def generate_combined_signal(self, data: pd.DataFrame) -> str:
        """
        Generate combined signal from all strategies
        
        Uses weighted voting:
        - Each strategy votes BUY (+1), SELL (-1), or HOLD (0)
        - Weights are applied to votes
        - Final signal based on weighted sum
        
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
            
            logger.debug(f"{strategy.name}: {signal} (weighted vote: {weighted_vote:+.2f})")
        
        # Calculate combined signal
        total_vote = sum(votes)
        
        # Decision threshold: require significant agreement
        if total_vote > 0.5:
            combined_signal = 'BUY'
        elif total_vote < -0.5:
            combined_signal = 'SELL'
        else:
            combined_signal = 'HOLD'
        
        logger.info(f"Combined signal: {combined_signal} (total vote: {total_vote:+.2f})")
        
        return combined_signal
    
    def get_all_indicator_values(self, data: pd.DataFrame) -> Dict:
        """Get indicator values from all strategies"""
        indicators = {}
        
        for item in self.strategies:
            strategy = item['strategy']
            strategy_indicators = strategy.get_indicator_values(data)
            indicators[strategy.name] = strategy_indicators
        
        return indicators


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Trading Strategies Module - Example Usage")
    print("="*60)
    
    # Generate sample data
    # Note: Using fixed date and seed for reproducible examples
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate price data with trend and noise
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.normal(0, 2, 100)
    prices = base_price + trend + noise
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    print(f"\nGenerated {len(data)} days of sample data")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Test SMA Strategy
    print("\n" + "="*60)
    print("Testing SMA Crossover Strategy")
    print("="*60)
    
    sma_strategy = SMAStrategy(fast_period=10, slow_period=30)
    signal = sma_strategy.generate_signal(data)
    print(f"Signal: {signal}")
    
    indicators = sma_strategy.get_indicator_values(data)
    if indicators:
        print(f"Fast SMA: ${indicators['sma_fast']:.2f}")
        print(f"Slow SMA: ${indicators['sma_slow']:.2f}")
    
    # Test Bollinger Bands Strategy
    print("\n" + "="*60)
    print("Testing Bollinger Bands Strategy")
    print("="*60)
    
    bb_strategy = BollingerBandsStrategy(period=20, num_std=2.0)
    signal = bb_strategy.generate_signal(data)
    print(f"Signal: {signal}")
    
    indicators = bb_strategy.get_indicator_values(data)
    if indicators:
        print(f"Current Price: ${indicators['price']:.2f}")
        print(f"Upper Band: ${indicators['upper_band']:.2f}")
        print(f"Middle Band: ${indicators['middle_band']:.2f}")
        print(f"Lower Band: ${indicators['lower_band']:.2f}")
        print(f"Band Width: {indicators['band_width']:.4f}")
        print(f"Position in Bands: {indicators['position_in_bands']:.2%}")
    
    # Test RSI Strategy
    print("\n" + "="*60)
    print("Testing RSI Strategy")
    print("="*60)
    
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    signal = rsi_strategy.generate_signal(data)
    print(f"Signal: {signal}")
    
    indicators = rsi_strategy.get_indicator_values(data)
    if indicators:
        print(f"RSI: {indicators['rsi']:.2f}")
        print(f"Condition: {indicators['condition']}")
    
    # Test MACD Strategy
    print("\n" + "="*60)
    print("Testing MACD Strategy")
    print("="*60)
    
    macd_strategy = MACDStrategy(fast=12, slow=26, signal=9)
    signal = macd_strategy.generate_signal(data)
    print(f"Signal: {signal}")
    
    indicators = macd_strategy.get_indicator_values(data)
    if indicators:
        print(f"MACD: {indicators['macd']:.4f}")
        print(f"Signal Line: {indicators['signal_line']:.4f}")
        print(f"Histogram: {indicators['histogram']:.4f}")
        print(f"Trend: {indicators['trend']}")
    
    # Test Momentum Strategy
    print("\n" + "="*60)
    print("Testing Momentum Strategy")
    print("="*60)
    
    momentum_strategy = MomentumStrategy(period=10, threshold=0.02)
    signal = momentum_strategy.generate_signal(data)
    print(f"Signal: {signal}")
    
    indicators = momentum_strategy.get_indicator_values(data)
    if indicators:
        print(f"Momentum: {indicators['momentum']:.2%}")
        print(f"Condition: {indicators['condition']}")
    
    # Test Strategy Manager with All Strategies
    print("\n" + "="*60)
    print("Testing Strategy Manager (All Strategies Combined)")
    print("="*60)
    
    manager = StrategyManager()
    manager.add_strategy(SMAStrategy(fast_period=10, slow_period=30), weight=1.0)
    manager.add_strategy(BollingerBandsStrategy(period=20, num_std=2.0), weight=1.0)
    manager.add_strategy(RSIStrategy(period=14), weight=0.8)
    manager.add_strategy(MACDStrategy(), weight=0.8)
    manager.add_strategy(MomentumStrategy(period=10), weight=0.6)
    
    combined_signal = manager.generate_combined_signal(data)
    print(f"\nCombined Signal: {combined_signal}")
    
    all_indicators = manager.get_all_indicator_values(data)
    print("\nAll Indicators:")
    for strategy_name, indicators in all_indicators.items():
        print(f"\n{strategy_name}:")
        for key, value in indicators.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Strategies module initialized successfully")
    print(f"Available strategies: SMA, Bollinger Bands, RSI, MACD, Momentum")
    print("="*60)
