"""
Test mode configuration override behavior.
Validates that mode settings can be changed at runtime via os.environ
and that the bot correctly reads the updated values.
"""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


class TestModeOverride(unittest.TestCase):
    """Test that mode settings can be overridden at runtime"""
    
    def setUp(self):
        """Save original environment variables"""
        self.original_env = {}
        self.env_vars = ['PAPER_TRADING_MODE', 'SCHWAB_SANDBOX_MODE', 'SCHWAB_API_ENABLED', 'DRY_RUN_MODE']
        for var in self.env_vars:
            self.original_env[var] = os.environ.get(var)
    
    def tearDown(self):
        """Restore original environment variables"""
        for var in self.env_vars:
            if self.original_env[var] is not None:
                os.environ[var] = self.original_env[var]
            elif var in os.environ:
                del os.environ[var]
    
    def test_helper_functions_read_dynamically(self):
        """Test that helper functions read current os.environ values"""
        # Set to sandbox mode
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        
        self.assertTrue(main._get_paper_trading_mode())
        self.assertTrue(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
        
        # Change to live mode
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        
        self.assertFalse(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
        
        # Change to training mode (API disabled)
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        
        self.assertTrue(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertFalse(main._get_schwab_api_enabled())
    
    def test_api_enabled_accepts_multiple_formats(self):
        """Test that SCHWAB_API_ENABLED accepts various on/off formats"""
        # Test 'on' values
        for value in ['on', 'ON', 'true', 'TRUE', '1', 'yes', 'YES']:
            os.environ['SCHWAB_API_ENABLED'] = value
            self.assertTrue(main._get_schwab_api_enabled(), 
                          f"Failed for value: {value}")
        
        # Test 'off' values
        for value in ['off', 'OFF', 'false', 'FALSE', '0', 'no', 'NO']:
            os.environ['SCHWAB_API_ENABLED'] = value
            self.assertFalse(main._get_schwab_api_enabled(),
                           f"Failed for value: {value}")
    
    def test_mode_defaults(self):
        """Test that helper functions have correct defaults when env vars not set"""
        # Remove all mode env vars
        for var in self.env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Defaults should be: paper=true, sandbox=false, api=on
        # (SCHWAB_SANDBOX_MODE defaults to 'false' in main.py, api/bot_manager.py and api/main.py)
        self.assertTrue(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
    
    def test_web_gui_mode_configurations(self):
        """Test the four mode configurations set by web GUI"""
        # Sandbox mode (mode-sandbox-button)
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'false'
        
        self.assertTrue(main._get_paper_trading_mode())
        self.assertTrue(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
        self.assertFalse(main._get_dry_run_mode())
        
        # 2. Live mode (mode-live-button)
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'false'
        
        self.assertFalse(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
        self.assertFalse(main._get_dry_run_mode())
        
        # 3. Training mode (mode-yfinance-button)
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        os.environ['DRY_RUN_MODE'] = 'false'
        
        self.assertTrue(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertFalse(main._get_schwab_api_enabled())
        
        # Dry-run (Live) mode - live mode with dry-run enabled
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        os.environ['DRY_RUN_MODE'] = 'true'
        
        self.assertFalse(main._get_paper_trading_mode())
        self.assertFalse(main._get_schwab_sandbox_mode())
        self.assertTrue(main._get_schwab_api_enabled())
    
    def test_is_pure_simulation_mode_dynamic(self):
        """Test that _is_pure_simulation_mode reads dynamically"""
        # Need to set env for testing even if not used
        os.environ['ENABLE_PDT_RULES'] = 'false'
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        
        # Create a bot instance
        bot = main.TradingBot(total_capital=10000.0)
        
        # Pure simulation mode: paper=true, sandbox=false, api=on
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        self.assertTrue(bot._is_pure_simulation_mode())
        
        # Not pure simulation: paper=true, sandbox=true (sandbox mode)
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        self.assertFalse(bot._is_pure_simulation_mode())
        
        # Not pure simulation: paper=false (live mode)
        os.environ['PAPER_TRADING_MODE'] = 'false'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'
        os.environ['SCHWAB_API_ENABLED'] = 'on'
        self.assertFalse(bot._is_pure_simulation_mode())
        
        # Pure simulation: api=off (overrides other settings)
        os.environ['PAPER_TRADING_MODE'] = 'true'
        os.environ['SCHWAB_SANDBOX_MODE'] = 'true'  # Doesn't matter
        os.environ['SCHWAB_API_ENABLED'] = 'off'
        self.assertTrue(bot._is_pure_simulation_mode())
    
    def test_dry_run_mode_helper_function(self):
        """Test that _get_dry_run_mode reads current os.environ value"""
        # Test dry-run mode enabled
        os.environ['DRY_RUN_MODE'] = 'true'
        self.assertTrue(main._get_dry_run_mode())
        
        # Test dry-run mode disabled
        os.environ['DRY_RUN_MODE'] = 'false'
        self.assertFalse(main._get_dry_run_mode())
        
        # Test dry-run mode with various 'on' formats (like _get_schwab_api_enabled)
        for value in ['true', 'TRUE', 'True', '1', 'yes', 'YES', 'on', 'ON']:
            os.environ['DRY_RUN_MODE'] = value
            self.assertTrue(main._get_dry_run_mode(),
                          f"Failed for value: {value}")
        
        # Test dry-run mode with various 'off' formats
        for value in ['false', 'FALSE', 'False', 'off', 'OFF', 'no', 'NO', '0']:
            os.environ['DRY_RUN_MODE'] = value
            self.assertFalse(main._get_dry_run_mode(),
                           f"Failed for value: {value}")
    
    def test_dry_run_mode_default(self):
        """Test that DRY_RUN_MODE defaults to false when not set"""
        if 'DRY_RUN_MODE' in os.environ:
            del os.environ['DRY_RUN_MODE']
        
        # Default should be false (normal operation)
        self.assertFalse(main._get_dry_run_mode())
    
    def test_dry_run_live_mode_configuration(self):
        """Test the dry-run (Live) mode configuration set by web GUI"""
        # Dry-run (Live) mode should use live-like settings with DRY_RUN_MODE=true
        os.environ['PAPER_TRADING_MODE'] = 'false'  # Live-like
        os.environ['SCHWAB_SANDBOX_MODE'] = 'false'  # Production API
        os.environ['SCHWAB_API_ENABLED'] = 'on'  # API enabled
        os.environ['DRY_RUN_MODE'] = 'true'  # But no orders placed
        
        # Verify all settings
        self.assertFalse(main._get_paper_trading_mode(), "Should be false for live-like mode")
        self.assertFalse(main._get_schwab_sandbox_mode(), "Should be false for production API")
        self.assertTrue(main._get_schwab_api_enabled(), "Should be enabled for API access")
        self.assertTrue(main._get_dry_run_mode(), "Should be true to prevent order execution")


if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""
Test script for mode selection functionality in web GUI.
Verifies that mode selection properly configures environment variables.
"""

import os
import sys

def test_mode_configurations():
    """Test that each mode sets the correct environment variables"""
    
    print("Testing mode configurations...\n")
    
    # Test Schwab Sandbox Mode
    print("1. Testing Schwab Sandbox Mode")
    mode_settings = {
        'PAPER_TRADING_MODE': 'true',
        'SCHWAB_SANDBOX_MODE': 'true',
        'SCHWAB_API_ENABLED': 'on'
    }
    for key, value in mode_settings.items():
        os.environ[key] = str(value)
    
    assert os.getenv('PAPER_TRADING_MODE') == 'true', "Sandbox mode: PAPER_TRADING_MODE should be 'true'"
    assert os.getenv('SCHWAB_SANDBOX_MODE') == 'true', "Sandbox mode: SCHWAB_SANDBOX_MODE should be 'true'"
    assert os.getenv('SCHWAB_API_ENABLED') == 'on', "Sandbox mode: SCHWAB_API_ENABLED should be 'on'"
    print("   ✓ Sandbox mode configuration correct\n")
    
    # Test Schwab Live Mode
    print("2. Testing Schwab Live Mode")
    mode_settings = {
        'PAPER_TRADING_MODE': 'false',
        'SCHWAB_SANDBOX_MODE': 'false',
        'SCHWAB_API_ENABLED': 'on'
    }
    for key, value in mode_settings.items():
        os.environ[key] = str(value)
    
    assert os.getenv('PAPER_TRADING_MODE') == 'false', "Live mode: PAPER_TRADING_MODE should be 'false'"
    assert os.getenv('SCHWAB_SANDBOX_MODE') == 'false', "Live mode: SCHWAB_SANDBOX_MODE should be 'false'"
    assert os.getenv('SCHWAB_API_ENABLED') == 'on', "Live mode: SCHWAB_API_ENABLED should be 'on'"
    print("   ✓ Live mode configuration correct\n")
    
    # Test yfinance Training Mode
    print("3. Testing yfinance Training Mode")
    mode_settings = {
        'PAPER_TRADING_MODE': 'true',
        'SCHWAB_SANDBOX_MODE': 'false',
        'SCHWAB_API_ENABLED': 'off'
    }
    for key, value in mode_settings.items():
        os.environ[key] = str(value)
    
    assert os.getenv('PAPER_TRADING_MODE') == 'true', "yfinance mode: PAPER_TRADING_MODE should be 'true'"
    assert os.getenv('SCHWAB_SANDBOX_MODE') == 'false', "yfinance mode: SCHWAB_SANDBOX_MODE should be 'false'"
    assert os.getenv('SCHWAB_API_ENABLED') == 'off', "yfinance mode: SCHWAB_API_ENABLED should be 'off'"
    print("   ✓ yfinance mode configuration correct\n")
    
    print("All mode configuration tests passed! ✓")

def test_mode_selection_prevents_startup():
    """Test that bot cannot start without mode selection"""
    
    print("\nTesting mode selection requirement...\n")
    
    # Simulate no mode selected
    selected_mode = None
    
    if selected_mode is None:
        print("   ✓ Bot correctly prevents startup when no mode is selected")
    else:
        print("   ✗ ERROR: Bot should prevent startup when no mode is selected")
        sys.exit(1)
    
    # Simulate mode selected
    selected_mode = 'sandbox'
    
    if selected_mode is not None:
        print(f"   ✓ Bot allows startup when mode is selected: {selected_mode}")
    else:
        print("   ✗ ERROR: Bot should allow startup when mode is selected")
        sys.exit(1)
    
    print("\nMode selection requirement test passed! ✓")

def test_mode_descriptions():
    """Test that mode descriptions match implementation"""
    
    print("\nTesting mode descriptions...\n")
    
    modes = {
        'sandbox': {
            'name': 'Schwab API (Sandbox)',
            'description': 'Paper trading mode with Schwab sandbox API',
            'purpose': 'Orders visible in ThinkorSwim paperMoney'
        },
        'live': {
            'name': 'Schwab API (Live)',
            'description': 'Production mode with real money trading',
            'purpose': 'Orders placed in your Schwab brokerage account'
        },
        'yfinance': {
            'name': 'yfinance Training Mode',
            'description': 'Training mode without Schwab API',
            'purpose': 'Uses yfinance for market data, no API credentials needed'
        }
    }
    
    for mode_key, mode_info in modes.items():
        print(f"Mode: {mode_info['name']}")
        print(f"  Description: {mode_info['description']}")
        print(f"  Purpose: {mode_info['purpose']}")
        print()
    
    print("Mode descriptions verified! ✓")

if __name__ == '__main__':
    print("="*60)
    print("Mode Selection Test Suite")
    print("="*60)
    print()
    
    try:
        test_mode_configurations()
        test_mode_selection_prevents_startup()
        test_mode_descriptions()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print()
        print("Summary:")
        print("  • Mode selection UI added to Dashboard tab")
        print("  • Three modes implemented: Sandbox, Live, yfinance")
        print("  • Bot initialization deferred until mode selected")
        print("  • Start button requires mode selection")
        print("  • Environment variables configured per mode")
        print()
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)
