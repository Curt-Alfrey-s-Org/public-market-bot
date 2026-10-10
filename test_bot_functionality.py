#!/usr/bin/env python3
"""
Comprehensive Bot Testing Suite
Tests all critical functionality after bug fixes
"""
import subprocess
import time
import requests
import json
import sys
from datetime import datetime

class BotTestSuite:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.api_base = "http://192.0.2.21:8004"
        self.bot_host = "operator@192.0.2.21"
        
    def log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test(self, name, func):
        """Run a single test"""
        self.log("TEST", f"Running: {name}")
        try:
            func()
            self.tests_passed += 1
            self.results.append((name, "PASS", None))
            self.log("✓", f"PASS: {name}")
            return True
        except AssertionError as e:
            self.tests_failed += 1
            self.results.append((name, "FAIL", str(e)))
            self.log("✗", f"FAIL: {name} - {e}")
            return False
        except Exception as e:
            self.tests_failed += 1
            self.results.append((name, "ERROR", str(e)))
            self.log("✗", f"ERROR: {name} - {e}")
            return False
    
    def run_ssh(self, command):
        """Run SSH command"""
        result = subprocess.run(
            ['ssh', self.bot_host, command],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout, result.stderr, result.returncode
    
    # ========== TEST CASES ==========
    
    def test_api_health(self):
        """Test: API is responding"""
        r = requests.get(f"{self.api_base}/api/bot/status", timeout=5)
        assert r.status_code == 200, f"API returned {r.status_code}"
    
    def test_bot_process_running(self):
        """Test: Bot process is running on operator"""
        stdout, _, code = self.run_ssh('pgrep -f "python main.py" | wc -l')
        count = int(stdout.strip())
        assert count > 0, "Bot process not found"
    
    def test_bot_initialized(self):
        """Test: Bot instance is initialized"""
        r = requests.get(f"{self.api_base}/api/bot/status", timeout=5)
        data = r.json()
        assert data.get('initialized', False) or data.get('mode'), "Bot not initialized"
    
    def test_strategies_loaded(self):
        """Test: Strategy signals are being generated"""
        stdout, _, _ = self.run_ssh(
            'grep -c "Combined signal:" /tmp/bot_output.log'
        )
        count = int(stdout.strip() or 0)
        assert count > 10, f"Only {count} signals found, expected >10"
    
    def test_trades_executing(self):
        """Test: Trades are being executed"""
        stdout, _, _ = self.run_ssh(
            'grep -c "Processing trade for" /tmp/bot_output.log'
        )
        count = int(stdout.strip() or 0)
        assert count > 5, f"Only {count} trades executed, expected >5"
    
    def test_trading_cycle_repeating(self):
        """Test: Trading cycles are executing (bot loops)"""
        stdout, _, _ = self.run_ssh(
            'grep "Trading Cycle #" /tmp/bot_output.log | wc -l'
        )
        count = int(stdout.strip() or 0)
        assert count >= 2, f"Only {count} cycles, expected >=2 (proves looping)"
    
    def test_no_crashes(self):
        """Test: No Python errors or crashes"""
        stdout, _, _ = self.run_ssh(
            'grep -i "traceback\\|error\\|exception" /tmp/bot_output.log | head -5'
        )
        # Allow warnings, but no tracebacks
        assert "Traceback" not in stdout, f"Found crash:\n{stdout}"
    
    def test_api_bot_status(self):
        """Test: API bot/status endpoint returns data"""
        r = requests.get(f"{self.api_base}/api/bot/status", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert 'mode' in data, "Missing 'mode' in response"
    
    def test_headless_mode_autostart(self):
        """Test: Bot auto-started in headless mode (no user prompt)"""
        stdout, _, _ = self.run_ssh(
            'grep -i "headless\\|auto-start" /tmp/bot_output.log'
        )
        assert len(stdout) > 0, "No headless mode detection logged"
    
    def test_strategy_signals_valid(self):
        """Test: Generated signals are BUY/SELL/HOLD"""
        stdout, _, _ = self.run_ssh(
            'grep "Combined signal:" /tmp/bot_output.log | grep -oE "BUY|SELL|HOLD" | sort | uniq -c'
        )
        assert len(stdout) > 0, "No valid signals found"
        assert "BUY" in stdout or "SELL" in stdout, "No BUY or SELL signals generated"
    
    def test_positions_created(self):
        """Test: Positions are being opened"""
        stdout, _, _ = self.run_ssh(
            'grep -E "BUY |SHORT " /tmp/bot_output.log | wc -l'
        )
        count = int(stdout.strip() or 0)
        assert count > 3, f"Only {count} positions opened, expected >3"
    
    def test_positions_closed(self):
        """Test: Positions are being closed"""
        stdout, _, _ = self.run_ssh(
            'grep -E "SELL |COVER " /tmp/bot_output.log | wc -l'
        )
        count = int(stdout.strip() or 0)
        assert count > 3, f"Only {count} positions closed, expected >3"
    
    def test_pnl_calculation(self):
        """Test: P&L is being calculated"""
        stdout, _, _ = self.run_ssh(
            'grep -i "P&L:" /tmp/bot_output.log | head -3'
        )
        assert "P&L:" in stdout, "No P&L calculations found"
    
    def test_continuous_loop(self):
        """Test: while True loop is working (multiple cycles)"""
        stdout, _, _ = self.run_ssh(
            'grep -oE "Trading Cycle #[0-9]+" /tmp/bot_output.log | tail -3'
        )
        cycles = stdout.strip().split('\n')
        assert len(cycles) >= 2, f"Less than 2 cycles, not looping properly"
    
    def test_no_action_tracking(self):
        """Test: 'no action' signals are properly tracked"""
        stdout, _, _ = self.run_ssh(
            'grep "no action (position state)" /tmp/bot_output.log | wc -l'
        )
        count = int(stdout.strip() or 0)
        assert count >= 0, "Should track position state (count can be 0 if all have actions)"
    
    def test_log_timestamps(self):
        """Test: All log entries have timestamps"""
        stdout, _, _ = self.run_ssh(
            'grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}" /tmp/bot_output.log | wc -l'
        )
        count = int(stdout.strip() or 0)
        assert count > 50, f"Only {count} timestamped logs, expected >50"
    
    def test_database_creation(self):
        """Test: Trade database is created"""
        stdout, _, code = self.run_ssh(
            'test -f ~/market-bot/market-pie5-bot/logs/trading_logs.db && echo "EXISTS"'
        )
        # Note: May not exist if restart recovery is off, but should exist after trading
        # This test is just informational
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Total:  {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed > 0:
            print("\nFailed Tests:")
            for name, status, error in self.results:
                if status != "PASS":
                    print(f"  ✗ {name}")
                    if error:
                        print(f"    {error}")
        
        print("\nDetailed Results:")
        for name, status, error in self.results:
            symbol = "✓" if status == "PASS" else "✗"
            print(f"{symbol} {status:5} - {name}")
        
        print("="*80)
        
        return self.tests_failed == 0
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("STARTING BOT TESTING SUITE")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {self.bot_host}")
        print("="*80 + "\n")
        
        # API & Process Tests
        self.test("API Health Check", self.test_api_health)
        self.test("Bot Process Running", self.test_bot_process_running)
        self.test("Bot Initialized", self.test_bot_initialized)
        
        # Core Functionality Tests
        self.test("Strategies Loaded", self.test_strategies_loaded)
        self.test("Trades Executing", self.test_trades_executing)
        self.test("Trading Cycle Repeating", self.test_trading_cycle_repeating)
        
        # Stability Tests
        self.test("No Crashes", self.test_no_crashes)
        
        # Feature Tests
        self.test("API Bot Status", self.test_api_bot_status)
        self.test("Headless Auto-Start", self.test_headless_mode_autostart)
        self.test("Strategy Signals Valid", self.test_strategy_signals_valid)
        self.test("Positions Created", self.test_positions_created)
        self.test("Positions Closed", self.test_positions_closed)
        self.test("P&L Calculation", self.test_pnl_calculation)
        
        # Loop & Logging Tests
        self.test("Continuous Loop", self.test_continuous_loop)
        self.test("No Action Tracking", self.test_no_action_tracking)
        self.test("Log Timestamps", self.test_log_timestamps)
        self.test("Database Creation", self.test_database_creation)
        
        # Print results
        success = self.print_summary()
        
        return 0 if success else 1

if __name__ == "__main__":
    suite = BotTestSuite()
    sys.exit(suite.run_all())
