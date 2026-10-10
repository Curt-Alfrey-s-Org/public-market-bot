#!/usr/bin/env python3
"""
Test suite for Copilot Debug Logger
Tests standalone logger and integration with TradingBot
"""

import os
# Disable PDT rules for testing
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')

import unittest
import tempfile
import shutil
import json
from pathlib import Path

from copilot_debug_logger import CopilotDebugLogger, get_debug_logger


class TestCopilotDebugLogger(unittest.TestCase):
    """Test CopilotDebugLogger functionality"""
    
    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.logger = CopilotDebugLogger(log_dir=self.test_dir, enabled=True)
    
    def tearDown(self):
        """Clean up test environment"""
        # Ensure logger file handles are closed before removing the directory
        if hasattr(self, "logger") and self.logger is not None:
            try:
                # Call close to ensure file handle is released
                self.logger.close()
            except Exception:
                # Ignore errors during cleanup
                pass
        shutil.rmtree(self.test_dir)
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        self.assertTrue(self.logger.enabled)
        self.assertIsNotNone(self.logger.session_id)
        self.assertTrue(self.logger.log_file.exists())
    
    def test_disabled_logger(self):
        """Test that disabled logger doesn't create log files"""
        disabled_logger = CopilotDebugLogger(log_dir=self.test_dir, enabled=False)
        self.assertFalse(disabled_logger.enabled)
        # Logging should not create additional files
        initial_files = list(Path(self.test_dir).glob("*.jsonl"))
        disabled_logger.log_initialization({'test': 'data'})
        final_files = list(Path(self.test_dir).glob("*.jsonl"))
        # Only the enabled logger's file should exist
        self.assertEqual(len(initial_files), len(final_files))
    
    def test_log_initialization(self):
        """Test logging initialization data"""
        config = {
            'total_capital': 10000.0,
            'risk_threshold': 0.02,
            'paper_trading_mode': True
        }
        self.logger.log_initialization(config)
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            # Should have session_start + initialization entries
            self.assertGreaterEqual(len(lines), 2)
            
            # Parse and verify initialization entry
            init_entry = json.loads(lines[1])
            self.assertEqual(init_entry['event_type'], 'bot_initialization')
            self.assertEqual(init_entry['config']['total_capital'], 10000.0)
    
    def test_log_decision(self):
        """Test logging decision points"""
        self.logger.log_decision(
            decision_type='trade_signal',
            context={'symbol': 'AAPL', 'price': 150.0},
            result='BUY',
            rationale='Strong momentum indicators'
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'decision')
            self.assertEqual(last_entry['decision_type'], 'trade_signal')
            self.assertEqual(last_entry['result'], 'BUY')
    
    def test_log_trade_execution(self):
        """Test logging trade execution"""
        self.logger.log_trade_execution(
            symbol='AAPL',
            action='BUY',
            quantity=10.0,
            price=150.25,
            metadata={'strategy': 'momentum'}
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'trade_execution')
            self.assertEqual(last_entry['symbol'], 'AAPL')
            self.assertEqual(last_entry['action'], 'BUY')
            self.assertEqual(last_entry['quantity'], 10.0)
    
    def test_log_strategy_selection(self):
        """Test logging strategy selection"""
        self.logger.log_strategy_selection(
            symbol='AAPL',
            strategies_evaluated=['momentum', 'mean_reversion', 'breakout'],
            selected_strategy='momentum',
            scores={'momentum': 0.85, 'mean_reversion': 0.65, 'breakout': 0.70}
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'strategy_selection')
            self.assertEqual(last_entry['selected_strategy'], 'momentum')
            self.assertEqual(last_entry['scores']['momentum'], 0.85)
    
    def test_log_error(self):
        """Test logging errors"""
        self.logger.log_error(
            error_type='API_ERROR',
            error_message='Failed to fetch price',
            context={'symbol': 'AAPL'},
            stack_trace='Traceback...'
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'error')
            self.assertEqual(last_entry['error_type'], 'API_ERROR')
    
    def test_log_state_snapshot(self):
        """Test logging state snapshots"""
        self.logger.log_state_snapshot(
            state_type='positions',
            state_data={
                'AAPL': {'quantity': 10, 'entry_price': 150.0},
                'total_capital': 9850.0
            }
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'state_snapshot')
            self.assertEqual(last_entry['state_type'], 'positions')
    
    def test_log_performance_metric(self):
        """Test logging performance metrics"""
        self.logger.log_performance_metric(
            metric_name='win_rate',
            metric_value=0.65,
            context={'total_trades': 20}
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'performance_metric')
            self.assertEqual(last_entry['metric_name'], 'win_rate')
            self.assertEqual(last_entry['metric_value'], 0.65)
    
    def test_log_api_call(self):
        """Test logging API calls"""
        self.logger.log_api_call(
            api_name='schwab',
            method='get_quotes',
            success=True,
            duration_ms=125.5,
            response_summary={'symbols': 5}
        )
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'api_call')
            self.assertEqual(last_entry['api_name'], 'schwab')
            self.assertTrue(last_entry['success'])
    
    def test_log_session_end(self):
        """Test logging session end"""
        self.logger.log_session_end({
            'total_trades': 10,
            'win_rate': 0.70,
            'total_pnl': 150.0
        })
        
        # Verify log entry
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
            self.assertEqual(last_entry['event_type'], 'session_end')
            self.assertEqual(last_entry['summary']['win_rate'], 0.70)
    
    def test_event_id_increment(self):
        """Test that event IDs increment properly"""
        self.logger.log_initialization({'test': 'data'})
        self.logger.log_decision('test', {}, 'result')
        self.logger.log_trade_execution('AAPL', 'BUY', 10, 150.0)
        
        # Verify event IDs are incrementing
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            event_ids = [json.loads(line)['event_id'] for line in lines]
            self.assertEqual(event_ids, list(range(1, len(event_ids) + 1)))
    
    def test_get_log_file_path(self):
        """Test getting log file path"""
        path = self.logger.get_log_file_path()
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())
        self.assertTrue(str(path).endswith('.jsonl'))
    
    def test_env_variable_control(self):
        """Test that COPILOT_DEBUG_MODE env variable controls logger"""
        original_value = os.environ.get('COPILOT_DEBUG_MODE')

        def cleanup():
            if original_value is None:
                os.environ.pop('COPILOT_DEBUG_MODE', None)
            else:
                os.environ['COPILOT_DEBUG_MODE'] = original_value

        self.addCleanup(cleanup)

        # Test with env variable set to true
        os.environ['COPILOT_DEBUG_MODE'] = 'true'
        logger1 = CopilotDebugLogger(log_dir=self.test_dir)
        self.assertTrue(logger1.enabled)
        
        # Test with env variable set to false
        os.environ['COPILOT_DEBUG_MODE'] = 'false'
        logger2 = CopilotDebugLogger(log_dir=self.test_dir)
        self.assertFalse(logger2.enabled)


