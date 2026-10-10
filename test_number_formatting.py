#!/usr/bin/env python3
"""
Test script for number formatting in web GUI
Tests that money values and percentages are formatted correctly
"""

import unittest
import os
import sys

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the format_trade_value function from web_gui
from web_gui import format_trade_value


class TestNumberFormatting(unittest.TestCase):
    """Test number formatting in web GUI History tab"""
    
    def test_format_trade_value_money_fields(self):
        """Test that money fields are formatted to 2 decimal places"""
        # Test money field formatting
        self.assertEqual(format_trade_value('price', 46.72999954223633), 46.73)
        self.assertEqual(format_trade_value('entry_price', 46.72999954223633), 46.73)
        self.assertEqual(format_trade_value('exit_price', 49.06649951934815), 49.07)
        self.assertEqual(format_trade_value('pnl', 2.5000000000000044), 2.5)
        self.assertEqual(format_trade_value('starting_capital', 10000), 10000)
        self.assertEqual(format_trade_value('current_capital', 10155.589571618784), 10155)
        self.assertEqual(format_trade_value('total_return', 155.58957161878425), 155)
    
    def test_format_trade_value_percentage_fields(self):
        """Test that percentage fields are formatted to 4 decimal places"""
        # Test percentage field formatting (stored as decimal, e.g., 0.05 = 5%)
        self.assertEqual(format_trade_value('pnl_percent', 5.000000000000009), 5.0)
        self.assertEqual(format_trade_value('win_rate', 0.75), 0.75)
        self.assertEqual(format_trade_value('return_percentage', 1.5558957161878426), 1.5559)
        self.assertEqual(format_trade_value('volatility', 0.033997593278843344), 0.034)
    
    def test_format_trade_value_quantity_fields(self):
        """Test that quantity fields are formatted to 2 decimal places"""
        # Test quantity field formatting
        self.assertEqual(format_trade_value('quantity', 1.06997647099928), 1.07)
        self.assertEqual(format_trade_value('quantity', 10.123456789), 10.12)
    
    def test_format_trade_value_hold_duration(self):
        """Test that hold_duration is formatted to 2 decimal places"""
        # Test hold_duration field formatting (extremely small value from issue)
        self.assertEqual(format_trade_value('hold_duration', 9.166666666666668e-09), 0.0)
        self.assertEqual(format_trade_value('hold_duration', 1.5), 1.5)
        self.assertEqual(format_trade_value('hold_duration', 24.567), 24.57)
    
    def test_format_trade_value_non_numeric(self):
        """Test that non-numeric values are returned as-is"""
        # Test non-numeric values
        self.assertEqual(format_trade_value('symbol', 'AAPL'), 'AAPL')
        self.assertEqual(format_trade_value('action', 'BUY'), 'BUY')
        self.assertEqual(format_trade_value('exit_reason', 'end_of_simulation'), 'end_of_simulation')
        self.assertIsNone(format_trade_value('price', None))
    
    def test_full_trade_formatting(self):
        """Test formatting a complete trade record like in the issue"""
        # Sample trade from the issue
        trade = {
            "timestamp": "2026-01-19T23:12:48.811241",
            "symbol": "SLB",
            "action": "BUY",
            "quantity": 1.06997647099928,
            "price": 46.72999954223633,
            "is_win": True,
            "mode": "api_disabled",
            "entry_price": 46.72999954223633,
            "exit_price": 49.06649951934815,
            "pnl": 2.5000000000000044,
            "pnl_percent": 5.000000000000009,
            "exit_reason": "end_of_simulation",
            "hold_duration": 9.166666666666668e-09,
            "volatility": 0.033997593278843344,
            "volume": 17367700
        }
        
        # Format the trade
        formatted_trade = {}
        for key, value in trade.items():
            formatted_trade[key] = format_trade_value(key, value)
        
        # Verify key fields are properly formatted
        self.assertEqual(formatted_trade['quantity'], 1.07)
        self.assertEqual(formatted_trade['price'], 46.73)
        self.assertEqual(formatted_trade['entry_price'], 46.73)
        self.assertEqual(formatted_trade['exit_price'], 49.07)
        self.assertEqual(formatted_trade['pnl'], 2.5)
        self.assertEqual(formatted_trade['pnl_percent'], 5.0)
        self.assertEqual(formatted_trade['hold_duration'], 0.0)
        self.assertEqual(formatted_trade['volatility'], 0.034)
        
        # Verify non-numeric fields are unchanged
        self.assertEqual(formatted_trade['symbol'], 'SLB')
        self.assertEqual(formatted_trade['action'], 'BUY')
        self.assertEqual(formatted_trade['exit_reason'], 'end_of_simulation')


if __name__ == '__main__':
    print("="*60)
    print("Testing Number Formatting for Web GUI")
    print("="*60)
    print("\nTesting:")
    print("1. Money field formatting (2 decimal places)")
    print("2. Percentage field formatting (4 decimal places)")
    print("3. Quantity field formatting (2 decimal places)")
    print("4. Hold duration formatting (2 decimal places)")
    print("5. Non-numeric value handling")
    print("6. Full trade record formatting")
    print("="*60)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
