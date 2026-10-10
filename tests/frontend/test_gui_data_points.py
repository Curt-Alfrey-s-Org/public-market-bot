"""
Frontend GUI Data Points Tests
Tests all data points displayed in the GUI
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus
import json


class GUIDataPointsTest(BaseTestModule):
    """Test all GUI data points"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("GUI Data Points", api_base_url)
    
    def test_dashboard_stats_data(self) -> TestResult:
        """Test dashboard stats data availability"""
        def _test():
            response = self.api_request("GET", "/api/stats")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Dashboard displays these stats
            dashboard_fields = [
                "capital", "capital_change", "capital_change_pct",
                "allocation", "win_rate", "total_trades", "open_positions"
            ]
            
            missing_fields = []
            for field in dashboard_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                return TestResult(
                    "Dashboard Stats Data",
                    TestStatus.FAIL,
                    f"Missing fields: {', '.join(missing_fields)}"
                )
            
            return True
        
        return self.run_test("Dashboard Stats Data", _test)
    
    def test_trades_page_data(self) -> TestResult:
        """Test trades page data availability"""
        def _test():
            response = self.api_request("GET", "/api/trades", params={"limit": 100})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Trades page needs these fields
            assert "trades" in data, "Trades endpoint should return 'trades' array"
            assert "total" in data, "Trades endpoint should return 'total' count"
            
            # Validate trade structure for display
            if data["trades"]:
                trade = data["trades"][0]
                display_fields = ["symbol", "side", "entry_price", "quantity", "status", "entry_timestamp"]
                missing = [f for f in display_fields if f not in trade]
                
                if missing:
                    return TestResult(
                        "Trades Page Data",
                        TestStatus.FAIL,
                        f"Trade missing display fields: {', '.join(missing)}"
                    )
            
            return True
        
        return self.run_test("Trades Page Data", _test)
    
    def test_messages_sidebar_data(self) -> TestResult:
        """Test messages sidebar data availability"""
        def _test():
            response = self.api_request("GET", "/api/messages", params={"limit": 50})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Messages sidebar needs these fields
            assert "messages" in data, "Messages endpoint should return 'messages' array"
            assert "total" in data, "Messages endpoint should return 'total' count"
            
            # Validate message structure for display
            if data["messages"]:
                message = data["messages"][0]
                display_fields = ["message", "timestamp", "category"]
                missing = [f for f in display_fields if f not in message]
                
                if missing:
                    return TestResult(
                        "Messages Sidebar Data",
                        TestStatus.FAIL,
                        f"Message missing display fields: {', '.join(missing)}"
                    )
            
            return True
        
        return self.run_test("Messages Sidebar Data", _test)
    
    def test_logs_page_data(self) -> TestResult:
        """Test logs page data availability"""
        def _test():
            response = self.api_request("GET", "/api/logs", params={"limit": 500})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Logs page needs these fields
            assert "logs" in data, "Logs endpoint should return 'logs' array"
            assert "total" in data, "Logs endpoint should return 'total' count"
            assert "exists" in data, "Logs endpoint should return 'exists' flag"
            
            # Validate log structure for display
            if data["logs"]:
                log = data["logs"][0]
                display_fields = ["timestamp", "level", "logger", "message"]
                missing = [f for f in display_fields if f not in log]
                
                if missing:
                    return TestResult(
                        "Logs Page Data",
                        TestStatus.FAIL,
                        f"Log entry missing display fields: {', '.join(missing)}"
                    )
            
            return True
        
        return self.run_test("Logs Page Data", _test)
    
    def test_bot_controls_data(self) -> TestResult:
        """Test bot controls data availability"""
        def _test():
            response = self.api_request("GET", "/api/bot/status")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Bot controls need these fields
            assert "running" in data, "Bot status should include 'running'"
            assert "mode" in data, "Bot status should include 'mode'"
            
            # Validate types
            assert isinstance(data["running"], bool), "running should be boolean"
            assert isinstance(data["mode"], str), "mode should be string"
            
            return True
        
        return self.run_test("Bot Controls Data", _test)
    
    def test_performance_chart_data(self) -> TestResult:
        """Test performance chart data availability"""
        def _test():
            # Performance charts use stats data
            response = self.api_request("GET", "/api/stats")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Charts need capital and PnL data
            chart_fields = ["capital", "total_pnl"]
            missing = [f for f in chart_fields if f not in data]
            
            if missing:
                return TestResult(
                    "Performance Chart Data",
                    TestStatus.FAIL,
                    f"Missing chart fields: {', '.join(missing)}"
                )
            
            return True
        
        return self.run_test("Performance Chart Data", _test)
    
    def test_data_refresh_rates(self) -> TestResult:
        """Test that data can be refreshed at expected rates"""
        def _test():
            # Test that endpoints respond quickly enough for frontend polling
            endpoints = [
                ("/api/stats", 5),  # 5 second refresh
                ("/api/trades", 5),  # 5 second refresh
                ("/api/messages", 1),  # 1 second refresh
                ("/api/bot/status", 2),  # 2 second refresh
            ]
            
            slow_endpoints = []
            for endpoint, max_time in endpoints:
                import time
                start = time.time()
                response = self.api_request("GET", endpoint)
                duration = time.time() - start
                
                if duration > max_time:
                    slow_endpoints.append(f"{endpoint} ({duration:.2f}s > {max_time}s)")
            
            if slow_endpoints:
                return TestResult(
                    "Data Refresh Rates",
                    TestStatus.WARN,
                    f"Slow endpoints: {', '.join(slow_endpoints)}"
                )
            
            return True
        
        return self.run_test("Data Refresh Rates", _test)
    
    def test_error_handling(self) -> TestResult:
        """Test error handling for missing data"""
        def _test():
            # Test that endpoints handle missing bot gracefully
            # (They should return empty/default data, not 503)
            
            endpoints = [
                "/api/stats",
                "/api/trades",
                "/api/messages",
            ]
            
            for endpoint in endpoints:
                response = self.api_request("GET", endpoint)
                # Should return 200 with empty/default data, not 503
                assert response.status_code == 200, f"{endpoint} returned {response.status_code}, expected 200"
                data = self.assert_json(response)
                # Should have expected structure even if empty
                assert isinstance(data, dict), f"{endpoint} should return object"
            
            return True
        
        return self.run_test("Error Handling", _test)
    
    def run(self):
        """Run all GUI data point tests"""
        self.log("Starting GUI data points tests...")
        
        if not self.api_available():
            skip_msg = "API not running. Start with: ./start_api.sh or ./fix_api_connection.sh"
            for name in ["Dashboard Stats Data", "Trades Page Data", "Messages Sidebar Data", "Logs Page Data",
                         "Bot Controls Data", "Performance Chart Data", "Data Refresh Rates", "Error Handling"]:
                self.results.append(TestResult(name, TestStatus.SKIP, skip_msg))
            self.log(f"Completed {len(self.results)} tests (skipped - API not available)")
            return self.results
        
        tests = [
            self.test_dashboard_stats_data,
            self.test_trades_page_data,
            self.test_messages_sidebar_data,
            self.test_logs_page_data,
            self.test_bot_controls_data,
            self.test_performance_chart_data,
            self.test_data_refresh_rates,
            self.test_error_handling,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
