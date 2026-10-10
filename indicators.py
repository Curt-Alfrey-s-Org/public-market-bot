#!/usr/bin/env python3
"""
Technical Indicators Module for market-pie5-bot
Uses pandas-ta for calculating technical indicators including:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- SMA (Simple Moving Average)
- Bollinger Bands
- Additional momentum and trend indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import pandas_ta, fall back to manual calculations if not available
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
    logger.info("pandas-ta library loaded successfully")
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas-ta not available - using manual indicator calculations")


class TechnicalIndicators:
    """
    Technical indicators calculator with support for both pandas-ta and manual calculations
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with price data
        
        Args:
            data: DataFrame with OHLCV data (open, high, low, close, volume)
        """
        self.data = data.copy()
        logger.debug(f"Initialized TechnicalIndicators with {len(data)} data points")
    
    def calculate_rsi(self, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI measures momentum and identifies overbought/oversold conditions
        - RSI > 70: Overbought (potential sell signal)
        - RSI < 30: Oversold (potential buy signal)
        
        Args:
            period: RSI period (default: 14)
            column: Column to calculate RSI on (default: 'close')
            
        Returns:
            Series with RSI values
        """
        if PANDAS_TA_AVAILABLE:
            rsi = ta.rsi(self.data[column], length=period)
        else:
            # Manual RSI calculation
            delta = self.data[column].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"Calculated RSI (period={period})")
        return rsi
    
    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9, 
                       column: str = 'close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        MACD is a trend-following momentum indicator
        - MACD line crosses above signal: Bullish (buy signal)
        - MACD line crosses below signal: Bearish (sell signal)
        
        Args:
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            column: Column to calculate MACD on (default: 'close')
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        if PANDAS_TA_AVAILABLE:
            macd_df = ta.macd(self.data[column], fast=fast, slow=slow, signal=signal)
            macd_line = macd_df[f'MACD_{fast}_{slow}_{signal}']
            signal_line = macd_df[f'MACDs_{fast}_{slow}_{signal}']
            histogram = macd_df[f'MACDh_{fast}_{slow}_{signal}']
        else:
            # Manual MACD calculation
            ema_fast = self.data[column].ewm(span=fast, adjust=False).mean()
            ema_slow = self.data[column].ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
        
        logger.debug(f"Calculated MACD (fast={fast}, slow={slow}, signal={signal})")
        return macd_line, signal_line, histogram
    
    def calculate_sma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Calculate Simple Moving Average (SMA)
        
        Args:
            period: SMA period (default: 20)
            column: Column to calculate SMA on (default: 'close')
            
        Returns:
            Series with SMA values
        """
        if PANDAS_TA_AVAILABLE:
            sma = ta.sma(self.data[column], length=period)
        else:
            # Manual SMA calculation
            sma = self.data[column].rolling(window=period).mean()
        
        logger.debug(f"Calculated SMA (period={period})")
        return sma
    
    def calculate_ema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA)
        
        Args:
            period: EMA period (default: 20)
            column: Column to calculate EMA on (default: 'close')
            
        Returns:
            Series with EMA values
        """
        if PANDAS_TA_AVAILABLE:
            ema = ta.ema(self.data[column], length=period)
        else:
            # Manual EMA calculation
            ema = self.data[column].ewm(span=period, adjust=False).mean()
        
        logger.debug(f"Calculated EMA (period={period})")
        return ema
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0,
                                   column: str = 'close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Bollinger Bands show volatility and potential reversal points
        - Price at upper band: Overbought
        - Price at lower band: Oversold
        
        Args:
            period: Period for moving average (default: 20)
            std_dev: Number of standard deviations (default: 2.0)
            column: Column to calculate bands on (default: 'close')
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        if PANDAS_TA_AVAILABLE:
            bb_df = ta.bbands(self.data[column], length=period, std=std_dev)
            # pandas-ta uses format: BBU_20_2.0_2.0, BBM_20_2.0_2.0, BBL_20_2.0_2.0
            upper = bb_df[f'BBU_{period}_{std_dev}_{std_dev}']
            middle = bb_df[f'BBM_{period}_{std_dev}_{std_dev}']
            lower = bb_df[f'BBL_{period}_{std_dev}_{std_dev}']
        else:
            # Manual Bollinger Bands calculation
            middle = self.data[column].rolling(window=period).mean()
            std = self.data[column].rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
        
        logger.debug(f"Calculated Bollinger Bands (period={period}, std={std_dev})")
        return upper, middle, lower
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        ATR measures market volatility
        - High ATR: High volatility
        - Low ATR: Low volatility
        
        Args:
            period: ATR period (default: 14)
            
        Returns:
            Series with ATR values
        """
        if PANDAS_TA_AVAILABLE and all(col in self.data.columns for col in ['high', 'low', 'close']):
            atr = ta.atr(self.data['high'], self.data['low'], self.data['close'], length=period)
        else:
            # Manual ATR calculation
            if not all(col in self.data.columns for col in ['high', 'low', 'close']):
                logger.warning("ATR requires high, low, close columns - returning None")
                return pd.Series(dtype=float)
            
            high_low = self.data['high'] - self.data['low']
            high_close = np.abs(self.data['high'] - self.data['close'].shift())
            low_close = np.abs(self.data['low'] - self.data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
        
        logger.debug(f"Calculated ATR (period={period})")
        return atr
    
    def calculate_adx(self, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index (ADX)
        
        ADX measures trend strength (not direction)
        - ADX > 25: Strong trend
        - ADX < 20: Weak trend
        
        Args:
            period: ADX period (default: 14)
            
        Returns:
            Series with ADX values
        """
        if PANDAS_TA_AVAILABLE and all(col in self.data.columns for col in ['high', 'low', 'close']):
            adx_df = ta.adx(self.data['high'], self.data['low'], self.data['close'], length=period)
            adx = adx_df[f'ADX_{period}']
        else:
            # Simplified ADX calculation (full implementation is complex)
            if not all(col in self.data.columns for col in ['high', 'low', 'close']):
                logger.warning("ADX requires high, low, close columns - returning None")
                return pd.Series(dtype=float)
            
            # This is a simplified version - use pandas_ta for accurate ADX
            high_diff = self.data['high'].diff()
            low_diff = -self.data['low'].diff()
            
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
            
            atr = self.calculate_atr(period)
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            
            # Avoid division by zero when plus_di + minus_di is zero or close to zero
            denominator = plus_di + minus_di
            # Replace zeros and very small values with NaN to avoid invalid calculations
            denominator = denominator.replace(0, np.nan)
            dx = 100 * np.abs(plus_di - minus_di) / denominator
            adx = dx.rolling(window=period).mean()
        
        logger.debug(f"Calculated ADX (period={period})")
        return adx
    
    def calculate_stochastic(self, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator
        
        Stochastic shows momentum and identifies overbought/oversold
        - %K > 80: Overbought
        - %K < 20: Oversold
        
        Args:
            k_period: %K period (default: 14)
            d_period: %D period (default: 3)
            
        Returns:
            Tuple of (%K, %D)
        """
        if PANDAS_TA_AVAILABLE and all(col in self.data.columns for col in ['high', 'low', 'close']):
            stoch_df = ta.stoch(self.data['high'], self.data['low'], self.data['close'], 
                               k=k_period, d=d_period)
            k = stoch_df[f'STOCHk_{k_period}_{d_period}_3']
            d = stoch_df[f'STOCHd_{k_period}_{d_period}_3']
        else:
            # Manual Stochastic calculation
            if not all(col in self.data.columns for col in ['high', 'low', 'close']):
                logger.warning("Stochastic requires high, low, close columns - returning None")
                return pd.Series(dtype=float), pd.Series(dtype=float)
            
            low_min = self.data['low'].rolling(window=k_period).min()
            high_max = self.data['high'].rolling(window=k_period).max()
            
            k = 100 * (self.data['close'] - low_min) / (high_max - low_min)
            d = k.rolling(window=d_period).mean()
        
        logger.debug(f"Calculated Stochastic (k={k_period}, d={d_period})")
        return k, d
    
    def get_all_indicators(self) -> Dict:
        """
        Calculate all available indicators and return as dictionary
        
        Returns:
            Dictionary with all calculated indicators
        """
        indicators = {}
        
        try:
            # Trend indicators
            indicators['sma_20'] = self.calculate_sma(period=20)
            indicators['sma_50'] = self.calculate_sma(period=50)
            indicators['ema_12'] = self.calculate_ema(period=12)
            indicators['ema_26'] = self.calculate_ema(period=26)
            
            # Momentum indicators
            indicators['rsi_14'] = self.calculate_rsi(period=14)
            
            macd_line, signal_line, histogram = self.calculate_macd()
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
            
            # Volatility indicators
            upper, middle, lower = self.calculate_bollinger_bands()
            indicators['bb_upper'] = upper
            indicators['bb_middle'] = middle
            indicators['bb_lower'] = lower
            
            if all(col in self.data.columns for col in ['high', 'low', 'close']):
                indicators['atr_14'] = self.calculate_atr(period=14)
                indicators['adx_14'] = self.calculate_adx(period=14)
                
                k, d = self.calculate_stochastic()
                indicators['stoch_k'] = k
                indicators['stoch_d'] = d
            
            logger.info(f"Calculated {len(indicators)} technical indicators")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators
    
    def get_latest_values(self) -> Dict:
        """
        Get the latest value of all indicators
        
        Returns:
            Dictionary with latest indicator values
        """
        indicators = self.get_all_indicators()
        latest = {}
        
        for name, series in indicators.items():
            if isinstance(series, pd.Series) and len(series) > 0:
                latest[name] = series.iloc[-1]
        
        logger.debug(f"Retrieved latest values for {len(latest)} indicators")
        return latest
    
    def interpret_indicators(self) -> Dict:
        """
        Interpret indicators and provide trading insights
        
        Returns:
            Dictionary with interpretations and signals
        """
        latest = self.get_latest_values()
        interpretations = {}
        
        # RSI interpretation
        if 'rsi_14' in latest and not pd.isna(latest['rsi_14']):
            rsi = latest['rsi_14']
            if rsi > 70:
                interpretations['rsi'] = {'value': rsi, 'signal': 'OVERBOUGHT', 'action': 'SELL'}
            elif rsi < 30:
                interpretations['rsi'] = {'value': rsi, 'signal': 'OVERSOLD', 'action': 'BUY'}
            else:
                interpretations['rsi'] = {'value': rsi, 'signal': 'NEUTRAL', 'action': 'HOLD'}
        
        # MACD interpretation
        if all(k in latest for k in ['macd_line', 'macd_signal']):
            macd = latest['macd_line']
            signal = latest['macd_signal']
            
            if not pd.isna(macd) and not pd.isna(signal):
                if macd > signal:
                    interpretations['macd'] = {'macd': macd, 'signal': signal, 
                                              'position': 'BULLISH', 'action': 'BUY'}
                else:
                    interpretations['macd'] = {'macd': macd, 'signal': signal,
                                              'position': 'BEARISH', 'action': 'SELL'}
        
        # Bollinger Bands interpretation
        if all(k in latest for k in ['bb_upper', 'bb_middle', 'bb_lower']) and 'close' in self.data.columns:
            price = self.data['close'].iloc[-1]
            upper = latest['bb_upper']
            middle = latest['bb_middle']
            lower = latest['bb_lower']
            
            if not any(pd.isna(v) for v in [price, upper, middle, lower]):
                if price >= upper:
                    interpretations['bollinger'] = {'price': price, 'position': 'OVERBOUGHT', 'action': 'SELL'}
                elif price <= lower:
                    interpretations['bollinger'] = {'price': price, 'position': 'OVERSOLD', 'action': 'BUY'}
                else:
                    interpretations['bollinger'] = {'price': price, 'position': 'NEUTRAL', 'action': 'HOLD'}
        
        # Stochastic interpretation
        if 'stoch_k' in latest and not pd.isna(latest['stoch_k']):
            stoch_k = latest['stoch_k']
            if stoch_k > 80:
                interpretations['stochastic'] = {'k': stoch_k, 'signal': 'OVERBOUGHT', 'action': 'SELL'}
            elif stoch_k < 20:
                interpretations['stochastic'] = {'k': stoch_k, 'signal': 'OVERSOLD', 'action': 'BUY'}
            else:
                interpretations['stochastic'] = {'k': stoch_k, 'signal': 'NEUTRAL', 'action': 'HOLD'}
        
        logger.info(f"Generated interpretations for {len(interpretations)} indicators")
        return interpretations


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Technical Indicators Module - Example Usage")
    print("="*60)
    print(f"pandas-ta available: {PANDAS_TA_AVAILABLE}")
    
    # Generate sample OHLCV data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.normal(0, 2, 100)
    close_prices = base_price + trend + noise
    
    # Generate OHLC from close
    open_prices = close_prices + np.random.normal(0, 0.5, 100)
    high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 1, 100)
    low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 1, 100)
    volumes = np.random.randint(1000000, 5000000, 100)
    
    data = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })
    
    print(f"\nGenerated {len(data)} days of sample OHLCV data")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Initialize indicators
    print("\n" + "="*60)
    print("Calculating Technical Indicators")
    print("="*60)
    
    indicators = TechnicalIndicators(data)
    
    # Calculate all indicators
    all_indicators = indicators.get_all_indicators()
    print(f"\nCalculated {len(all_indicators)} indicators")
    
    # Get latest values
    latest = indicators.get_latest_values()
    print("\nLatest Indicator Values:")
    for name, value in latest.items():
        if not pd.isna(value):
            print(f"  {name}: {value:.4f}")
    
    # Get interpretations
    print("\n" + "="*60)
    print("Indicator Interpretations")
    print("="*60)
    
    interpretations = indicators.interpret_indicators()
    for indicator_name, interpretation in interpretations.items():
        print(f"\n{indicator_name.upper()}:")
        for key, value in interpretation.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Technical Indicators module initialized successfully")
    print("="*60)
