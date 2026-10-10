#!/usr/bin/env python3
"""
Test TOS-style table layout for trade displays
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the web_gui module
import web_gui

class TestTOSTableLayout(unittest.TestCase):
    """Test TOS-style table layout implementation"""
    
    def test_create_tos_style_trade_table_empty(self):
        """Test table creation with empty trades list"""
        result = web_gui.create_tos_style_trade_table([])
        # Should return a message div
        self.assertIsNotNone(result)
    
    def test_create_tos_style_trade_table_with_trades(self):
        """Test table creation with sample trades"""
        sample_trades = [
            {
                'symbol': 'AAPL',
                'action': 'BUY',
                'price': 150.25,
                'entry_price': 150.25,
                'exit_price': 155.50,
                'quantity': 10,
                'pnl': 52.50,
                'pnl_percent': 3.49,
                'hold_duration': 2.5,
                'exit_reason': 'trailing_stop',
                'timestamp': '2026-01-23T10:30:00',
                'is_win': True
            },
            {
                'symbol': 'MSFT',
                'action': 'BUY',
                'price': 380.50,
                'entry_price': 380.50,
                'exit_price': 375.00,
                'quantity': 5,
                'pnl': -27.50,
                'pnl_percent': -1.44,
                'hold_duration': 1.2,
                'exit_reason': 'stop_loss',
                'timestamp': '2026-01-23T11:45:00',
                'is_win': False
            }
        ]
        
        result = web_gui.create_tos_style_trade_table(sample_trades)
        
        # Should return a DataTable
        self.assertIsNotNone(result)
        self.assertEqual(result._type, 'DataTable')
        
        # Check that data was created
        self.assertIsNotNone(result.data)
        self.assertEqual(len(result.data), 2)
        
        # Verify first row data (most recent first, so MSFT)
        first_row = result.data[0]
        self.assertEqual(first_row['Symbol'], 'MSFT')
        self.assertEqual(first_row['Action'], 'CLOSED')
        self.assertEqual(first_row['Result'], '❌')
        self.assertIn('$-27.50', first_row['P&L'])
        
        # Verify second row data (AAPL)
        second_row = result.data[1]
        self.assertEqual(second_row['Symbol'], 'AAPL')
        self.assertEqual(second_row['Action'], 'CLOSED')
        self.assertEqual(second_row['Result'], '✅')
        self.assertIn('$52.50', second_row['P&L'])
        
        # Verify columns are properly defined
        self.assertEqual(len(result.columns), 10)
        column_names = [col['name'] for col in result.columns]
        self.assertIn('Symbol', column_names)
        self.assertIn('Action', column_names)
        self.assertIn('Entry', column_names)
        self.assertIn('Exit', column_names)
        self.assertIn('P&L', column_names)
        self.assertIn('Hold', column_names)
        
        print("✓ TOS-style table created successfully with proper formatting")
    
    def test_create_tos_style_trade_table_max_rows(self):
        """Test table respects max_rows parameter"""
        # Create 30 sample trades
        sample_trades = [
            {
                'symbol': f'SYM{i}',
                'action': 'BUY',
                'price': 100 + i,
                'timestamp': f'2026-01-23T{10 + (i % 14):02d}:00:00',
                'is_win': i % 2 == 0
            }
            for i in range(30)
        ]
        
        # Request only 10 rows
        result = web_gui.create_tos_style_trade_table(sample_trades, max_rows=10)
        
        # Should only have 10 rows
        self.assertEqual(len(result.data), 10)
        
        # Should be the most recent 10
        self.assertEqual(result.data[0]['Symbol'], 'SYM29')  # Most recent
        self.assertEqual(result.data[9]['Symbol'], 'SYM20')
        
        print("✓ Max rows parameter working correctly")
    
    def test_hold_duration_formatting(self):
        """Test various hold duration formats"""
        sample_trades = [
            {
                'symbol': 'TEST1',
                'action': 'BUY',
                'price': 100,
                'hold_duration': 0.5,  # 30 minutes
                'timestamp': '2026-01-23T10:00:00',
                'is_win': True
            },
            {
                'symbol': 'TEST2',
                'action': 'BUY',
                'price': 100,
                'hold_duration': 5.0,  # 5 hours
                'timestamp': '2026-01-23T11:00:00',
                'is_win': True
            },
            {
                'symbol': 'TEST3',
                'action': 'BUY',
                'price': 100,
                'hold_duration': 48.0,  # 2 days
                'timestamp': '2026-01-23T12:00:00',
                'is_win': True
            }
        ]
        
        result = web_gui.create_tos_style_trade_table(sample_trades)
        
        # Check formatting (remember: most recent first, so reversed order)
        self.assertIn('2.0d', result.data[0]['Hold'])  # Days (TEST3 most recent)
        self.assertIn('5.0h', result.data[1]['Hold'])  # Hours (TEST2)
        self.assertIn('30m', result.data[2]['Hold'])  # Minutes (TEST1 oldest)
        
        print("✓ Hold duration formatting working correctly")

if __name__ == '__main__':
    # Run tests
    print("\n" + "="*70)
    print("Testing TOS-Style Table Layout Implementation")
    print("="*70 + "\n")
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTOSTableLayout)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✓ All TOS table layout tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*70 + "\n")
    
    sys.exit(0 if result.wasSuccessful() else 1)
