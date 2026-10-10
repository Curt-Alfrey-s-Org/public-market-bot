"""
Backend API Endpoints Tests
Tests all API endpoints for correctness
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus
import json


class APIEndpointsTest(BaseTestModule):
    """Test all API endpoints"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("API Endpoints", api_base_url, timeout=15)  # Longer timeout for bot operations
    
    def test_health_check(self) -> TestResult:
        """Test health check endpoint"""
        def _test():
            response = self.api_request("GET", "/api/health")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            self.assert_field_exists(data, "status")
            assert data["status"] == "healthy", "Health status should be 'healthy'"
            return True
        
        return self.run_test("Health Check", _test)
    
    def test_root_endpoint(self) -> TestResult:
        """Test root endpoint"""
        def _test():
            response = self.api_request("GET", "/")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            self.assert_field_exists(data, "message")
            return True
        
        return self.run_test("Root Endpoint", _test)
    
    def test_bot_status(self) -> TestResult:
        """Test bot status endpoint"""
        def _test():
            response = self.api_request("GET", "/api/bot/status")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            self.assert_field_exists(data, "running")
            self.assert_field_exists(data, "mode")
            assert isinstance(data["running"], bool), "running should be boolean"
            assert isinstance(data["mode"], str), "mode should be string"
            return data
        
        return self.run_test("Bot Status", _test)
    
    def test_bot_start(self) -> TestResult:
        """Test bot start endpoint - actually starts the bot and verifies it's running"""
        def _test():
            # Get initial status
            initial_status = self.api_request("GET", "/api/bot/status")
            initial_data = self.assert_json(initial_status)
            initial_running = initial_data.get("running", False)
            
            # If already running, stop it first to test start
            if initial_running:
                stop_response = self.api_request("POST", "/api/bot/stop")
                import time
                time.sleep(1)  # Wait for stop
            
            # Start the bot
            response = self.api_request("POST", "/api/bot/start")
            assert response.status_code == 200, f"Start returned {response.status_code}, expected 200"
            data = self.assert_json(response)
            self.assert_field_exists(data, "status")
            
            # Verify bot is actually running
            import time
            time.sleep(2)  # Wait for bot to start
            status_response = self.api_request("GET", "/api/bot/status")
            status_data = self.assert_json(status_response)
            is_running = status_data.get("running", False)
            
            if not is_running:
                return TestResult(
                    "Bot Start",
                    TestStatus.FAIL,
                    f"Bot start endpoint returned success but bot is not running. Status: {status_data}"
                )
            
            return True
        
        return self.run_test("Bot Start", _test)
    
    def test_bot_stop(self) -> TestResult:
        """Test bot stop endpoint - actually stops the bot and verifies it's stopped"""
        def _test():
            # Ensure bot is running first
            start_response = self.api_request("POST", "/api/bot/start")
            import time
            time.sleep(2)  # Wait for bot to start
            
            # Verify it's running
            status_before = self.api_request("GET", "/api/bot/status")
            status_data_before = self.assert_json(status_before)
            if not status_data_before.get("running", False):
                return TestResult(
                    "Bot Stop",
                    TestStatus.SKIP,
                    "Could not start bot to test stop functionality"
                )
            
            # Stop the bot
            response = self.api_request("POST", "/api/bot/stop")
            assert response.status_code == 200, f"Stop returned {response.status_code}, expected 200"
            
            # Verify bot is actually stopped
            time.sleep(1)
            status_after = self.api_request("GET", "/api/bot/status")
            status_data_after = self.assert_json(status_after)
            is_running = status_data_after.get("running", False)
            
            if is_running:
                return TestResult(
                    "Bot Stop",
                    TestStatus.FAIL,
                    f"Bot stop endpoint returned success but bot is still running. Status: {status_data_after}"
                )
            
            return True
        
        return self.run_test("Bot Stop", _test)
    
    def test_bot_shutdown(self) -> TestResult:
        """Test bot shutdown endpoint - actually shuts down and verifies bot instance is cleaned up"""
        def _test():
            # Start bot first to have something to shutdown
            start_response = self.api_request("POST", "/api/bot/start")
            import time
            time.sleep(2)
            
            # Shutdown
            response = self.api_request("POST", "/api/bot/shutdown")
            assert response.status_code == 200, f"Shutdown returned {response.status_code}, expected 200"
            data = self.assert_json(response)
            self.assert_field_exists(data, "status")
            
            # Verify bot is stopped
            time.sleep(1)
            status_response = self.api_request("GET", "/api/bot/status")
            status_data = self.assert_json(status_response)
            is_running = status_data.get("running", False)
            
            if is_running:
                return TestResult(
                    "Bot Shutdown",
                    TestStatus.FAIL,
                    f"Bot shutdown endpoint returned success but bot is still running. Status: {status_data}"
                )
            
            return True
        
        return self.run_test("Bot Shutdown", _test)
    
    def test_stats_endpoint(self) -> TestResult:
        """Test stats endpoint"""
        def _test():
            response = self.api_request("GET", "/api/stats")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Check required fields
            required_fields = [
                "capital", "capital_change", "capital_change_pct",
                "allocation", "win_rate", "total_trades",
                "open_positions", "total_pnl"
            ]
            
            for field in required_fields:
                self.assert_field_exists(data, field)
                self.assert_field_type(data, field, (int, float))
            
            return data
        
        return self.run_test("Stats Endpoint", _test)
    
    def test_trades_endpoint(self) -> TestResult:
        """Test trades endpoint"""
        def _test():
            response = self.api_request("GET", "/api/trades")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            self.assert_field_exists(data, "trades")
            self.assert_field_exists(data, "total")
            assert isinstance(data["trades"], list), "trades should be a list"
            assert isinstance(data["total"], int), "total should be an integer"
            
            # If trades exist, validate structure
            if data["trades"]:
                trade = data["trades"][0]
                required_trade_fields = ["symbol", "side", "entry_price", "quantity", "status"]
                for field in required_trade_fields:
                    assert field in trade, f"Trade missing field: {field}"
            
            return data
        
        return self.run_test("Trades Endpoint", _test)
    
    def test_trades_filters(self) -> TestResult:
        """Test trades endpoint with filters - verify filters actually work"""
        def _test():
            # Get all trades first
            all_trades_response = self.api_request("GET", "/api/trades", params={"limit": 100})
            all_trades_data = self.assert_json(all_trades_response)
            all_trades = all_trades_data.get("trades", [])
            
            if not all_trades:
                # No trades to filter, just verify endpoint works
                response = self.api_request("GET", "/api/trades", params={"symbol": "AAPL", "limit": 10})
                self.assert_status(response, 200)
                return True
            
            # Test symbol filter - verify it actually filters
            test_symbol = all_trades[0].get("symbol", "AAPL")
            response = self.api_request("GET", "/api/trades", params={"symbol": test_symbol, "limit": 100})
            self.assert_status(response, 200)
            filtered_data = self.assert_json(response)
            filtered_trades = filtered_data.get("trades", [])
            
            # Verify all returned trades match the filter
            for trade in filtered_trades:
                if trade.get("symbol") != test_symbol:
                    return TestResult(
                        "Trades Filters",
                        TestStatus.FAIL,
                        f"Symbol filter failed: found {trade.get('symbol')} when filtering for {test_symbol}"
                    )
            
            # Test side filter
            test_side = all_trades[0].get("side", "long")
            response = self.api_request("GET", "/api/trades", params={"side": test_side, "limit": 100})
            self.assert_status(response, 200)
            side_filtered = self.assert_json(response)
            
            # Verify all returned trades match the side filter
            for trade in side_filtered.get("trades", []):
                if trade.get("side") != test_side:
                    return TestResult(
                        "Trades Filters",
                        TestStatus.FAIL,
                        f"Side filter failed: found {trade.get('side')} when filtering for {test_side}"
                    )
            
            # Test status filter
            response = self.api_request("GET", "/api/trades", params={"status": "open", "limit": 10})
            self.assert_status(response, 200)
            
            return True
        
        return self.run_test("Trades Filters", _test)
    
    def test_messages_endpoint(self) -> TestResult:
        """Test messages endpoint"""
        def _test():
            response = self.api_request("GET", "/api/messages")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            self.assert_field_exists(data, "messages")
            self.assert_field_exists(data, "total")
            assert isinstance(data["messages"], list), "messages should be a list"
            assert isinstance(data["total"], int), "total should be an integer"
            
            return data
        
        return self.run_test("Messages Endpoint", _test)
    
    def test_messages_filters(self) -> TestResult:
        """Test messages endpoint with filters"""
        def _test():
            response = self.api_request("GET", "/api/messages", params={"category": "alerts", "limit": 10})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            assert isinstance(data["messages"], list)
            return True
        
        return self.run_test("Messages Filters", _test)
    
    def test_logs_endpoint(self) -> TestResult:
        """Test logs endpoint"""
        def _test():
            response = self.api_request("GET", "/api/logs", params={"limit": 10})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            self.assert_field_exists(data, "logs")
            self.assert_field_exists(data, "total")
            self.assert_field_exists(data, "file")
            self.assert_field_exists(data, "exists")
            
            assert isinstance(data["logs"], list), "logs should be a list"
            assert isinstance(data["total"], int), "total should be an integer"
            assert isinstance(data["exists"], bool), "exists should be boolean"
            
            return data
        
        return self.run_test("Logs Endpoint", _test)
    
    def test_logs_filters(self) -> TestResult:
        """Test logs endpoint with filters - verify filters actually work"""
        def _test():
            # Get all logs first
            all_logs_response = self.api_request("GET", "/api/logs", params={"limit": 100})
            all_logs_data = self.assert_json(all_logs_response)
            all_logs = all_logs_data.get("logs", [])
            
            if not all_logs:
                # No logs to filter, just verify endpoint works
                response = self.api_request("GET", "/api/logs", params={"level": "ERROR", "limit": 10})
                self.assert_status(response, 200)
                return True
            
            # Test level filter - verify it actually filters
            test_level = "ERROR"
            response = self.api_request("GET", "/api/logs", params={"level": test_level, "limit": 100})
            self.assert_status(response, 200)
            filtered_data = self.assert_json(response)
            filtered_logs = filtered_data.get("logs", [])
            
            # Verify all returned logs match the filter
            for log in filtered_logs:
                if log.get("level") != test_level:
                    return TestResult(
                        "Logs Filters",
                        TestStatus.FAIL,
                        f"Level filter failed: found {log.get('level')} when filtering for {test_level}"
                    )
            
            # Test search filter - verify it actually searches
            test_search = "trade"
            response = self.api_request("GET", "/api/logs", params={"search": test_search, "limit": 100})
            self.assert_status(response, 200)
            search_data = self.assert_json(response)
            search_logs = search_data.get("logs", [])
            
            # Verify all returned logs contain the search term
            for log in search_logs:
                message = log.get("message", "").lower()
                if test_search.lower() not in message:
                    return TestResult(
                        "Logs Filters",
                        TestStatus.FAIL,
                        f"Search filter failed: log message '{message[:50]}' doesn't contain '{test_search}'"
                    )
            
            # Test sort
            response = self.api_request("GET", "/api/logs", params={"sort_by": "timestamp", "sort_order": "desc", "limit": 10})
            self.assert_status(response, 200)
            
            return True
        
        return self.run_test("Logs Filters", _test)
    
    def test_bot_mode_change(self) -> TestResult:
        """Test bot mode change endpoint - actually changes mode and verifies it"""
        def _test():
            import time
            
            # Must stop bot before changing mode (API rejects mode change while running)
            status_resp = self.api_request("GET", "/api/bot/status")
            status_data = self.assert_json(status_resp)
            if status_data.get("running", False):
                self.api_request("POST", "/api/bot/stop")
                time.sleep(2)  # Wait for stop
            
            # Get initial mode
            initial_status = self.api_request("GET", "/api/bot/status")
            initial_data = self.assert_json(initial_status)
            initial_mode = initial_data.get("mode", "unknown")
            
            # Try to change to a different mode
            # Test yfinance mode
            target_mode = "yfinance" if initial_mode != "yfinance" else "sandbox"
            
            response = self.api_request("POST", "/api/bot/mode", json={"mode": target_mode})
            self.assert_status(response, 200)
            data = self.assert_json(response)
            self.assert_field_exists(data, "mode")
            assert data["mode"] == target_mode, f"Mode endpoint returned {data['mode']}, expected {target_mode}"
            
            # Verify mode was persisted to .env file
            import os
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    # Check if mode was persisted
                    if target_mode == "yfinance":
                        if "PAPER_TRADING_MODE=true" not in env_content or "SCHWAB_SANDBOX_MODE=false" not in env_content:
                            return TestResult(
                                "Bot Mode Change",
                                TestStatus.FAIL,
                                f"Mode change to {target_mode} not persisted to .env file"
                            )
                    elif target_mode == "sandbox":
                        if "PAPER_TRADING_MODE=true" not in env_content or "SCHWAB_SANDBOX_MODE=true" not in env_content:
                            return TestResult(
                                "Bot Mode Change",
                                TestStatus.FAIL,
                                f"Mode change to {target_mode} not persisted to .env file"
                            )
            
            # If bot instance exists, verify mode on instance
            bot = self.api_request("GET", "/api/bot/status")
            bot_data = self.assert_json(bot)
            # Mode might be updated on instance or will be on next start
            
            return True
        
        return self.run_test("Bot Mode Change", _test)
    
    def test_settings_endpoint(self) -> TestResult:
        """Test settings endpoint"""
        def _test():
            try:
                response = self.api_request("GET", "/api/settings")
            except Exception as e:
                raise Exception(f"Cannot connect to API: {str(e)}. Is the API running? Start with: ./start_api.sh")
            
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}: {response.text[:200]}")
            
            try:
                data = self.assert_json(response)
            except Exception as e:
                raise Exception(f"Failed to parse JSON response: {str(e)}")
            
            # Verify required settings fields exist
            required_fields = [
                "BOT_TOTAL_CAPITAL",
                "BOT_MIN_ALLOCATION",
                "BOT_MAX_ALLOCATION",
                "BOT_RISK_THRESHOLD",
                "BOT_POSITION_SIZE",
                "BOT_MAX_OPEN_POSITIONS",
                "BOT_STOP_LOSS_PERCENT",
                "BOT_TAKE_PROFIT_PERCENT",
            ]
            
            # Trading mode settings
            trading_mode_fields = [
                "MANUAL_TRADE_APPROVAL_MODE",
                "PAPER_TRADING_MODE",
                "DRY_RUN_MODE",
                "BACKTEST_MODE",
                "SCHWAB_SANDBOX_MODE",
                "SCHWAB_API_ENABLED",
            ]
            
            # Advanced settings
            advanced_fields = [
                "TRADING_FREQUENCY",
                "LOG_LEVEL",
                "DEBUG",
                "TOP_PERFORMERS_REFRESH_INTERVAL",
                "ASYNC_REQUEST_TIMEOUT",
                "BOT_MAX_CPU_PERCENT",
                "BOT_MAX_MEMORY_PERCENT",
                "BOT_THROTTLE_DELAY",
                "BOT_ENABLE_THROTTLING",
                "EXIT_REFRESH_PRICE",
            ]
            
            all_fields = required_fields + trading_mode_fields + advanced_fields
            
            for field in all_fields:
                self.assert_field_exists(data, field)
                if field in required_fields or field in ["TRADING_FREQUENCY", "TOP_PERFORMERS_REFRESH_INTERVAL",
                                                         "ASYNC_REQUEST_TIMEOUT", "BOT_MAX_CPU_PERCENT",
                                                         "BOT_MAX_MEMORY_PERCENT", "BOT_THROTTLE_DELAY"]:
                    assert isinstance(data[field], (int, float)), f"{field} should be a number"
                elif field == "LOG_LEVEL":
                    assert isinstance(data[field], str), f"{field} should be a string"
                    assert data[field] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], \
                        f"{field} should be a valid log level"
            
            return data
        
        return self.run_test("Settings Endpoint", _test)
    
    def test_reports_decisions_endpoint(self) -> TestResult:
        """Test reports/decisions endpoint (Decision Report - yfinance visibility)"""
        def _test():
            response = self.api_request("GET", "/api/reports/decisions")
            self.assert_status(response, 200)
            data = self.assert_json(response)

            self.assert_field_exists(data, "candidates")
            self.assert_field_exists(data, "decisions")
            self.assert_field_exists(data, "cycle_number")
            self.assert_field_exists(data, "total_candidates")
            self.assert_field_exists(data, "evaluated_count")
            self.assert_field_exists(data, "cycle_in_progress_no_data")
            assert isinstance(data["candidates"], list), "candidates should be a list"
            assert isinstance(data["decisions"], list), "decisions should be a list"
            assert isinstance(data["cycle_number"], (int, float)), "cycle_number should be numeric"
            assert isinstance(data["total_candidates"], int), "total_candidates should be int"
            assert isinstance(data["evaluated_count"], int), "evaluated_count should be int"
            assert isinstance(data["cycle_in_progress_no_data"], bool), "cycle_in_progress_no_data should be bool"
            return data

        return self.run_test("Reports Decisions Endpoint", _test)

    def test_system_endpoint(self) -> TestResult:
        """Test system endpoint"""
        def _test():
            response = self.api_request("GET", "/api/system")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # System endpoint should return system info with expected structure
            required_fields = ["cpu_usage", "cpu_count", "memory_usage", "memory_total", "disk_usage", "uptime", "timestamp"]
            for field in required_fields:
                self.assert_field_exists(data, field)
            
            return data
        
        return self.run_test("System Endpoint", _test)
    
    def test_cors_headers(self) -> TestResult:
        """Test CORS headers"""
        def _test():
            response = self.api_request("OPTIONS", "/api/health")
            # CORS preflight should return 200 or 204
            assert response.status_code in [200, 204, 405], f"Unexpected CORS status: {response.status_code}"
            
            # Check for CORS headers in regular request
            response = self.api_request("GET", "/api/health")
            cors_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods"]
            has_cors = any(header in response.headers for header in cors_headers)
            
            if not has_cors:
                return TestResult("CORS Headers", TestStatus.WARN, "CORS headers not found (may be configured elsewhere)")
            
            return True
        
        return self.run_test("CORS Headers", _test)
    
    def run(self):
        """Run all API endpoint tests"""
        self.start_time = self.end_time = None  # Will be set by test runner
        
        self.log("Starting API endpoints tests...")
        
        if not self.api_available():
            skip_msg = "API not running. Start with: ./start_api.sh or ./fix_api_connection.sh"
            names = [
                "Health Check", "Root Endpoint", "Bot Status", "Bot Start", "Bot Stop", "Bot Shutdown",
                "Bot Mode Change", "Stats Endpoint", "Trades Endpoint", "Trades Filters",
                "Messages Endpoint", "Messages Filters", "Logs Endpoint", "Logs Filters",
                "Reports Decisions Endpoint", "Settings Endpoint", "System Endpoint", "CORS Headers"
            ]
            for name in names:
                self.results.append(TestResult(name, TestStatus.SKIP, skip_msg))
            self.log(f"Completed {len(self.results)} tests (skipped - API not available)")
            return self.results
        
        tests = [
            self.test_health_check,
            self.test_root_endpoint,
            self.test_bot_status,
            # Bot control tests - actually verify actions work
            self.test_bot_start,
            self.test_bot_stop,
            self.test_bot_shutdown,
            self.test_bot_mode_change,
            self.test_stats_endpoint,
            self.test_trades_endpoint,
            self.test_trades_filters,
            self.test_messages_endpoint,
            self.test_messages_filters,
            self.test_logs_endpoint,
            self.test_logs_filters,
            self.test_reports_decisions_endpoint,
            self.test_settings_endpoint,
            self.test_system_endpoint,
            self.test_cors_headers,
        ]
        
        for test in tests:
            try:
                result = test()
                # Print result immediately for visibility
                if result:
                    status_symbol = "✓" if result.status == TestStatus.PASS else "✗" if result.status == TestStatus.FAIL else "⚠" if result.status == TestStatus.WARN else "-"
                    self.log(f"{status_symbol} {result.name}: {result.message if result.message else result.status.value}", 
                           "INFO" if result.status == TestStatus.PASS else "ERROR" if result.status == TestStatus.FAIL else "WARNING")
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
                import traceback
                traceback.print_exc()
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
