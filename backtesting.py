#!/usr/bin/env python3
"""
Backtesting module for the trading bot
Provides historical data analysis and performance testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Import risk-free rate from main module
try:
    from main import BOT_RISK_FREE_RATE
except ImportError:
    # If main not available, use default
    BOT_RISK_FREE_RATE = 0.0


class Backtester:
    """
    Backtesting framework for testing trading strategies on historical data
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.results = []
        self.baseline_results = []
    
    def _extract_pnl_values(self, trades: List[Dict]) -> List[float]:
        """
        Extract P&L values from trades, handling both dict and direct value formats
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            List of P&L values as floats
        """
        pnl_values = []
        for t in trades:
            if 'pnl' in t:
                pnl = t['pnl']
                # Handle nested dict format (from run_backtest)
                if isinstance(pnl, dict):
                    pnl_values.append(pnl.get('pnl', 0))
                # Handle direct value format (from run_swing_backtest)
                else:
                    pnl_values.append(float(pnl))
        return pnl_values
        
    def generate_historical_data(self, symbol: str, days: int = 100, 
                                 start_price: float = 100.0, 
                                 volatility: float = 0.02) -> pd.DataFrame:
        """
        Generate synthetic historical price data for backtesting
        
        Args:
            symbol: Stock symbol
            days: Number of days of data
            start_price: Starting price
            volatility: Daily volatility (standard deviation)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        dates = [datetime.now() - timedelta(days=days-i) for i in range(days)]
        
        # Generate random walks for price
        returns = np.random.normal(0, volatility, days)
        prices = [start_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate OHLC data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Add some randomness to OHLC
            daily_range = close * volatility
            high = close + np.random.uniform(0, daily_range)
            low = close - np.random.uniform(0, daily_range)
            open_price = low + np.random.uniform(0, high - low)
            volume = int(np.random.uniform(500000, 5000000))
            
            data.append({
                'symbol': symbol,
                'date': date.strftime('%Y-%m-%d'),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def load_historical_data(self, csv_file: str) -> pd.DataFrame:
        """
        Load historical data from CSV file
        Expected columns: symbol, date, open, high, low, close, volume
        """
        try:
            df = pd.read_csv(csv_file)
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            
            required_cols = ['date', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"[ERROR] Missing required columns: {', '.join(missing_cols)}")
                return pd.DataFrame()
            
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            return df
        except Exception as e:
            print(f"[ERROR] Failed to load historical data: {str(e)}")
            return pd.DataFrame()
    
    def fetch_historical_data_yfinance(self, symbol: str, period: str = '1y') -> pd.DataFrame:
        """
        Fetch historical data from yfinance for backtesting
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period ('1y', '2y', '5y', '1mo', '3mo', '6mo')
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            import yfinance as yf
            
            print(f"[INFO] Fetching historical data for {symbol} ({period})...")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                print(f"[WARNING] No data returned for {symbol}")
                return pd.DataFrame()
            
            # Prepare data in expected format
            df = pd.DataFrame({
                'symbol': symbol,
                'date': hist.index.strftime('%Y-%m-%d'),
                'open': hist['Open'].values,
                'high': hist['High'].values,
                'low': hist['Low'].values,
                'close': hist['Close'].values,
                'volume': hist['Volume'].values
            })
            
            print(f"[INFO] Fetched {len(df)} days of data for {symbol}")
            return df
            
        except ImportError:
            print("[ERROR] yfinance not available. Install with: pip install yfinance")
            return pd.DataFrame()
        except Exception as e:
            print(f"[ERROR] Failed to fetch data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def run_backtest(self, bot, historical_data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data using the trading bot
        
        Args:
            bot: TradingBot instance
            historical_data: DataFrame with historical price data
        
        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'='*60}")
        print("BACKTEST STARTED")
        print(f"{'='*60}")
        print(f"Initial Capital: ${self.initial_capital:.2f}")
        print(f"Data Points: {len(historical_data)}")
        print(f"Date Range: {historical_data['date'].min()} to {historical_data['date'].max()}")
        
        trades = []
        starting_capital = self.initial_capital
        
        for idx, row in historical_data.iterrows():
            symbol = row.get('symbol', 'TEST')
            price = row['close']
            volume = row.get('volume', 1000000)
            date = row['date']
            
            # Update price history for the bot
            bot.update_price_history(symbol, price)
            
            # Simple strategy: buy if we don't have position, check stops if we do
            if symbol not in bot.positions:
                # Try to open position
                result = bot.execute_trade_paper_mode(symbol, 'BUY', price, volume)
                
                if result.get('status') == 'simulated':
                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': price,
                        'result': result
                    })
            else:
                # Check trailing stop
                stop_triggered = bot.check_trailing_stop(symbol, price)
                
                if stop_triggered and stop_triggered != 'partial_exit':
                    # Position closed by trailing stop
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': price,
                        'triggered_by': 'trailing_stop'
                    })
        
        # Close any remaining positions
        for symbol in list(bot.positions.keys()):
            symbol_data = historical_data[historical_data['symbol'] == symbol]
            if len(symbol_data) > 0:
                final_price = symbol_data['close'].iloc[-1]
            else:
                # If no data for this symbol, use last available price from any row
                final_price = historical_data['close'].iloc[-1]
            
            pnl_info = bot.close_position(symbol, final_price, exit_reason='backtest_end')
            trades.append({
                'date': historical_data['date'].iloc[-1],
                'action': 'SELL',
                'price': final_price,
                'triggered_by': 'backtest_end',
                'pnl': pnl_info
            })
        
        # Calculate results - use helper to extract P&L values
        total_pnl = sum(self._extract_pnl_values(trades))
        final_capital = starting_capital + total_pnl
        roi = (final_capital - starting_capital) / starting_capital
        
        results = {
            'initial_capital': starting_capital,
            'final_capital': final_capital,
            'total_pnl': total_pnl,
            'roi': roi,
            'total_trades': len(trades),
            'winning_trades': bot.track_record['winning_trades'],
            'losing_trades': bot.track_record['losing_trades'],
            'win_rate': bot.track_record['win_rate'],
            'trades': trades
        }
        
        self.results.append(results)
        
        print(f"\n{'='*60}")
        print("BACKTEST COMPLETED")
        print(f"{'='*60}")
        print(f"Initial Capital: ${starting_capital:.2f}")
        print(f"Final Capital: ${final_capital:.2f}")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"ROI: {roi:.2%}")
        print(f"Total Trades: {len(trades)}")
        print(f"Win Rate: {bot.track_record['win_rate']:.2%}")
        print(f"{'='*60}\n")
        
        return results
    
    def run_baseline(self, historical_data: pd.DataFrame) -> Dict:
        """
        Run baseline strategy (buy and hold) for comparison
        
        Args:
            historical_data: DataFrame with historical price data
        
        Returns:
            Dictionary with baseline results
        """
        print(f"\n{'='*60}")
        print("BASELINE (BUY & HOLD) STARTED")
        print(f"{'='*60}")
        
        start_price = historical_data['close'].iloc[0]
        end_price = historical_data['close'].iloc[-1]
        
        # Calculate how many shares we could buy with initial capital
        shares = self.initial_capital / start_price
        
        # Calculate final value
        final_value = shares * end_price
        total_pnl = final_value - self.initial_capital
        roi = total_pnl / self.initial_capital
        
        results = {
            'strategy': 'buy_and_hold',
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'total_pnl': total_pnl,
            'roi': roi,
            'shares': shares,
            'start_price': start_price,
            'end_price': end_price
        }
        
        self.baseline_results.append(results)
        
        print(f"Initial Capital: ${self.initial_capital:.2f}")
        print(f"Start Price: ${start_price:.2f}")
        print(f"End Price: ${end_price:.2f}")
        print(f"Shares Purchased: {shares:.6f}")
        print(f"Final Value: ${final_value:.2f}")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"ROI: {roi:.2%}")
        print(f"{'='*60}\n")
        
        return results
    
    def compare_with_baseline(self, backtest_result: Dict, baseline_result: Dict) -> Dict:
        """
        Compare backtest results with baseline (buy and hold)
        
        Returns:
            Dictionary with comparison metrics
        """
        print(f"\n{'='*60}")
        print("PERFORMANCE COMPARISON")
        print(f"{'='*60}")
        
        strategy_roi = backtest_result['roi']
        baseline_roi = baseline_result['roi']
        
        outperformance = strategy_roi - baseline_roi
        outperformance_pct = (outperformance / abs(baseline_roi)) * 100 if baseline_roi != 0 else 0
        
        comparison = {
            'strategy_roi': strategy_roi,
            'baseline_roi': baseline_roi,
            'outperformance': outperformance,
            'outperformance_pct': outperformance_pct,
            'strategy_pnl': backtest_result['total_pnl'],
            'baseline_pnl': baseline_result['total_pnl'],
            'strategy_wins': backtest_result['winning_trades'],
            'strategy_losses': backtest_result['losing_trades'],
            'strategy_win_rate': backtest_result['win_rate']
        }
        
        print(f"Strategy ROI: {strategy_roi:.2%}")
        print(f"Baseline ROI: {baseline_roi:.2%}")
        print(f"Outperformance: {outperformance:.2%} ({outperformance_pct:+.1f}%)")
        print(f"\nStrategy P&L: ${backtest_result['total_pnl']:.2f}")
        print(f"Baseline P&L: ${baseline_result['total_pnl']:.2f}")
        print(f"\nStrategy Trades: {backtest_result['total_trades']}")
        print(f"Strategy Win Rate: {backtest_result['win_rate']:.2%}")
        
        if outperformance > 0:
            print(f"\n✓ Strategy OUTPERFORMED baseline by {outperformance:.2%}")
        else:
            print(f"\n✗ Strategy UNDERPERFORMED baseline by {abs(outperformance):.2%}")
        
        print(f"{'='*60}\n")
        
        return comparison
    
    def calculate_rolling_metrics(self, trades: List[Dict], window: int = 10) -> Dict:
        """
        Calculate rolling metrics for trades
        
        Args:
            trades: List of trade dictionaries
            window: Window size for rolling calculations
            
        Returns:
            Dictionary with rolling metrics
        """
        if not trades or len(trades) < window:
            return {}
        
        # Extract P&L values - use helper method
        pnl_values = self._extract_pnl_values(trades)
        
        # Calculate rolling average P&L
        rolling_avg = []
        for i in range(len(pnl_values)):
            if i < window - 1:
                rolling_avg.append(np.mean(pnl_values[:i+1]))
            else:
                rolling_avg.append(np.mean(pnl_values[i-window+1:i+1]))
        
        # Calculate rolling win rate
        rolling_win_rate = []
        for i in range(len(trades)):
            if i < window - 1:
                window_trades = trades[:i+1]
            else:
                window_trades = trades[i-window+1:i+1]
            
            # Handle both dict and direct value formats for is_win
            wins = 0
            for t in window_trades:
                if 'is_win' in t:
                    # Direct format (from run_swing_backtest)
                    wins += 1 if t['is_win'] else 0
                elif 'pnl' in t:
                    # Nested dict format (from run_backtest)
                    pnl = t['pnl']
                    if isinstance(pnl, dict):
                        wins += 1 if pnl.get('is_win', False) else 0
            rolling_win_rate.append(wins / len(window_trades) if window_trades else 0)
        
        return {
            'rolling_avg_pnl': rolling_avg,
            'rolling_win_rate': rolling_win_rate,
            'window_size': window
        }
    
    def calculate_distribution_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate statistical distribution metrics
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Dictionary with distribution metrics
        """
        # Extract P&L values - use helper method
        pnl_values = self._extract_pnl_values(trades)
        
        if not pnl_values:
            return {}
        
        pnl_array = np.array(pnl_values)
        
        # Calculate percentiles
        percentiles = {
            'p25': np.percentile(pnl_array, 25),
            'p50': np.percentile(pnl_array, 50),  # median
            'p75': np.percentile(pnl_array, 75),
            'p90': np.percentile(pnl_array, 90),
            'p95': np.percentile(pnl_array, 95)
        }
        
        # Calculate moments
        mean = np.mean(pnl_array)
        std = np.std(pnl_array)
        
        # Skewness and kurtosis (simplified)
        centered = pnl_array - mean
        skewness = np.mean(centered**3) / (std**3) if std > 0 else 0
        kurtosis = np.mean(centered**4) / (std**4) if std > 0 else 0
        
        return {
            'mean': mean,
            'std': std,
            'percentiles': percentiles,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def calculate_sharpe_ratio(self, trades: List[Dict], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio from trades
        
        Args:
            trades: List of trade dictionaries
            risk_free_rate: Risk-free rate (annualized)
            
        Returns:
            Sharpe ratio
        """
        # Use helper to extract P&L values
        pnl_values = self._extract_pnl_values(trades)
        
        if not pnl_values or len(pnl_values) < 2:
            return 0.0
        
        returns = np.array(pnl_values)
        excess_returns = returns - risk_free_rate
        
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns)
        
        if std_return == 0:
            return 0.0
        
        return mean_return / std_return
    
    def calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """
        Calculate maximum drawdown from trades
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Maximum drawdown as a percentage
        """
        # Use helper to extract P&L values
        pnl_values = self._extract_pnl_values(trades)
        
        if not pnl_values:
            return 0.0
        
        # Calculate cumulative P&L
        cumulative = np.cumsum(pnl_values)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(cumulative)
        
        # Calculate drawdown
        drawdown = (running_max - cumulative) / np.maximum(running_max, 1)
        
        return np.max(drawdown)
    
    def run_swing_backtest(self, historical_data: pd.DataFrame, 
                          take_profit_pct: float = 0.10,
                          trailing_stop_pct: float = 0.03,
                          stop_loss_pct: float = 0.06,
                          min_hold_days: int = 2,
                          max_hold_days: int = 10,
                          capital: float = None) -> Dict:
        """
        Run swing trading backtest with "go back in time" methodology
        
        For each historical date, simulates entering a position and looks forward
        to see when it would exit (take profit, trailing stop, or stop loss).
        This tests buy-then-future-sell scenarios mimicking real swing trading.
        
        Args:
            historical_data: DataFrame with OHLC price data (columns: date, open, high, low, close, volume)
            take_profit_pct: Take profit percentage (default: 0.10 = 10%)
            trailing_stop_pct: Trailing stop percentage (default: 0.03 = 3%)
            stop_loss_pct: Stop loss percentage (default: 0.06 = 6%)
            min_hold_days: Minimum holding period in days (default: 2)
            max_hold_days: Maximum holding period in days (default: 10)
            capital: Starting capital (uses self.initial_capital if None)
            
        Returns:
            Dictionary with swing backtest results including win rate stats
        """
        if capital is None:
            capital = self.initial_capital
        
        print(f"\n{'='*60}")
        print("SWING TRADING BACKTEST STARTED")
        print(f"{'='*60}")
        print(f"Initial Capital: ${capital:.2f}")
        print(f"Data Points: {len(historical_data)}")
        print(f"Date Range: {historical_data['date'].min()} to {historical_data['date'].max()}")
        print(f"Take Profit: {take_profit_pct:.1%}")
        print(f"Trailing Stop: {trailing_stop_pct:.1%}")
        print(f"Stop Loss: {stop_loss_pct:.1%}")
        print(f"Hold Period: {min_hold_days}-{max_hold_days} days")
        
        # Ensure data is sorted by date
        historical_data = historical_data.sort_values('date').reset_index(drop=True)
        
        trades = []
        current_capital = capital
        
        # Iterate through each date as potential entry point
        for entry_idx in range(len(historical_data) - max_hold_days):
            entry_date = historical_data['date'].iloc[entry_idx]
            entry_price = historical_data['close'].iloc[entry_idx]
            # Safe symbol extraction
            symbol = historical_data['symbol'].iloc[entry_idx] if 'symbol' in historical_data.columns else 'TEST'
            
            # Calculate position size (simple: 10% of capital per trade)
            position_size_capital = current_capital * 0.10
            shares = position_size_capital / entry_price
            
            # Set exit thresholds
            take_profit_price = entry_price * (1 + take_profit_pct)
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            high_water_mark = entry_price
            
            # Look forward to find exit
            exit_idx = None
            exit_price = None
            exit_reason = None
            exit_date = None
            
            for future_idx in range(entry_idx + min_hold_days, min(entry_idx + max_hold_days + 1, len(historical_data))):
                future_date = historical_data['date'].iloc[future_idx]
                future_high = historical_data['high'].iloc[future_idx]
                future_low = historical_data['low'].iloc[future_idx]
                # Update high water mark for trailing stop
                high_water_mark = max(high_water_mark, future_high)
                trailing_stop_price = high_water_mark * (1 - trailing_stop_pct)
                
                # Check exit conditions (order matters for realism)
                # 1. Check if stop loss hit (highest priority)
                if future_low <= stop_loss_price:
                    exit_idx = future_idx
                    # Use max() to simulate potential negative slippage (worse execution)
                    exit_price = max(future_low, stop_loss_price)
                    exit_reason = 'stop_loss'
                    exit_date = future_date
                    break
                
                # 2. Check if take profit hit
                if future_high >= take_profit_price:
                    exit_idx = future_idx
                    # Use min() to simulate potential negative slippage (worse execution)
                    exit_price = min(future_high, take_profit_price)
                    exit_reason = 'take_profit'
                    exit_date = future_date
                    break
                
                # 3. Check if trailing stop hit
                if future_low <= trailing_stop_price:
                    exit_idx = future_idx
                    # Use max() to simulate potential negative slippage
                    exit_price = max(future_low, trailing_stop_price)
                    exit_reason = 'trailing_stop'
                    exit_date = future_date
                    break
            
            # If no exit found within max hold period, exit at end
            if exit_idx is None:
                exit_idx = min(entry_idx + max_hold_days, len(historical_data) - 1)
                exit_price = historical_data['close'].iloc[exit_idx]
                exit_date = historical_data['date'].iloc[exit_idx]
                exit_reason = 'max_hold_period'
            
            # Calculate trade P&L
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price - entry_price) / entry_price
            is_win = pnl > 0
            holding_days = exit_idx - entry_idx
            
            # Update capital
            current_capital += pnl
            
            # Record trade
            trade = {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'shares': shares,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'is_win': is_win,
                'holding_days': holding_days,
                'symbol': symbol,
                'high_water_mark': high_water_mark
            }
            trades.append(trade)
        
        # Calculate statistics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['is_win'])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_win = np.mean([t['pnl'] for t in trades if t['is_win']]) if winning_trades > 0 else 0.0
        avg_loss = np.mean([t['pnl'] for t in trades if not t['is_win']]) if losing_trades > 0 else 0.0
        
        # Calculate profit factor (gross profit / gross loss)
        gross_profit = sum(t['pnl'] for t in trades if t['is_win'])
        gross_loss = abs(sum(t['pnl'] for t in trades if not t['is_win']))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate average holding period
        avg_holding_days = np.mean([t['holding_days'] for t in trades]) if trades else 0.0
        
        # Calculate average risk/reward
        avg_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        
        # Compile results
        results = {
            'initial_capital': capital,
            'final_capital': current_capital,
            'total_pnl': total_pnl,
            'roi': (current_capital - capital) / capital,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_holding_days': avg_holding_days,
            'avg_risk_reward': avg_rr,
            'trades': trades,
            'parameters': {
                'take_profit_pct': take_profit_pct,
                'trailing_stop_pct': trailing_stop_pct,
                'stop_loss_pct': stop_loss_pct,
                'min_hold_days': min_hold_days,
                'max_hold_days': max_hold_days
            }
        }
        
        self.results.append(results)
        
        # Print summary
        print(f"\n{'='*60}")
        print("SWING TRADING BACKTEST COMPLETED")
        print(f"{'='*60}")
        print(f"Initial Capital: ${capital:.2f}")
        print(f"Final Capital: ${current_capital:.2f}")
        print(f"Total P&L: ${total_pnl:+.2f}")
        print(f"ROI: {results['roi']:+.2%}")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2%} {'✓' if win_rate >= 0.70 else '✗'} (Target: 70%)")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Avg Win: ${avg_win:.2f}")
        print(f"Avg Loss: ${avg_loss:.2f}")
        print(f"Avg Risk/Reward: 1:{avg_rr:.2f}")
        print(f"Avg Holding Period: {avg_holding_days:.1f} days")
        print(f"{'='*60}\n")
        
        return results
    
    def generate_report(self, output_file: str = 'backtest_report.json'):
        """
        Generate a comprehensive backtest report with enhanced analytics
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'backtest_results': self.results,
            'baseline_results': self.baseline_results
        }
        
        # Add comparison if we have both results
        if self.results and self.baseline_results:
            report['comparison'] = self.compare_with_baseline(
                self.results[0], 
                self.baseline_results[0]
            )
        
        # Enhanced analytics for backtest results
        if self.results:
            for i, result in enumerate(self.results):
                trades = result.get('trades', [])
                
                # Calculate rolling metrics
                rolling_metrics = self.calculate_rolling_metrics(trades, window=10)
                result['rolling_metrics'] = rolling_metrics
                
                # Calculate distribution metrics
                distribution = self.calculate_distribution_metrics(trades)
                result['distribution_metrics'] = distribution
                
                # Calculate Sharpe ratio
                sharpe = self.calculate_sharpe_ratio(trades, risk_free_rate=BOT_RISK_FREE_RATE)
                result['sharpe_ratio'] = sharpe
                
                # Calculate max drawdown
                max_dd = self.calculate_max_drawdown(trades)
                result['max_drawdown'] = max_dd
                
                print(f"\n[ENHANCED ANALYTICS - Run {i+1}]")
                print(f"  Sharpe Ratio: {sharpe:.3f}")
                print(f"  Max Drawdown: {max_dd:.2%}")
                if distribution:
                    print(f"  Mean P&L: ${distribution['mean']:.2f}")
                    print(f"  Std Dev P&L: ${distribution['std']:.2f}")
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n[REPORT GENERATED] Saved to {output_file}")
        
        return report


if __name__ == "__main__":
    # Example usage
    from main import TradingBot
    
    print("Backtesting Module - Example Usage")
    print("="*60)
    
    # Create backtester
    backtester = Backtester(initial_capital=10000.0)
    
    # Example 1: Traditional forward simulation backtest
    print("\n[EXAMPLE 1] Traditional Forward Simulation Backtest")
    print("="*60)
    
    # Generate historical data
    historical_data = backtester.generate_historical_data(
        symbol='TEST',
        days=100,
        start_price=100.0,
        volatility=0.02
    )
    
    print(f"\nGenerated {len(historical_data)} days of historical data")
    print(f"Price range: ${historical_data['close'].min():.2f} - ${historical_data['close'].max():.2f}")
    
    # Create trading bot
    bot = TradingBot(total_capital=10000.0)
    
    # Run backtest
    backtest_result = backtester.run_backtest(bot, historical_data)
    
    # Run baseline
    baseline_result = backtester.run_baseline(historical_data)
    
    # Compare
    comparison = backtester.compare_with_baseline(backtest_result, baseline_result)
    
    # Example 2: Swing Trading Backtest (NEW!)
    print("\n[EXAMPLE 2] Swing Trading Backtest (Go Back in Time)")
    print("="*60)
    
    # Generate data with better OHLC characteristics
    swing_data = backtester.generate_historical_data(
        symbol='SWING_TEST',
        days=100,
        start_price=150.0,
        volatility=0.03
    )
    
    # Run swing backtest
    swing_result = backtester.run_swing_backtest(
        historical_data=swing_data,
        take_profit_pct=0.10,     # 10% take profit
        trailing_stop_pct=0.03,   # 3% trailing stop
        stop_loss_pct=0.06,       # 6% stop loss
        min_hold_days=2,          # Minimum 2-day hold
        max_hold_days=10,         # Maximum 10-day hold
        capital=10000.0
    )
    
    # Example 3: Testing with real data from yfinance
    print("\n[EXAMPLE 3] Real Data from yfinance (if available)")
    print("="*60)
    
    try:
        # Fetch real data for a popular stock
        real_data = backtester.fetch_historical_data_yfinance('AAPL', period='1y')
        
        if not real_data.empty:
            print(f"\nFetched {len(real_data)} days of AAPL data")
            
            # Run swing backtest on real data
            real_swing_result = backtester.run_swing_backtest(
                historical_data=real_data,
                take_profit_pct=0.08,
                trailing_stop_pct=0.04,
                stop_loss_pct=0.05,
                min_hold_days=3,
                max_hold_days=15,
                capital=10000.0
            )
            
            print(f"\nReal data backtest win rate: {real_swing_result['win_rate']:.2%}")
        else:
            print("[INFO] Could not fetch real data, skipping real data example")
            
    except Exception as e:
        print(f"[INFO] Skipping real data example: {str(e)}")
    
    # Generate comprehensive report
    print("\n[GENERATING REPORT]")
    backtester.generate_report('backtest_report.json')
    
    print("\n" + "="*60)
    print("Backtesting examples completed!")
    print("Review backtest_report.json for detailed results")
    print("="*60)
