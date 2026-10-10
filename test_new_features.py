#!/usr/bin/env python3
"""
Test suite for new trading bot features: trailing stops, TOS CSV import, and realistic sequencing
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')

import unittest
import tempfile
from unittest.mock import patch
from main import TradingBot


class TestTrailingStop(unittest.TestCase):
    """Test trailing stop functionality"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_open_position(self):
        """Test opening a position initializes tracking correctly"""
        self.bot.open_position('TEST', 100.0, 10.0)
        
        self.assertIn('TEST', self.bot.positions)
        self.assertEqual(self.bot.positions['TEST']['entry_price'], 100.0)
        self.assertEqual(self.bot.positions['TEST']['quantity'], 10.0)
        self.assertEqual(self.bot.positions['TEST']['high_price'], 100.0)
    
    def test_trailing_stop_not_triggered(self):
        """Test trailing stop not triggered when price rises"""
        self.bot.open_position('TEST', 100.0, 10.0)
        
        # Price rises to 105
        is_triggered = self.bot.check_trailing_stop('TEST', 105.0)
        self.assertFalse(is_triggered)
        
        # High water mark should be updated
        self.assertEqual(self.bot.positions['TEST']['high_price'], 105.0)
    
    def test_trailing_stop_triggered(self):
        """Test trailing stop triggered when price falls below threshold"""
        self.bot.open_position('TEST', 100.0, 10.0)
        
        # Price rises to 110
        self.bot.check_trailing_stop('TEST', 110.0)
        self.assertEqual(self.bot.positions['TEST']['high_price'], 110.0)
        
        # Price falls to 103 (below 110 * 0.95 = 104.5)
        is_triggered = self.bot.check_trailing_stop('TEST', 103.0)
        self.assertTrue(is_triggered)
    
    def test_close_position_win(self):
        """Test closing a winning position"""
        self.bot.open_position('TEST', 100.0, 10.0)
        
        result = self.bot.close_position('TEST', 110.0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'TEST')
        self.assertEqual(result['entry_price'], 100.0)
        self.assertEqual(result['exit_price'], 110.0)
        self.assertEqual(result['quantity'], 10.0)
        self.assertEqual(result['pnl'], 100.0)  # (110 - 100) * 10
        self.assertEqual(result['pnl_percent'], 10.0)
        self.assertTrue(result['is_win'])
        
        # Position should be removed
        self.assertNotIn('TEST', self.bot.positions)
    
    def test_close_position_loss(self):
        """Test closing a losing position"""
        self.bot.open_position('TEST', 100.0, 10.0)
        
        result = self.bot.close_position('TEST', 95.0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['pnl'], -50.0)  # (95 - 100) * 10
        self.assertEqual(result['pnl_percent'], -5.0)
        self.assertFalse(result['is_win'])
    
    def test_close_position_not_exists(self):
        """Test closing a position that doesn't exist"""
        result = self.bot.close_position('NONEXISTENT', 100.0)
        self.assertIsNone(result)


class TestCSVImport(unittest.TestCase):
    """Test TOS CSV import functionality"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_import_valid_csv(self):
        """Test importing a valid CSV file"""
        # Create a temporary CSV file
        csv_content = """Symbol,Quantity,Price,Action,Date
AAPL,10,150.00,BUY,2026-01-15
MSFT,5,380.00,BUY,2026-01-15
GOOGL,-8,140.00,SELL,2026-01-15
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            trades = self.bot.import_tos_csv(csv_file)
            
            self.assertEqual(len(trades), 3)
            self.assertEqual(trades[0]['symbol'], 'AAPL')
            self.assertEqual(trades[0]['quantity'], 10.0)
            self.assertEqual(trades[0]['price'], 150.0)
            self.assertEqual(trades[0]['action'], 'BUY')
            
            self.assertEqual(trades[2]['symbol'], 'GOOGL')
            self.assertEqual(trades[2]['quantity'], -8.0)  # Negative quantity for SELL
            self.assertEqual(trades[2]['action'], 'SELL')
        finally:
            os.unlink(csv_file)
    
    def test_import_csv_case_insensitive(self):
        """Test CSV import handles case-insensitive column names"""
        csv_content = """SYMBOL,QUANTITY,PRICE
TEST,5,100.50
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            trades = self.bot.import_tos_csv(csv_file)
            
            self.assertEqual(len(trades), 1)
            self.assertEqual(trades[0]['symbol'], 'TEST')
            self.assertEqual(trades[0]['quantity'], 5.0)
            self.assertEqual(trades[0]['price'], 100.5)
        finally:
            os.unlink(csv_file)
    
    def test_import_csv_missing_columns(self):
        """Test CSV import with missing required columns"""
        csv_content = """Symbol,Action