class TestDebugLoggerSingleton(unittest.TestCase):
    """Test the global debug logger singleton"""
    
    def setUp(self):
        """Reset singleton before each test"""
        from copilot_debug_logger import reset_debug_logger
        reset_debug_logger()
    
    def tearDown(self):
        """Reset singleton after each test"""
        from copilot_debug_logger import reset_debug_logger
        reset_debug_logger()
    
    def test_get_debug_logger_singleton(self):
        """Test that get_debug_logger returns same instance"""
        logger1 = get_debug_logger()
        logger2 = get_debug_logger()
        self.assertIs(logger1, logger2)


class TestTradingBotIntegration(unittest.TestCase):
    """Test CopilotDebugLogger integration with TradingBot"""
    
    def setUp(self):
        """Set up test environment"""
        # Enable debug mode for testing
        os.environ['COPILOT_DEBUG_MODE'] = 'true'
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        # Reset singleton to prevent test pollution
        from copilot_debug_logger import reset_debug_logger
        reset_debug_logger()
        
        if 'COPILOT_DEBUG_MODE' in os.environ:
            del os.environ['COPILOT_DEBUG_MODE']
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_bot_has_debug_logger(self):
        """Test that TradingBot initializes with debug logger"""
        # Import here to avoid circular dependency issues
        try:
            from main import TradingBot
            bot = TradingBot(total_capital=10000.0)
            
            # Should have debug logger
            self.assertIsNotNone(bot.debug_logger)
            
            # Should be enabled (we set COPILOT_DEBUG_MODE=true)
            if bot.debug_logger:
                self.assertTrue(bot.debug_logger.enabled)
                
                # Should have logged initialization
                log_file = bot.debug_logger.get_log_file_path()
                if log_file:
                    self.assertTrue(log_file.exists())
                    
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Should have at least session_start and bot_initialization
                        self.assertGreaterEqual(len(lines), 2)
                        
                        # Check for bot_initialization event
                        events = [json.loads(line) for line in lines]
                        init_events = [e for e in events if e['event_type'] == 'bot_initialization']
                        self.assertEqual(len(init_events), 1)
                        
                        # Verify initialization has config data
                        init_event = init_events[0]
                        self.assertIn('config', init_event)
                        self.assertIn('total_capital', init_event['config'])
        except ImportError as e:
            self.skipTest(f"TradingBot import failed: {e}")


if __name__ == '__main__':
    unittest.main()
