#!/usr/bin/env python3
"""
Test script for mode isolation fixes
Verifies that sandbox and live modes enforce strict "no fallback" policy
"""

import os
import unittest
from unittest.mock import patch

# Set test environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['SCHWAB_API_ENABLED'] = 'on'
os.environ['SCHWAB_API_KEY'] = 'test_key'
os.environ['SCHWAB_APP_SECRET'] = 'test_secret'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['ALLOW_RANDOM_FALLBACK'] = 'true'  # Enable random fallback for tests

# Import after setting environment variables
import main



class TestSandboxModeNoFallback(unittest.TestCase):
    """Test that sandbox mode enforces strict no fallback policy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = main.TradingBot(total_capital=10000.0)
    
    @patch.object(main.TradingBot, 'fetch_real_stock_price')
    @patch.object(main.TradingBot, 'fetch_schwab_stock_price')
    def test_sandbox_mode_no_yfinance_fallback(self, mock_schwab, mock_yfinance):
        """Test that sandbox mode does NOT fallback to yfinance when Schwab API fails"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        # Mock yfinance (should not be called)
        mock_yfinance.return_value = (150.0, 1000000)
        
        # In sandbox mode, should raise error immediately (no yfinance fallback)
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        error_msg = str(context.exception).lower()
        self.assertIn('critical error', error_msg)
        self.assertIn('schwab sandbox api failed', error_msg)
        self.assertIn('stopped immediately', error_msg)
        
        # Verify yfinance was NOT called (no fallback)
        mock_yfinance.assert_not_called()
    
    @patch.object(main.TradingBot, 'fetch_real_stock_price')
    @patch.object(main.TradingBot, 'fetch_schwab_stock_price')
    def test_sandbox_mode_no_random_fallback(self, mock_schwab, mock_yfinance):
        """Test that sandbox mode does NOT fallback to random simulation"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        # Mock yfinance (should not be called)
        mock_yfinance.return_value = (150.0, 1000000)
        
        # Even with use_random_fallback=True, sandbox mode should raise error
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        error_msg = str(context.exception).lower()
        self.assertIn('critical error', error_msg)
        self.assertIn('sandbox', error_msg)


class TestLiveModeNoFallback(unittest.TestCase):
    """Test that live mode enforces strict no fallback policy"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Temporarily switch to live mode for these tests
        self.original_paper_mode = os.environ.get('PAPER_TRADING_MODE')
        os.environ['PAPER_TRADING_MODE'] = 'false'
        # Need to reload to pick up new env value
        import importlib
        importlib.reload(main)
        self.bot = main.TradingBot(total_capital=10000.0)
    
    def tearDown(self):
        """Restore original environment"""
        if self.original_paper_mode:
            os.environ['PAPER_TRADING_MODE'] = self.original_paper_mode
        else:
            os.environ.pop('PAPER_TRADING_MODE', None)
        # Reload main to pick up restored environment
        import importlib
        importlib.reload(main)
    
    @patch('main.TradingBot.fetch_schwab_stock_price')
    def test_live_mode_no_yfinance_fallback(self, mock_schwab):
        """Test that live mode does NOT fallback to yfinance when Schwab API fails"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        
        # In live mode, should raise error immediately (no yfinance fallback)
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=False)
        
        error_msg = str(context.exception).lower()
        self.assertIn('critical error', error_msg)
        self.assertIn('schwab production api failed', error_msg)
    
    @patch('main.TradingBot.fetch_schwab_stock_price')
    def test_live_mode_no_random_fallback(self, mock_schwab):
        """Test that live mode NEVER uses random simulation"""
        # Mock Schwab API failure
        mock_schwab.return_value = None
        
        # Live mode should never use random fallback, regardless of parameter
        with self.assertRaises(ValueError):
            self.bot.get_stock_price('AAPL', use_random_fallback=True)


class TestAPIDisabledMode(unittest.TestCase):
    """Test that API disabled mode works correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Switch to API disabled mode
        self.original_api_enabled = os.environ.get('SCHWAB_API_ENABLED')
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        # Need to reload to pick up new env value
        import importlib
        importlib.reload(main)
        self.bot = main.TradingBot(total_capital=10000.0)
    
    def tearDown(self):
        """Restore original environment"""
        if self.original_api_enabled:
            os.environ['SCHWAB_API_ENABLED'] = self.original_api_enabled
        else:
            os.environ.pop('SCHWAB_API_ENABLED', None)
        # Reload main to pick up restored environment
        import importlib
        importlib.reload(main)
    
    @patch('main.TradingBot.fetch_real_stock_price')
    @patch('main.TradingBot.fetch_schwab_stock_price')
    def test_api_disabled_skips_schwab(self, mock_schwab, mock_yfinance):
        """Test that API disabled mode skips Schwab API entirely"""
        # Mock yfinance success
        mock_yfinance.return_value = (150.0, 1000000)
        
        result = self.bot.get_stock_price('AAPL')
        
        # Should NOT call Schwab at all
        mock_schwab.assert_not_called()
        # Should call yfinance
        mock_yfinance.assert_called_once()
        self.assertEqual(result, (150.0, 1000000))
    
    @patch('main.TradingBot.fetch_real_stock_price')
    def test_api_disabled_allows_random_fallback(self, mock_yfinance):
        """Test that API disabled mode allows random fallback"""
        # Mock yfinance failure
        mock_yfinance.return_value = None
        
        # Should not raise error, should return random price
        result = self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        self.assertIsNotNone(result)
        price, volume = result
        self.assertGreater(price, 0)
        self.assertGreater(volume, 0)