AAPL,BUY
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            trades = self.bot.import_tos_csv(csv_file)
            
            # Should return empty list due to missing columns
            self.assertEqual(len(trades), 0)
        finally:
            os.unlink(csv_file)
    
    def test_import_csv_nonexistent_file(self):
        """Test importing a non-existent CSV file"""
        trades = self.bot.import_tos_csv('nonexistent_file.csv')
        self.assertEqual(len(trades), 0)
    
    def test_process_tos_trades(self):
        """Test processing TOS trades updates track record"""
        trades = [
            {'symbol': 'AAPL', 'quantity': 10, 'price': 150.0, 'action': 'BUY'},
            {'symbol': 'MSFT', 'quantity': 5, 'price': 380.0, 'action': 'BUY'},
        ]
        
        initial_trades = self.bot.track_record['total_trades']
        
        with patch('random.uniform', return_value=1.01):  # Force wins
            self.bot.process_tos_trades(trades)
        
        self.assertEqual(self.bot.track_record['total_trades'], initial_trades + 2)
        self.assertGreater(self.bot.track_record['winning_trades'], 0)


class TestSymbolScanning(unittest.TestCase):
    """Test symbol scanning and sequencing functionality"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_load_scan_symbols_from_file(self):
        """Test loading symbols from a file"""
        # Create a temporary symbol file
        symbol_content = """AAPL
MSFT
GOOGL
TSLA
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(symbol_content)
            symbol_file = f.name
        
        try:
            symbols = self.bot.load_scan_symbols(symbol_file)
            
            self.assertEqual(len(symbols), 4)
            self.assertIn('AAPL', symbols)
            self.assertIn('MSFT', symbols)
            self.assertIn('GOOGL', symbols)
            self.assertIn('TSLA', symbols)
        finally:
            os.unlink(symbol_file)
    
    def test_load_scan_symbols_nonexistent_file(self):
        """Test loading symbols from non-existent file returns defaults"""
        symbols = self.bot.load_scan_symbols('nonexistent_file.txt')
        
        # Should return default symbols
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)
    
    def test_generate_random_price_no_base(self):
        """Test generating random price without base price"""
        price = self.bot.generate_random_price()
        
        self.assertGreater(price, 0)
        self.assertLessEqual(price, 500.0)
    
    def test_generate_random_price_with_base(self):
        """Test generating random price with base price"""
        base_price = 100.0
        
        # Generate multiple prices to test variation
        prices = [self.bot.generate_random_price(base_price) for _ in range(10)]
        
        for price in prices:
            # Price should be within +/- 5% of base
            self.assertGreaterEqual(price, base_price * 0.95)
            self.assertLessEqual(price, base_price * 1.05)
    
    def test_generate_random_volume(self):
        """Test generating random volume"""
        volume = self.bot.generate_random_volume()
        
        self.assertGreaterEqual(volume, 100000)
        self.assertLessEqual(volume, 10000000)
        self.assertIsInstance(volume, int)


class TestIntegrationWithNewFeatures(unittest.TestCase):
    """Integration tests for new features"""
    
    def setUp(self):
        """Set up test bot instance"""
        self.bot = TradingBot(total_capital=10000.0)
    
    def test_trailing_stop_integration_in_trade(self):
        """Test trailing stop is integrated in paper mode trading"""
        # Execute a trade - should open position and check trailing stop
        with patch('random.random', return_value=0.5):
            with patch.object(self.bot, 'generate_random_price', side_effect=[95.0, 100.0, 105.0, 103.0, 101.0]):
                result = self.bot.execute_trade_paper_mode('TEST', 'BUY', 100.0)
        
        # Trade should execute
        self.assertEqual(result['status'], 'simulated')
        self.assertEqual(result['symbol'], 'TEST')
    
    def test_end_to_end_csv_workflow(self):
        """Test complete CSV import and processing workflow"""
        # Create CSV
        csv_content = """Symbol,Quantity,Price,Action
AAPL,10,150.00,BUY
MSFT,5,380.00,BUY
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            # Import and process
            trades = self.bot.import_tos_csv(csv_file)
            self.assertEqual(len(trades), 2)
            
            initial_total = self.bot.track_record['total_trades']
            
            with patch('random.uniform', return_value=1.01):
                self.bot.process_tos_trades(trades)
            
            # Verify trades were processed
            self.assertEqual(self.bot.track_record['total_trades'], initial_total + 2)
        finally:
            os.unlink(csv_file)


if __name__ == "__main__":
    # Run tests with unittest's standard runner
    unittest.main(verbosity=2)
