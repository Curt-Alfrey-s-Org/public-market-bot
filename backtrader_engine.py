#!/usr/bin/env python3
"""
Enhanced Backtrader Integration for market-pie5-bot
Provides advanced backtesting with Backtrader framework
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import backtrader
try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
    logger.info("Backtrader library loaded successfully")
except ImportError:
    BACKTRADER_AVAILABLE = False
    logger.warning("Backtrader not available - using fallback backtesting")


class BacktraderStrategy(bt.Strategy if BACKTRADER_AVAILABLE else object):
    """
    Base Backtrader strategy with risk management
    """
    
    params = (
        ('risk_per_trade', 0.02),  # 2% risk per trade
        ('stop_loss_pct', 0.03),   # 3% stop loss
        ('take_profit_pct', 0.06), # 6% take profit (2:1 reward/risk)
        ('trailing_stop_pct', 0.03), # 3% trailing stop
    )
    
    def __init__(self):
        if not BACKTRADER_AVAILABLE:
            return
        
        self.order = None
        self.entry_price = None
        self.high_since_entry = None
        self.trades = []
        
        logger.info("Initialized BacktraderStrategy")
    
    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.debug(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if not BACKTRADER_AVAILABLE:
            return
        
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
                self.high_since_entry = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                
                # Calculate P&L
                if self.entry_price:
                    pnl = order.executed.price - self.entry_price
                    pnl_pct = (pnl / self.entry_price) * 100
                    
                    self.trades.append({
                        'entry': self.entry_price,
                        'exit': order.executed.price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'date': self.datas[0].datetime.date(0)
                    })
                    
                    self.log(f'P&L: {pnl:.2f} ({pnl_pct:.2f}%)')
                    
                self.entry_price = None
                self.high_since_entry = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not BACKTRADER_AVAILABLE:
            return
        
        if not trade.isclosed:
            return
        
        self.log(f'OPERATION PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}')


class SMABacktraderStrategy(BacktraderStrategy if BACKTRADER_AVAILABLE else object):
    """
    SMA Crossover strategy for Backtrader
    """
    
    params = (
        ('fast_period', 20),
        ('slow_period', 50),
        ('risk_per_trade', 0.02),
        ('stop_loss_pct', 0.03),
    )
    
    def __init__(self):
        if not BACKTRADER_AVAILABLE:
            return
        
        super().__init__()
        
        # Add indicators
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.fast_period)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.slow_period)
        
        # Crossover signal
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        
        logger.info(f"Initialized SMA strategy (fast={self.params.fast_period}, slow={self.params.slow_period})")
    
    def next(self):
        """Called for each new data point"""
        if not BACKTRADER_AVAILABLE:
            return
        
        # Check if order is pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Golden cross: BUY signal
            if self.crossover > 0:
                # Calculate position size based on risk
                size = self.calculate_position_size()
                
                self.log(f'BUY CREATE, {self.datas[0].close[0]:.2f}, size={size}')
                self.order = self.buy(size=size)
        
        else:
            # Update trailing stop
            current_price = self.datas[0].close[0]
            
            if current_price > self.high_since_entry:
                self.high_since_entry = current_price
            
            # Check trailing stop
            trailing_stop_price = self.high_since_entry * (1 - self.params.trailing_stop_pct)
            
            if current_price <= trailing_stop_price:
                self.log(f'SELL CREATE (Trailing Stop), {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # Death cross: SELL signal
            elif self.crossover < 0:
                self.log(f'SELL CREATE (Death Cross), {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
    
    def calculate_position_size(self):
        """Calculate position size based on risk management"""
        if not BACKTRADER_AVAILABLE:
            return 0
        
        # Simple fixed percentage of capital
        cash = self.broker.getcash()
        risk_amount = cash * self.params.risk_per_trade
        
        # Calculate shares based on stop loss
        current_price = self.datas[0].close[0]
        stop_loss_price = current_price * (1 - self.params.stop_loss_pct)
        risk_per_share = current_price - stop_loss_price
        
        if risk_per_share > 0:
            shares = int(risk_amount / risk_per_share)
        else:
            shares = int(cash * 0.1 / current_price)  # Fallback: 10% of capital
        
        return max(1, shares)


class BollingerBacktraderStrategy(BacktraderStrategy if BACKTRADER_AVAILABLE else object):
    """
    Bollinger Bands strategy for Backtrader
    """
    
    params = (
        ('period', 20),
        ('devfactor', 2.0),
        ('risk_per_trade', 0.02),
        ('stop_loss_pct', 0.03),
    )
    
    def __init__(self):
        if not BACKTRADER_AVAILABLE:
            return
        
        super().__init__()
        
        # Add Bollinger Bands indicator
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0].close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        
        logger.info(f"Initialized Bollinger Bands strategy (period={self.params.period}, std={self.params.devfactor})")
    
    def next(self):
        """Called for each new data point"""
        if not BACKTRADER_AVAILABLE:
            return
        
        # Check if order is pending
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        # Check if we are in the market
        if not self.position:
            # Price crosses below lower band: BUY signal (oversold)
            if current_price < self.bbands.lines.bot[0]:
                size = self.calculate_position_size()
                
                self.log(f'BUY CREATE (Oversold), {current_price:.2f}, size={size}')
                self.order = self.buy(size=size)
        
        else:
            # Update trailing stop
            if current_price > self.high_since_entry:
                self.high_since_entry = current_price
            
            # Check trailing stop
            trailing_stop_price = self.high_since_entry * (1 - self.params.trailing_stop_pct)
            
            if current_price <= trailing_stop_price:
                self.log(f'SELL CREATE (Trailing Stop), {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # Price crosses above upper band: SELL signal (overbought)
            elif current_price > self.bbands.lines.top[0]:
                self.log(f'SELL CREATE (Overbought), {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
    
    def calculate_position_size(self):
        """Calculate position size based on risk management"""
        if not BACKTRADER_AVAILABLE:
            return 0
        
        # Simple fixed percentage of capital
        cash = self.broker.getcash()
        risk_amount = cash * self.params.risk_per_trade
        
        # Calculate shares based on stop loss
        current_price = self.datas[0].close[0]
        stop_loss_price = current_price * (1 - self.params.stop_loss_pct)
        risk_per_share = current_price - stop_loss_price
        
        if risk_per_share > 0:
            shares = int(risk_amount / risk_per_share)
        else:
            shares = int(cash * 0.1 / current_price)  # Fallback: 10% of capital
        
        return max(1, shares)


class BacktraderEngine:
    """
    Backtrader backtesting engine wrapper
    """
    
    def __init__(self, initial_cash: float = 10000.0, commission: float = 0.001):
        """
        Initialize Backtrader engine
        
        Args:
            initial_cash: Starting capital
            commission: Commission rate (default: 0.001 = 0.1%)
        """
        if not BACKTRADER_AVAILABLE:
            logger.error("Backtrader not available - cannot initialize engine")
            return
        
        self.initial_cash = initial_cash
        self.commission = commission
        self.cerebro = None
        self.results = None
        
        logger.info(f"Initialized BacktraderEngine (cash=${initial_cash:.2f}, commission={commission:.3%})")
    
    def setup_cerebro(self):
        """Setup Cerebro instance"""
        if not BACKTRADER_AVAILABLE:
            return None
        
        self.cerebro = bt.Cerebro()
        
        # Set initial cash
        self.cerebro.broker.setcash(self.initial_cash)
        
        # Set commission
        self.cerebro.broker.setcommission(commission=self.commission)
        
        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        logger.info("Cerebro setup complete")
        
        return self.cerebro
    
    def add_data(self, data: pd.DataFrame, name: str = 'data'):
        """
        Add data to Cerebro
        
        Args:
            data: DataFrame with OHLCV data
            name: Data name
        """
        if not BACKTRADER_AVAILABLE or self.cerebro is None:
            return
        
        # Convert DataFrame to Backtrader data feed
        data = data.copy()
        
        # Ensure required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return
        
        # Convert date to datetime if needed
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
        
        # Create Backtrader data feed
        bt_data = bt.feeds.PandasData(dataname=data)
        
        self.cerebro.adddata(bt_data, name=name)
        logger.info(f"Added data '{name}' with {len(data)} rows")
    
    def add_strategy(self, strategy_class, **params):
        """
        Add strategy to Cerebro
        
        Args:
            strategy_class: Strategy class
            **params: Strategy parameters
        """
        if not BACKTRADER_AVAILABLE or self.cerebro is None:
            return
        
        self.cerebro.addstrategy(strategy_class, **params)
        logger.info(f"Added strategy: {strategy_class.__name__}")
    
    def run(self) -> Dict:
        """
        Run backtest
        
        Returns:
            Dictionary with results
        """
        if not BACKTRADER_AVAILABLE or self.cerebro is None:
            logger.error("Cannot run backtest - Cerebro not initialized")
            return {}
        
        logger.info("Starting backtest...")
        
        # Get initial value
        start_value = self.cerebro.broker.getvalue()
        
        # Run backtest
        self.results = self.cerebro.run()
        
        # Get final value
        end_value = self.cerebro.broker.getvalue()
        
        # Extract strategy
        strategy = self.results[0]
        
        # Get analyzer results
        analyzers = {}
        
        if hasattr(strategy, 'analyzers'):
            # Sharpe Ratio
            if hasattr(strategy.analyzers, 'sharpe'):
                sharpe_analysis = strategy.analyzers.sharpe.get_analysis()
                analyzers['sharpe_ratio'] = sharpe_analysis.get('sharperatio', 0)
            
            # Drawdown
            if hasattr(strategy.analyzers, 'drawdown'):
                dd_analysis = strategy.analyzers.drawdown.get_analysis()
                analyzers['max_drawdown'] = dd_analysis.get('max', {}).get('drawdown', 0)
                analyzers['max_drawdown_pct'] = dd_analysis.get('max', {}).get('drawdown', 0)
            
            # Returns
            if hasattr(strategy.analyzers, 'returns'):
                ret_analysis = strategy.analyzers.returns.get_analysis()
                analyzers['total_return'] = ret_analysis.get('rtot', 0)
                analyzers['average_return'] = ret_analysis.get('ravg', 0)
            
            # Trades
            if hasattr(strategy.analyzers, 'trades'):
                trade_analysis = strategy.analyzers.trades.get_analysis()
                analyzers['total_trades'] = trade_analysis.get('total', {}).get('total', 0)
                analyzers['winning_trades'] = trade_analysis.get('won', {}).get('total', 0)
                analyzers['losing_trades'] = trade_analysis.get('lost', {}).get('total', 0)
                
                total = analyzers['total_trades']
                won = analyzers['winning_trades']
                analyzers['win_rate'] = (won / total) if total > 0 else 0
        
        # Calculate basic metrics
        pnl = end_value - start_value
        roi = (pnl / start_value) * 100
        
        results = {
            'initial_value': start_value,
            'final_value': end_value,
            'pnl': pnl,
            'roi': roi,
            'analyzers': analyzers,
            'strategy': strategy
        }
        
        logger.info(f"Backtest complete - ROI: {roi:.2f}%")
        
        return results
    
    def print_results(self, results: Dict):
        """Print backtest results"""
        print("\n" + "="*60)
        print("BACKTRADER BACKTEST RESULTS")
        print("="*60)
        print(f"Initial Value: ${results['initial_value']:.2f}")
        print(f"Final Value: ${results['final_value']:.2f}")
        print(f"P&L: ${results['pnl']:.2f}")
        print(f"ROI: {results['roi']:.2f}%")
        
        analyzers = results.get('analyzers', {})
        if analyzers:
            print("\n" + "-"*60)
            print("Analysis Metrics")
            print("-"*60)
            
            if 'sharpe_ratio' in analyzers:
                print(f"Sharpe Ratio: {analyzers['sharpe_ratio']:.3f}")
            
            if 'max_drawdown_pct' in analyzers:
                print(f"Max Drawdown: {analyzers['max_drawdown_pct']:.2f}%")
            
            if 'total_trades' in analyzers:
                print(f"\nTotal Trades: {analyzers['total_trades']}")
                print(f"Winning Trades: {analyzers['winning_trades']}")
                print(f"Losing Trades: {analyzers['losing_trades']}")
                print(f"Win Rate: {analyzers['win_rate']:.2%}")
        
        print("="*60 + "\n")
    
    def plot(self):
        """Plot backtest results"""
        if not BACKTRADER_AVAILABLE or self.cerebro is None:
            logger.warning("Cannot plot - Cerebro not initialized")
            return
        
        try:
            self.cerebro.plot()
        except Exception as e:
            logger.error(f"Error plotting results: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Enhanced Backtrader Integration - Example Usage")
    print("="*60)
    print(f"Backtrader available: {BACKTRADER_AVAILABLE}")
    
    if not BACKTRADER_AVAILABLE:
        print("\nBacktrader not installed. Install with: pip install backtrader")
        print("Exiting...")
    else:
        # Generate sample data
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        np.random.seed(42)
        
        base_price = 100
        trend = np.linspace(0, 20, 252)
        noise = np.random.normal(0, 2, 252)
        close_prices = base_price + trend + noise
        
        # Generate OHLC
        open_prices = close_prices + np.random.normal(0, 0.5, 252)
        high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 1, 252)
        low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 1, 252)
        volumes = np.random.randint(1000000, 5000000, 252)
        
        data = pd.DataFrame({
            'date': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        })
        
        print(f"\nGenerated {len(data)} days of sample data")
        
        # Test SMA Strategy
        print("\n" + "="*60)
        print("Testing SMA Crossover Strategy")
        print("="*60)
        
        engine = BacktraderEngine(initial_cash=10000.0, commission=0.001)
        engine.setup_cerebro()
        engine.add_data(data)
        engine.add_strategy(SMABacktraderStrategy, fast_period=20, slow_period=50)
        
        results = engine.run()
        engine.print_results(results)
        
        print("\n" + "="*60)
        print("Enhanced Backtrader integration complete")
        print("="*60)