class TestModeDetection(unittest.TestCase):
    """Test that mode detection works correctly in trade recording"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Save original environment
        self.original_api_enabled = os.environ.get('SCHWAB_API_ENABLED')
    
    def tearDown(self):
        """Restore original environment"""
        if self.original_api_enabled:
            os.environ['SCHWAB_API_ENABLED'] = self.original_api_enabled
        else:
            os.environ.pop('SCHWAB_API_ENABLED', None)
        # Reload main to pick up restored environment
        import importlib
        importlib.reload(main)
    
    def test_api_disabled_mode_detection(self):
        """Test that trades are tagged with correct mode"""
        # Set API disabled mode
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        import importlib
        importlib.reload(main)
        bot = main.TradingBot(total_capital=10000.0)
        
        # Record a trade
        bot.record_trade('AAPL', 'BUY', 10, 150.0, True)
        
        # Check that trade is tagged with api_disabled mode
        self.assertEqual(len(bot.trade_history), 1)
        self.assertEqual(bot.trade_history[0]['mode'], 'api_disabled')


if __name__ == '__main__':
    print("="*60)
    print("Mode Isolation Test Suite")
    print("Testing strict 'no fallback' policy for sandbox and live modes")
    print("="*60)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
#!/usr/bin/env python3
"""
Test script for mode isolation, PDT tracking, and GUI alert fixes.
Validates the changes made to address incomplete mode isolation issues.
"""

import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import importlib

# Try to import gui module (may fail in headless environments)
try:
    import gui
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    gui = None

# Save original environment values
_original_env = {
    'PAPER_TRADING_MODE': os.environ.get('PAPER_TRADING_MODE', 'true'),
    'SCHWAB_SANDBOX_MODE': os.environ.get('SCHWAB_SANDBOX_MODE', 'false'),
    'SCHWAB_API_ENABLED': os.environ.get('SCHWAB_API_ENABLED', 'on'),
    'SCHWAB_API_KEY': os.environ.get('SCHWAB_API_KEY', ''),
    'SCHWAB_APP_SECRET': os.environ.get('SCHWAB_APP_SECRET', ''),
    'ENABLE_PDT_RULES': os.environ.get('ENABLE_PDT_RULES', 'false'),
    'ALLOW_RANDOM_FALLBACK': os.environ.get('ALLOW_RANDOM_FALLBACK', 'true'),
    'BOT_TOTAL_CAPITAL': os.environ.get('BOT_TOTAL_CAPITAL', '10000'),
    'SIMULATED_WIN_RATE': os.environ.get('SIMULATED_WIN_RATE', '0.7'),
}

# Set test environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
os.environ['SCHWAB_API_ENABLED'] = 'off'
os.environ['SCHWAB_API_KEY'] = 'test_key'
os.environ['SCHWAB_APP_SECRET'] = 'test_secret'
os.environ['ENABLE_PDT_RULES'] = 'false'
os.environ['ALLOW_RANDOM_FALLBACK'] = 'true'
os.environ['BOT_TOTAL_CAPITAL'] = '10000'
os.environ['SIMULATED_WIN_RATE'] = '0.7'

# Force reload of main module to pick up new environment values
if 'main' in sys.modules:
    import main
    importlib.reload(main)
else:
    import main


class TestModeIsolationWithAPIDisabled(unittest.TestCase):
    """Test that _is_pure_simulation_mode() correctly handles SCHWAB_API_ENABLED=off"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class"""
        # Ensure SCHWAB_API_ENABLED is off for these tests
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        if 'main' in sys.modules:
            importlib.reload(main)
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = main.TradingBot(total_capital=10000.0)
    
    def test_pure_simulation_mode_with_api_disabled(self):
        """Test that SCHWAB_API_ENABLED=off is considered pure simulation mode"""
        # With SCHWAB_API_ENABLED=off, should be pure simulation mode
        self.assertTrue(self.bot._is_pure_simulation_mode())
        
    def test_pure_simulation_mode_description(self):
        """Test that _is_pure_simulation_mode docstring is accurate"""
        doc = self.bot._is_pure_simulation_mode.__doc__
        self.assertIn('API explicitly disabled', doc)
        self.assertIn('SCHWAB_API_ENABLED=off', doc)
    
    @patch.object(main.TradingBot, 'fetch_real_stock_price')
    def test_random_fallback_allowed_with_api_disabled(self, mock_yfinance):
        """Test that random fallback is allowed when API is disabled"""
        # Mock yfinance failure
        mock_yfinance.return_value = None
        
        # In API disabled mode with random fallback enabled, should use random prices
        price, volume = self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        # Should succeed and return a price
        self.assertIsNotNone(price)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0)
        self.assertIsNotNone(volume)
        self.assertIsInstance(volume, int)
        self.assertGreater(volume, 0)


