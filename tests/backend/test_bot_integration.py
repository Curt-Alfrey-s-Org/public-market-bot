"""
Bot Integration Tests
Tests bot functionality and data flow
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus
import time


class BotIntegrationTest(BaseTestModule):
    """Test bot integration and data flow"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("Bot Integration", api_base_url)
    
    def test_bot_instance_available(self) -> TestResult:
        """Test that bot instance can be accessed"""
        def _test():
            response = self.api_request("GET", "/api/bot/status")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Bot should have a mode (even if 'unknown')
            assert "mode" in data, "Bot status should include mode"
            
            return data
        
        return self.run_test("Bot Instance Available", _test)
    
    def test_bot_data_consistency(self) -> TestResult:
        """Test that bot data is consistent across endpoints"""
        def _test():
            # Get stats
            stats_response = self.api_request("GET", "/api/stats")
            self.assert_status(stats_response, 200)
            stats = self.assert_json(stats_response)
            
            # Get trades
            trades_response = self.api_request("GET", "/api/trades")
            self.assert_status(trades_response, 200)
            trades = self.assert_json(trades_response)
            
            # Check consistency
            # Total trades in stats should match trades count (approximately)
            stats_trades = stats.get("total_trades", 0)
            trades_count = trades.get("total", 0)
            
            # They should be close (stats might include closed trades)
            if abs(stats_trades - trades_count) > 10:  # Allow some variance
                return TestResult(
                    "Bot Data Consistency",
                    TestStatus.WARN,
                    f"Trade count mismatch: stats={stats_trades}, trades={trades_count}"
                )
            
            return True
        
        return self.run_test("Bot Data Consistency", _test)
    
    def test_trade_history_structure(self) -> TestResult:
        """Test that trade history has correct structure"""
        def _test():
            response = self.api_request("GET", "/api/trades", params={"limit": 5})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            if data["trades"]:
                trade = data["trades"][0]
                
                # Validate trade structure
                required_fields = {
                    "symbol": str,
                    "side": str,
                    "entry_price": (int, float),
                    "quantity": int,
                    "status": str,
                    "entry_timestamp": str
                }
                
                for field, expected_type in required_fields.items():
                    assert field in trade, f"Trade missing field: {field}"
                    value = trade[field]
                    if isinstance(expected_type, tuple):
                        assert isinstance(value, expected_type), f"{field} should be one of {expected_type}"
                    else:
                        assert isinstance(value, expected_type), f"{field} should be {expected_type.__name__}"
                
                # Validate side values
                assert trade["side"] in ["long", "short"], "side should be 'long' or 'short'"
                
                # Validate status values
                assert trade["status"] in ["open", "closed"], "status should be 'open' or 'closed'"
            
            return True
        
        return self.run_test("Trade History Structure", _test)
    
    def test_stats_calculations(self) -> TestResult:
        """Test that stats calculations are correct"""
        def _test():
            response = self.api_request("GET", "/api/stats")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Validate numeric ranges
            capital = data.get("capital", 0)
            assert capital >= 0, "Capital should be non-negative"
            
            win_rate = data.get("win_rate", 0)
            assert 0 <= win_rate <= 100, "Win rate should be between 0 and 100"
            
            total_trades = data.get("total_trades", 0)
            assert total_trades >= 0, "Total trades should be non-negative"
            
            open_positions = data.get("open_positions", 0)
            assert open_positions >= 0, "Open positions should be non-negative"
            
            # Capital change percentage should be reasonable
            capital_change_pct = data.get("capital_change_pct", 0)
            assert -1000 <= capital_change_pct <= 10000, "Capital change % seems unreasonable"
            
            return True
        
        return self.run_test("Stats Calculations", _test)
    
    def test_message_structure(self) -> TestResult:
        """Test that messages have correct structure"""
        def _test():
            response = self.api_request("GET", "/api/messages", params={"limit": 5})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            if data["messages"]:
                message = data["messages"][0]
                
                # Validate message structure
                required_fields = ["message", "timestamp", "category"]
                for field in required_fields:
                    assert field in message, f"Message missing field: {field}"
                
                # Validate category values
                valid_categories = ["trading_paused", "alerts", "info", "warning", "capital_schedule"]
                assert message["category"] in valid_categories, f"Invalid category: {message['category']}"
            
            return True
        
        return self.run_test("Message Structure", _test)
    
    def test_log_entries_structure(self) -> TestResult:
        """Test that log entries have correct structure"""
        def _test():
            response = self.api_request("GET", "/api/logs", params={"limit": 5})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            if data["logs"]:
                log = data["logs"][0]
                
                # Validate log structure
                required_fields = ["raw", "timestamp", "level", "logger", "message"]
                for field in required_fields:
                    assert field in log, f"Log entry missing field: {field}"
                
                # Validate level values
                valid_levels = ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]
                assert log["level"] in valid_levels, f"Invalid log level: {log['level']}"
            
            return True
        
        return self.run_test("Log Entries Structure", _test)
    
    def run(self):
        """Run all bot integration tests"""
        self.log("Starting bot integration tests...")
        
        if not self.api_available():
            skip_msg = "API not running. Start with: ./start_api.sh or ./fix_api_connection.sh"
            for name in ["Bot Instance Available", "Bot Data Consistency", "Trade History Structure",
                         "Stats Calculations", "Message Structure", "Log Entries Structure"]:
                self.results.append(TestResult(name, TestStatus.SKIP, skip_msg))
            self.log(f"Completed {len(self.results)} tests (skipped - API not available)")
            return self.results
        
        tests = [
            self.test_bot_instance_available,
            self.test_bot_data_consistency,
            self.test_trade_history_structure,
            self.test_stats_calculations,
            self.test_message_structure,
            self.test_log_entries_structure,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
