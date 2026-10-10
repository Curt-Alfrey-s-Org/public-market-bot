#!/usr/bin/env python3
"""
Test script for tooltip label fix
Tests that create_tooltip_label works with and without label_id parameter
"""

import unittest
import os
import sys

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'


class TestTooltipLabelFix(unittest.TestCase):
    """Test create_tooltip_label function fix"""
    
    def setUp(self):
        """Set up test environment"""
        try:
            import web_gui
            self.web_gui = web_gui
        except ImportError as e:
            self.skipTest(f"Web GUI dependencies not available: {e}")
    
    def test_create_tooltip_label_without_id(self):
        """Test that create_tooltip_label works without label_id parameter"""
        # This was the original bug - it would raise TypeError with id=None
        try:
            label = self.web_gui.create_tooltip_label(
                'Total Capital ($):', 
                'Total amount of money allocated for trading.'
            )
            # If we get here, the function worked
            self.assertIsNotNone(label)
        except TypeError as e:
            self.fail(f"create_tooltip_label raised TypeError without label_id: {e}")
    
    def test_create_tooltip_label_with_id(self):
        """Test that create_tooltip_label works with label_id parameter"""
        try:
            label = self.web_gui.create_tooltip_label(
                'Test Label:', 
                'Test tooltip text',
                label_id='test-label-id'
            )
            self.assertIsNotNone(label)
        except Exception as e:
            self.fail(f"create_tooltip_label raised exception with label_id: {e}")
    
    def test_multiple_tooltip_labels(self):
        """Test creating multiple tooltip labels without IDs (the common use case)"""
        labels = []
        test_cases = [
            ('Total Capital ($):', 'Total amount of money allocated for trading.'),
            ('Min Allocation ($):', 'Minimum dollar amount per trade.'),
            ('Max Allocation ($):', 'Maximum dollar amount per trade.'),
        ]
        
        for label_text, tooltip_text in test_cases:
            try:
                label = self.web_gui.create_tooltip_label(label_text, tooltip_text)
                labels.append(label)
            except TypeError as e:
                self.fail(f"Failed to create tooltip label for '{label_text}': {e}")
        
        self.assertEqual(len(labels), len(test_cases))


class TestDccInputFix(unittest.TestCase):
    """Test that dcc.Input doesn't have unsupported title parameter"""
    
    def test_web_gui_imports_successfully(self):
        """Test that web_gui module imports without TypeError from dcc.Input"""
        try:
            import web_gui
            self.assertIsNotNone(web_gui.app)
        except TypeError as e:
            if 'title' in str(e) and 'dcc.Input' in str(e):
                self.fail(f"dcc.Input still has unsupported title parameter: {e}")
            else:
                raise


if __name__ == '__main__':
    print("="*60)
    print("Testing Tooltip Label Fix")
    print("="*60)
    print("\nTesting:")
    print("1. create_tooltip_label without label_id (original bug)")
    print("2. create_tooltip_label with label_id")
    print("3. Multiple tooltip labels")
    print("4. dcc.Input component fix")
    print("="*60)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
