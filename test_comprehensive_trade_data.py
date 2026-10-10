#!/usr/bin/env python3
"""
Test comprehensive trade data capture for sell orders
Validates that trade history includes entry/exit prices, P&L, exit reasons, etc.
"""

import unittest
import os
import sys

# Set environment variables for testing
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


class TestComprehensiveTradeData(unittest.TestCase):
    """Test that comprehensive trade data is captured for both BUY and SELL orders"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create bot with paper trading
        self.bot = main.TradingBot(total_capital=10000.0)
    
    def test_buy_trade_includes_comprehensive_data(self):
        """Test that BUY trades capture comprehensive exit data"""
        # Execute a BUY trade (which automatically closes in paper mode)
        self.bot.execute_trade('AAPL', 'BUY', 150.0, volume=1000000)
        self.bot.execute_trade('AAPL', 'BUY', 150.0, volume=1000000)
        # Check that trade was recorded
        self.assertEqual(len(self.bot.trade_history), 1)
        
        trade = self.bot.trade_history[0]
        
        # Verify basic fields
        self.assertEqual(trade['symbol'], 'AAPL')
        self.assertEqual(trade['action'], 'BUY')
        self.assertIn('timestamp', trade)
        self.assertIn('is_win', trade)
        
        # Verify comprehensive data is present
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertIn('exit_reason', trade)
        self.assertIn('quantity', trade)
        
        # Verify data types and values
        self.assertIsInstance(trade['entry_price'], float)
        self.assertIsInstance(trade['exit_price'], float)
        self.assertIsInstance(trade['pnl'], float)
        self.assertIsInstance(trade['pnl_percent'], float)
        self.assertEqual(trade['exit_reason'], 'end_of_simulation')
        self.assertGreater(trade['quantity'], 0)
        
        # Verify P&L consistency
        expected_pnl = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
        self.assertAlmostEqual(trade['pnl'], expected_pnl, places=2)
        
        print(f"✓ BUY trade captured comprehensive data:")
        print(f"  Entry: ${trade['entry_price']:.2f}")
        print(f"  Exit: ${trade['exit_price']:.2f}")
        print(f"  P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
        print(f"  Exit Reason: {trade['exit_reason']}")
    
    def test_sell_trade_includes_comprehensive_data(self):
        """Test that SELL trades capture comprehensive entry/exit data"""
        # Execute a SELL trade
        self.bot.execute_trade('MSFT', 'SELL', 380.0, volume=500000)
        # Check that trade was recorded
        self.assertEqual(len(self.bot.trade_history), 1)
        
        trade = self.bot.trade_history[0]
        
        # Verify basic fields
        self.assertEqual(trade['symbol'], 'MSFT')
        self.assertEqual(trade['action'], 'SELL')
        
        # Verify comprehensive data is present
        self.assertIn('entry_price', trade)
        self.assertIn('exit_price', trade)
        self.assertIn('pnl', trade)
        self.assertIn('pnl_percent', trade)
        self.assertIn('exit_reason', trade)
        
        # Verify data types
        self.assertIsInstance(trade['entry_price'], float)
        self.assertIsInstance(trade['exit_price'], float)
        self.assertIsInstance(trade['pnl'], float)
        self.assertIsInstance(trade['pnl_percent'], float)
        
        # For SELL, exit_price should be the price parameter
        self.assertEqual(trade['exit_price'], 380.0)
        
        print(f"✓ SELL trade captured comprehensive data:")
        print(f"  Entry: ${trade['entry_price']:.2f}")
        print(f"  Exit: ${trade['exit_price']:.2f}")
        print(f"  P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
        print(f"  Exit Reason: {trade['exit_reason']}")
    
    def test_optional_fields_present(self):
        """Test that optional fields like volume and volatility are captured when available"""
        # Execute trade with volume
        self.bot.execute_trade('GOOGL', 'BUY', 140.0, volume=2000000)
        trade = self.bot.trade_history[0]
        self.bot.execute_trade('GOOGL', 'BUY', 140.0, volume=2000000)
        
        # Check optional fields
        self.assertIn('volume', trade)
        self.assertEqual(trade['volume'], 2000000)
        
        # Hold duration may be present (depends on position tracking)
        if 'hold_duration' in trade:
            self.assertIsInstance(trade['hold_duration'], (float, type(None)))
        
        # Volatility may be present
        if 'volatility' in trade:
            self.assertIsInstance(trade['volatility'], (float, type(None)))
        
        print(f"✓ Optional fields captured:")
        print(f"  Volume: {trade.get('volume', 'N/A')}")
        print(f"  Hold Duration: {trade.get('hold_duration', 'N/A')}")
        print(f"  Volatility: {trade.get('volatility', 'N/A')}")
    
    def test_multiple_trades_all_have_data(self):
        """Test that multiple trades all capture comprehensive data"""
        # Execute multiple trades
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        actions = ['BUY', 'SELL', 'BUY', 'SELL']
        
        for symbol, action in zip(symbols, actions):
            price = 150.0 if action == 'BUY' else 200.0
            self.bot.execute_trade(symbol, action, price, volume=1000000)
        
        # Verify all trades have comprehensive data
        self.assertEqual(len(self.bot.trade_history), 4)
        
        for trade in self.bot.trade_history:
            self.assertIn('entry_price', trade)
            self.assertIn('exit_price', trade)
            self.assertIn('pnl', trade)
            self.assertIn('pnl_percent', trade)
            self.assertIn('exit_reason', trade)
            self.assertIn('quantity', trade)
        
        print(f"✓ All {len(self.bot.trade_history)} trades have comprehensive data")
    
    def test_tos_import_includes_comprehensive_data(self):
        """Test that TOS CSV import includes comprehensive data"""
        # Create mock TOS trades
        tos_trades = [
            {
                'symbol': 'NVDA',
                'action': 'BUY',
                'quantity': 10.0,
                'price': 500.0
            },
            {
                'symbol': 'AMD',
                'action': 'SELL',
                'quantity': 5.0,
                'price': 120.0
            }
        ]
        
        # Process TOS trades
        self.bot.process_tos_trades(tos_trades)
        
        # Verify trades have comprehensive data
        self.assertEqual(len(self.bot.trade_history), 2)
        
        for trade in self.bot.trade_history:
            self.assertIn('entry_price', trade)
            self.assertIn('exit_price', trade)
            self.assertIn('pnl', trade)
            self.assertIn('pnl_percent', trade)
            self.assertIn('exit_reason', trade)
            self.assertEqual(trade['exit_reason'], 'tos_csv_import')
        
        print(f"✓ TOS imported trades have comprehensive data")
    
    def test_trade_data_structure_for_ai(self):
        """Test that trade data structure is suitable for AI analysis"""
        # Execute a trade
        self.bot.execute_trade('AAPL', 'BUY', 150.0, volume=1000000)
        
        trade = self.bot.trade_history[0]
        
        # Verify essential fields for AI analysis
        ai_required_fields = [
            'symbol',           # What was traded
            'action',           # BUY or SELL
            'timestamp',        # When
            'quantity',         # How much
            'entry_price',      # Entry point
            'exit_price',       # Exit point
            'pnl',             # Profit/Loss in dollars
            'pnl_percent',     # Profit/Loss percentage
            'is_win',          # Win or Loss
            'exit_reason',     # Why position was closed
            'mode'             # Trading mode
        ]
        
        for field in ai_required_fields:
            self.assertIn(field, trade, f"Required field '{field}' missing from trade data")
        
        print(f"✓ Trade data contains all fields required for AI analysis:")
        for field in ai_required_fields:
            print(f"  {field}: {trade[field]}")


if __name__ == '__main__':
    print("Testing comprehensive trade data capture...")
    print("=" * 60)
    unittest.main(verbosity=2)
