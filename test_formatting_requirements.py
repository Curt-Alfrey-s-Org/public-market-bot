#!/usr/bin/env python3
"""
Test to verify formatting requirements for dollar amounts and percentages
issue: dollar amounts rounded to the nearest cent

This test verifies that:
1. Dollar amounts are formatted with 2 decimal places (nearest cent)
2. Percentages are formatted with 1 decimal place (nearest tenth)
"""

import unittest
import re


class TestFormattingRequirements(unittest.TestCase):
    """Test that all formatting in key files meets requirements"""
    
    FILES_TO_CHECK = [
        'gui.py',
        'web_gui.py',
        'main.py',
        'report_generator.py'
    ]
    
    def test_dollar_amounts_use_2_decimal_places(self):
        """Verify all dollar amounts use .2f format (2 decimal places)"""
        # Pattern: ${variable:.Xf} where X should be 2
        dollar_pattern = r'\$\{[^}]+:\.(\d+)f\}'
        
        errors = []
        for filename in self.FILES_TO_CHECK:
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(dollar_pattern, line)
                    for match in matches:
                        decimal_places = match.group(1)
                        if decimal_places != '2':
                            errors.append(
                                f"{filename}:{line_num} - Dollar amount uses .{decimal_places}f "
                                f"instead of .2f: {match.group(0)}"
                            )
            except FileNotFoundError:
                self.fail(f"File {filename} not found")
        
        if errors:
            self.fail(
                "Found dollar amounts not using .2f format:\n  " + 
                "\n  ".join(errors)
            )
    
    def test_percentages_use_1_decimal_place(self):
        """Verify all percentages use .1f% or .1% format (1 decimal place)"""
        errors = []
        
        for filename in self.FILES_TO_CHECK:
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                # Pattern 1: {variable*100:.Xf}% where X should be 1
                # Match standard spacing around * operator (0 or 1 space on each side)
                pct_pattern1 = r'\{[^}]*\*\s?100\s?:\.(\d+)f\}%'
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pct_pattern1, line)
                    for match in matches:
                        decimal_places = match.group(1)
                        if decimal_places != '1':
                            errors.append(
                                f"{filename}:{line_num} - Percentage (decimal*100) uses "
                                f".{decimal_places}f% instead of .1f%: {match.group(0)}"
                            )
                
                # Pattern 2: {variable:.X%} where X should be 1
                # Match variable name before colon, then format specifier
                pct_pattern2 = r'\{[^}:]+:\.(\d+)%\}'
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pct_pattern2, line)
                    for match in matches:
                        decimal_places = match.group(1)
                        if decimal_places != '1':
                            errors.append(
                                f"{filename}:{line_num} - Percentage (% format) uses "
                                f".{decimal_places}% instead of .1%: {match.group(0)}"
                            )
            except FileNotFoundError:
                self.fail(f"File {filename} not found")
        
        if errors:
            self.fail(
                "Found percentages not using .1f% or .1% format:\n  " + 
                "\n  ".join(errors)
            )
    
    def test_formatting_examples(self):
        """Test that formatting functions work correctly with example values"""
        # Test dollar formatting
        test_dollars = [
            (1234.567, "$1234.57"),
            (0.99, "$0.99"),
            (999999.999, "$1000000.00"),
            (0.01, "$0.01"),
            (10000.0, "$10000.00"),
            (125.50, "$125.50")
        ]
        
        for value, expected in test_dollars:
            result = f"${value:.2f}"
            self.assertEqual(
                result, expected,
                f"Dollar formatting: ${value} should format to {expected}, got {result}"
            )
        
        # Test percentage formatting (decimal * 100 approach)
        test_percentages_decimal = [
            (0.567, "56.7%"),
            (0.123, "12.3%"),
            (0.999, "99.9%"),
            (0.001, "0.1%"),
            (0.0, "0.0%"),
            (0.7, "70.0%")
        ]
        
        for value, expected in test_percentages_decimal:
            result = f"{value*100:.1f}%"
            self.assertEqual(
                result, expected,
                f"Percentage formatting (decimal*100): {value} should format to {expected}, got {result}"
            )
        
        # Test percentage formatting (% specifier approach)
        test_percentages_specifier = [
            (0.567, "56.7%"),
            (0.123, "12.3%"),
            (0.999, "99.9%"),
            (0.001, "0.1%"),
            (0.0, "0.0%"),
            (0.7, "70.0%")
        ]
        
        for value, expected in test_percentages_specifier:
            result = f"{value:.1%}"
            self.assertEqual(
                result, expected,
                f"Percentage formatting (% specifier): {value} should format to {expected}, got {result}"
            )


if __name__ == '__main__':
    print("Testing formatting requirements...")
    print("="*70)
    print("Requirements:")
    print("  1. Dollar amounts: 2 decimal places (nearest cent)")
    print("  2. Percentages: 1 decimal place (nearest tenth)")
    print("="*70)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
