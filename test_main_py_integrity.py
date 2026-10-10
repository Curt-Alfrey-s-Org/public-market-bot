#!/usr/bin/env python3
"""
Test to verify main.py integrity and completeness.
Specifically checks that the file is not truncated and all key functions exist.
"""

import unittest
import ast
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestMainPyIntegrity(unittest.TestCase):
    """Test suite to verify main.py file integrity."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Parse the main.py file
        with open('main.py', 'r') as f:
            cls.main_py_code = f.read()
        
        # Parse AST
        cls.tree = ast.parse(cls.main_py_code)
        
        # Extract functions and classes
        cls.functions = [node.name for node in ast.walk(cls.tree) 
                        if isinstance(node, ast.FunctionDef)]
        cls.classes = [node.name for node in ast.walk(cls.tree) 
                      if isinstance(node, ast.ClassDef)]

    def test_file_is_syntactically_valid(self):
        """Test that main.py can be parsed without syntax errors."""
        self.assertIsNotNone(self.tree, "main.py should parse as valid Python")

    def test_tradingbot_class_exists(self):
        """Test that TradingBot class exists."""
        self.assertIn('TradingBot', self.classes, 
                     "TradingBot class should exist in main.py")

    def test_fetch_schwab_stock_price_exists(self):
        """Test that fetch_schwab_stock_price method exists."""
        self.assertIn('fetch_schwab_stock_price', self.functions,
                     "fetch_schwab_stock_price method should exist")

    def test_fetch_schwab_stock_price_is_complete(self):
        """Test that fetch_schwab_stock_price function is complete (not truncated)."""
        # Find the function in the AST
        func_node = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'fetch_schwab_stock_price':
                func_node = node
                break
        
        self.assertIsNotNone(func_node, "fetch_schwab_stock_price function should be in AST")
        
        # Check that function has a body
        self.assertGreater(len(func_node.body), 0, 
                          "fetch_schwab_stock_price should have a function body")
        
        # Check that function has return statements (not truncated)
        has_return = any(isinstance(node, ast.Return) for node in ast.walk(func_node))
        self.assertTrue(has_return, 
                       "fetch_schwab_stock_price should have at least one return statement")

    def test_fetch_real_stock_price_exists(self):
        """Test that fetch_real_stock_price method exists."""
        self.assertIn('fetch_real_stock_price', self.functions,
                     "fetch_real_stock_price method should exist")

    def test_get_stock_price_exists(self):
        """Test that get_stock_price method exists."""
        self.assertIn('get_stock_price', self.functions,
                     "get_stock_price method should exist")

    def test_execute_trade_exists(self):
        """Test that execute_trade method exists."""
        self.assertIn('execute_trade', self.functions,
                     "execute_trade method should exist")

    def test_main_function_exists(self):
        """Test that main function exists."""
        self.assertIn('main', self.functions,
                     "main function should exist")

    def test_default_initial_capital_defined(self):
        """Test that DEFAULT_INITIAL_CAPITAL is defined."""
        self.assertIn('DEFAULT_INITIAL_CAPITAL', self.main_py_code,
                     "DEFAULT_INITIAL_CAPITAL should be defined")

    def test_file_ends_properly(self):
        """Test that file ends with proper if __name__ == '__main__' block."""
        lines = self.main_py_code.strip().split('\n')
        last_lines = '\n'.join(lines[-5:])
        
        self.assertIn('if __name__', last_lines,
                     "File should end with if __name__ == '__main__' block")
        self.assertIn('main()', last_lines,
                     "File should call main() at the end")

    def test_no_abrupt_logger_truncation(self):
        """Test that no lines end abruptly with 'logger' (indicating truncation)."""
        lines = self.main_py_code.split('\n')
        
        # Check for lines that end with just "logger" (no dot or parentheses)
        suspicious_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if stripped.endswith('logger') and not any(c in stripped[-10:] 
                                                       for c in ['.', '(', ')', '=']):
                suspicious_lines.append((i, line))
        
        self.assertEqual(len(suspicious_lines), 0,
                        f"Found {len(suspicious_lines)} lines ending suspiciously with 'logger': {suspicious_lines[:3]}")

    def test_key_methods_have_docstrings(self):
        """Test that key methods have docstrings."""
        key_methods = ['fetch_schwab_stock_price', 'fetch_real_stock_price', 
                      'get_stock_price', 'execute_trade']
        
        for method_name in key_methods:
            # Find the method in AST
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef) and node.name == method_name:
                    # Check for docstring
                    has_docstring = (ast.get_docstring(node) is not None)
                    self.assertTrue(has_docstring,
                                  f"{method_name} should have a docstring")
                    break

    def test_file_line_count(self):
        """Test that file has expected number of lines (not truncated)."""
        lines = self.main_py_code.split('\n')
        line_count = len(lines)
        
        # File should have at least 4000 lines (based on current implementation)
        self.assertGreater(line_count, 4000,
                          f"main.py should have >4000 lines, found {line_count}")


if __name__ == '__main__':
    unittest.main()