class TestPDTTrackingInBacktesting(unittest.TestCase):
    """Test that day trades are tracked consistently in backtesting scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = main.TradingBot(total_capital=10000.0)
        # Clear any existing day trades
        self.bot.day_trades = []
    
    def test_day_trade_tracked_on_same_day_close(self):
        """Test that day trades are tracked when entry and exit are on same day"""
        symbol = 'TEST'
        entry_price = 100.0
        exit_price = 105.0
        quantity = 10
        
        # Open a position
        self.bot.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'high_price': entry_price,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': datetime.now().isoformat()
        }
        
        # Close the position on the same day
        pnl_info = self.bot.close_position(symbol, exit_price, exit_reason='test')
        
        # Verify pnl_info contains entry_time
        self.assertIsNotNone(pnl_info)
        self.assertIn('exit_conditions', pnl_info)
        self.assertIn('entry_time', pnl_info['exit_conditions'])
        
        # Simulate the day trade tracking logic from backtesting loop
        entry_time_str = pnl_info['exit_conditions']['entry_time']
        entry_date = datetime.fromisoformat(entry_time_str).date()
        exit_date = datetime.now().date()
        
        if entry_date == exit_date:
            self.bot.add_day_trade(symbol)
        
        # Verify day trade was tracked
        self.assertEqual(len(self.bot.day_trades), 1)
        self.assertEqual(self.bot.day_trades[0][1], symbol)
    
    def test_day_trade_not_tracked_on_different_day_close(self):
        """Test that day trades are NOT tracked when entry and exit are on different days"""
        symbol = 'TEST'
        entry_price = 100.0
        exit_price = 105.0
        quantity = 10
        
        # Open a position with entry time 2 days ago
        yesterday = datetime.now() - timedelta(days=2)
        self.bot.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'high_price': entry_price,
            'stop_percent': 0.03,
            'partial_exit_done': False,
            'entry_time': yesterday.isoformat()
        }
        
        # Close the position today
        pnl_info = self.bot.close_position(symbol, exit_price, exit_reason='test')
        
        # Simulate the day trade tracking logic
        entry_time_str = pnl_info['exit_conditions']['entry_time']
        entry_date = datetime.fromisoformat(entry_time_str).date()
        exit_date = datetime.now().date()
        
        if entry_date == exit_date:
            self.bot.add_day_trade(symbol)
        
        # Verify day trade was NOT tracked (different days)
        self.assertEqual(len(self.bot.day_trades), 0)


class TestSimulatedWinRate(unittest.TestCase):
    """Test that SIMULATED_WIN_RATE defaults to 0.7 (70%)"""
    
    def test_simulated_win_rate_default(self):
        """Test that SIMULATED_WIN_RATE is set to 0.7"""
        # Check the global variable
        self.assertEqual(main.SIMULATED_WIN_RATE, 0.7)
    
    def test_simulated_win_rate_from_env(self):
        """Test that SIMULATED_WIN_RATE can be overridden via environment"""
        # Already set to 0.7 in setUp via os.environ
        # Just verify it was loaded correctly
        self.assertAlmostEqual(main.SIMULATED_WIN_RATE, 0.7, places=1)


class TestGUIImports(unittest.TestCase):
    """Test that GUI imports the necessary variables for data source alerts"""
    
    def test_gui_imports_yfinance_available(self):
        """Test that gui.py imports YFINANCE_AVAILABLE"""
        try:
            # Force reload of gui to pick up current environment
            import gui
            importlib.reload(gui)
            # Check if YFINANCE_AVAILABLE is accessible in gui module
            self.assertTrue(hasattr(gui, 'YFINANCE_AVAILABLE'))
        except ImportError as e:
            self.skipTest(f"GUI module not available: {e}")
    
    def test_gui_imports_schwab_api_enabled(self):
        """Test that gui.py imports SCHWAB_API_ENABLED"""
        try:
            import gui
            # Check if SCHWAB_API_ENABLED is accessible in gui module
            self.assertTrue(hasattr(gui, 'SCHWAB_API_ENABLED'))
        except ImportError as e:
            self.skipTest(f"GUI module not available: {e}")
    
    def test_gui_imports_allow_random_fallback(self):
        """Test that gui.py imports ALLOW_RANDOM_FALLBACK"""
        try:
            import gui
            # Check if ALLOW_RANDOM_FALLBACK is accessible in gui module
            self.assertTrue(hasattr(gui, 'ALLOW_RANDOM_FALLBACK'))
        except ImportError as e:
            self.skipTest(f"GUI module not available: {e}")


def restore_environment():
    """Restore original environment values"""
    for key, value in _original_env.items():
        if value:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


if __name__ == '__main__':
    try:
        # Run tests with verbose output
        unittest.main(verbosity=2, exit=False)
    finally:
        # Restore original environment
        restore_environment()
        # Reload main to pick up restored environment
        if 'main' in sys.modules:
            importlib.reload(main)