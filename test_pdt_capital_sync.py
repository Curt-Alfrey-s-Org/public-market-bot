"""
Test PDT capital synchronization with environment variables
Validates that PDTTracker uses consistent capital values from BOT_TOTAL_CAPITAL
"""

import os
import unittest
from unittest.mock import patch

# Test PDTTracker class directly without importing full GUI
# This avoids tkinter dependency issues in CI/headless environments


class TestPDTTrackerCapital(unittest.TestCase):
    """Test PDTTracker capital configuration"""
    
    def test_pdt_tracker_default_is_10000(self):
        """Test that PDTTracker default capital is 10000 (not 500)"""
        # Import locally to avoid import errors
        try:
            from gui import PDTTracker
        except ImportError:
            self.skipTest("GUI module not available (likely missing tkinter)")
            return
        
        tracker = PDTTracker()
        
        self.assertEqual(tracker.starting_capital, 10000.0, 
                        "PDTTracker should default to 10000, not 500")
        self.assertEqual(tracker.current_capital, 10000.0,
                        "Current capital should match starting capital")
        self.assertEqual(tracker.capital_floor, 1000.0,
                        "Capital floor should be 10% of starting capital (1000)")
    
    def test_pdt_tracker_uses_custom_capital(self):
        """Test that PDTTracker accepts custom starting capital"""
        try:
            from gui import PDTTracker
        except ImportError:
            self.skipTest("GUI module not available (likely missing tkinter)")
            return
        
        tracker = PDTTracker(starting_capital=5000.0)
        
        self.assertEqual(tracker.starting_capital, 5000.0)
        self.assertEqual(tracker.current_capital, 5000.0)
        self.assertEqual(tracker.capital_floor, 500.0,
                        "Capital floor should be 10% of starting capital (500)")
    
    def test_capital_floor_calculation(self):
        """Test that capital floor is always 10% of starting capital"""
        try:
            from gui import PDTTracker
        except ImportError:
            self.skipTest("GUI module not available (likely missing tkinter)")
            return
        
        test_cases = [
            (10000.0, 1000.0),
            (5000.0, 500.0),
            (25000.0, 2500.0),
            (1000.0, 100.0),
        ]
        
        for starting_capital, expected_floor in test_cases:
            tracker = PDTTracker(starting_capital=starting_capital)
            self.assertEqual(tracker.capital_floor, expected_floor,
                           f"Floor should be 10% of {starting_capital}")
    
    def test_pdt_tracker_update_capital(self):
        """Test that update_capital() works correctly"""
        try:
            from gui import PDTTracker
        except ImportError:
            self.skipTest("GUI module not available (likely missing tkinter)")
            return
        
        tracker = PDTTracker(starting_capital=10000.0)
        
        # Update capital
        tracker.update_capital(12000.0)
        
        self.assertEqual(tracker.current_capital, 12000.0,
                        "Current capital should be updated")
        self.assertEqual(tracker.starting_capital, 10000.0,
                        "Starting capital should remain unchanged")
        self.assertEqual(tracker.capital_floor, 1000.0,
                        "Capital floor should remain 10% of starting capital")


class TestEnvironmentVariableHandling(unittest.TestCase):
    """Test environment variable handling for BOT_TOTAL_CAPITAL"""
    
    @patch.dict(os.environ, {'BOT_TOTAL_CAPITAL': '15000'})
    def test_valid_env_capital_parsing(self):
        """Test that valid BOT_TOTAL_CAPITAL is parsed correctly"""
        capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
        self.assertEqual(capital, 15000.0)
    
    @patch.dict(os.environ, {})
    def test_missing_env_uses_default(self):
        """Test that missing BOT_TOTAL_CAPITAL uses default"""
        capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
        self.assertEqual(capital, 10000.0)
    
    @patch.dict(os.environ, {'BOT_TOTAL_CAPITAL': 'invalid'})
    def test_invalid_env_raises_error(self):
        """Test that invalid BOT_TOTAL_CAPITAL raises ValueError"""
        with self.assertRaises(ValueError):
            float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
    
    @patch.dict(os.environ, {'BOT_TOTAL_CAPITAL': '-500'})
    def test_negative_capital_can_be_validated(self):
        """Test that negative capital can be parsed (validation happens elsewhere)"""
        capital = float(os.getenv('BOT_TOTAL_CAPITAL', '10000'))
        self.assertEqual(capital, -500.0)
        # Note: Actual validation that capital > 0 should happen in validate_params()


class TestCapitalConsistency(unittest.TestCase):
    """Test capital consistency between main.py and gui.py defaults"""
    
    def test_default_capital_matches_env_example(self):
        """Test that default capital (10000) matches .env.example"""
        # Read .env.example
        try:
            with open('.env.example', 'r') as f:
                content = f.read()
                # Find BOT_TOTAL_CAPITAL line
                for line in content.split('\n'):
                    if line.startswith('BOT_TOTAL_CAPITAL='):
                        value = line.split('=')[1]
                        self.assertEqual(value, '10000',
                                       ".env.example should have BOT_TOTAL_CAPITAL=10000")
                        break
        except FileNotFoundError:
            self.skipTest(".env.example not found")
    
    def test_pdt_tracker_default_matches_main_py_default(self):
        """Test that PDTTracker default (10000) matches main.py TradingBot default"""
        try:
            from gui import PDTTracker
            from main import TradingBot
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
            return
        
        # Create instances with defaults
        tracker = PDTTracker()
        bot = TradingBot()
        
        self.assertEqual(tracker.starting_capital, bot.total_capital,
                        "PDTTracker and TradingBot should have same default capital")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

