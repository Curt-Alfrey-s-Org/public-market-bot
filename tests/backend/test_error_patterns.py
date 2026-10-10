"""
Error Pattern Tests
Tests for common error patterns found during development
These tests catch errors that were previously encountered and fixed
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus
import os
import json


class ErrorPatternsTest(BaseTestModule):
    """Test for common error patterns that have been encountered"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("Error Patterns", api_base_url)
    
    def test_mode_not_unknown_when_stopped(self) -> TestResult:
        """
        Test: Mode should never be "unknown" when bot is stopped
        Error Found: Mode showed "unknown" even when bot was stopped
        Fix: Enhanced mode detection to always use environment variables as fallback
        """
        def _test():
            response = self.api_request("GET", "/api/bot/status")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            mode = data.get("mode", "")
            running = data.get("running", False)
            
            # Mode should never be "unknown"
            if mode == "unknown":
                return TestResult(
                    "Mode Not Unknown When Stopped",
                    TestStatus.FAIL,
                    f"Mode is 'unknown' when bot is {'running' if running else 'stopped'}. "
                    f"Mode should be determined from environment variables."
                )
            
            # Mode should be one of the valid modes
            valid_modes = ["sandbox", "yfinance", "live", "dry_run"]
            if mode not in valid_modes:
                return TestResult(
                    "Mode Not Unknown When Stopped",
                    TestStatus.FAIL,
                    f"Mode '{mode}' is not a valid mode. Expected one of: {valid_modes}"
                )
            
            return True
        
        return self.run_test("Mode Not Unknown When Stopped", _test)
    
    def test_mode_change_blocked_while_running(self) -> TestResult:
        """
        Test: Mode changes should be blocked when bot is running
        Error Found: User could change mode while bot was running, causing confusion
        Fix: Added check in set_bot_mode to prevent changes when bot is running
        """
        def _test():
            # Get current status
            status_response = self.api_request("GET", "/api/bot/status")
            status_data = self.assert_json(status_response)
            is_running = status_data.get("running", False)
            
            if not is_running:
                # Start bot first
                start_response = self.api_request("POST", "/api/bot/start")
                if start_response.status_code != 200:
                    return TestResult(
                        "Mode Change Blocked While Running",
                        TestStatus.SKIP,
                        "Could not start bot to test mode change blocking"
                    )
                import time
                time.sleep(2)  # Wait for bot to start
            
            # Try to change mode while running
            response = self.api_request("POST", "/api/bot/mode", json={"mode": "yfinance"})
            
            if is_running or self.api_request("GET", "/api/bot/status").json().get("running", False):
                # Should return 400 error
                if response.status_code != 400:
                    return TestResult(
                        "Mode Change Blocked While Running",
                        TestStatus.FAIL,
                        f"Expected 400 error when changing mode while bot is running, got {response.status_code}"
                    )
                
                error_data = self.assert_json(response)
                if "cannot change mode while bot is running" not in error_data.get("detail", "").lower():
                    return TestResult(
                        "Mode Change Blocked While Running",
                        TestStatus.FAIL,
                        f"Error message doesn't indicate mode change is blocked: {error_data.get('detail', '')}"
                    )
            else:
                # If bot is not running, mode change should succeed
                self.assert_status(response, 200)
            
            return True
        
        return self.run_test("Mode Change Blocked While Running", _test)
    
    def test_system_endpoint_structure(self) -> TestResult:
        """
        Test: System endpoint should return flat structure matching frontend expectations
        Error Found: System page showed "Something went wrong" - backend returned nested structure
        Fix: Changed backend to return flat structure with all required fields
        """
        def _test():
            response = self.api_request("GET", "/api/system")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            # Frontend expects these fields at top level
            required_fields = [
                "cpu_usage",
                "cpu_count",
                "memory_usage",
                "memory_total",
                "memory_available",
                "disk_usage",
                "disk_total",
                "disk_free",
                "uptime",
                "timestamp"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                return TestResult(
                    "System Endpoint Structure",
                    TestStatus.FAIL,
                    f"System endpoint missing required fields: {', '.join(missing_fields)}. "
                    f"Frontend expects flat structure, not nested."
                )
            
            # Verify types
            if not isinstance(data.get("cpu_usage"), (int, float)):
                return TestResult(
                    "System Endpoint Structure",
                    TestStatus.FAIL,
                    "cpu_usage should be a number"
                )
            
            if not isinstance(data.get("uptime"), (int, float)):
                return TestResult(
                    "System Endpoint Structure",
                    TestStatus.FAIL,
                    "uptime should be a number"
                )
            
            return True
        
        return self.run_test("System Endpoint Structure", _test)
    
    def test_settings_endpoint_returns_all_fields(self) -> TestResult:
        """
        Test: Settings endpoint should return all required fields
        Error Found: Settings page showing nothing - likely missing fields
        Fix: Added test to verify all required settings fields are returned
        """
        def _test():
            try:
                response = self.api_request("GET", "/api/settings")
            except Exception as e:
                return TestResult(
                    "Settings Endpoint Returns All Fields",
                    TestStatus.FAIL,
                    f"Cannot connect to API: {str(e)}. Is the API running? Start with: ./start_api.sh"
                )
            
            if response.status_code != 200:
                return TestResult(
                    "Settings Endpoint Returns All Fields",
                    TestStatus.FAIL,
                    f"API returned status {response.status_code}: {response.text[:200]}"
                )
            
            try:
                data = self.assert_json(response)
            except Exception as e:
                return TestResult(
                    "Settings Endpoint Returns All Fields",
                    TestStatus.FAIL,
                    f"Failed to parse JSON response: {str(e)}"
                )
            
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
            
            # Trading mode settings (strings/booleans)
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
            
            all_required_fields = required_fields + trading_mode_fields + advanced_fields
            
            missing_fields = []
            for field in all_required_fields:
                if field not in data:
                    missing_fields.append(field)
                elif field in required_fields and not isinstance(data[field], (int, float)):
                    return TestResult(
                        "Settings Endpoint Returns All Fields",
                        TestStatus.FAIL,
                        f"{field} should be a number, got {type(data[field])}"
                    )
                elif field in ["TRADING_FREQUENCY", "TOP_PERFORMERS_REFRESH_INTERVAL", "ASYNC_REQUEST_TIMEOUT",
                             "BOT_MAX_CPU_PERCENT", "BOT_MAX_MEMORY_PERCENT", "BOT_THROTTLE_DELAY"]:
                    if not isinstance(data[field], (int, float)):
                        return TestResult(
                            "Settings Endpoint Returns All Fields",
                            TestStatus.FAIL,
                            f"{field} should be a number, got {type(data[field])}"
                        )
            
            if missing_fields:
                return TestResult(
                    "Settings Endpoint Returns All Fields",
                    TestStatus.FAIL,
                    f"Settings endpoint missing required fields: {', '.join(missing_fields)}"
                )
            
            # All fields present and valid
            return TestResult(
                "Settings Endpoint Returns All Fields",
                TestStatus.PASS,
                f"All {len(all_required_fields)} required settings fields are present and valid"
            )
        
        return self.run_test("Settings Endpoint Returns All Fields", _test)
    
    def test_api_response_has_no_error_messages(self) -> TestResult:
        """
        Test: API responses should not contain user-facing error messages
        Error Found: Error messages were showing to users in GUI
        Fix: Removed error messages from API responses, use status codes instead
        """
        def _test():
            # Test various endpoints for error message patterns
            endpoints = [
                "/api/bot/status",
                "/api/stats",
                "/api/trades",
                "/api/messages",
                "/api/logs",
                "/api/settings",
                "/api/system",
            ]
            
            error_patterns = [
                "error",
                "failed",
                "cannot",
                "unable",
                "exception",
                "traceback"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.api_request("GET", endpoint)
                    if response.status_code == 200:
                        data = self.assert_json(response)
                        # Check if response contains error messages
                        response_str = json.dumps(data).lower()
                        for pattern in error_patterns:
                            if pattern in response_str and "error" in response_str:
                                # Check if it's a user-facing error message
                                if any(msg in response_str for msg in ["message", "detail", "description"]):
                                    return TestResult(
                                        "API Response Has No Error Messages",
                                        TestStatus.FAIL,
                                        f"Endpoint {endpoint} contains user-facing error message with pattern '{pattern}'"
                                    )
                except Exception:
                    # Skip endpoints that might not be available
                    continue
            
            return True
        
        return self.run_test("API Response Has No Error Messages", _test)
    
    def run(self):
        """Run all error pattern tests"""
        self.log("Starting error pattern tests...")
        
        if not self.api_available():
            skip_msg = "API not running. Start with: ./start_api.sh or ./fix_api_connection.sh"
            for name in ["Mode Not Unknown When Stopped", "Mode Change Blocked While Running",
                         "System Endpoint Structure", "Settings Endpoint Returns All Fields",
                         "API Response Has No Error Messages"]:
                self.results.append(TestResult(name, TestStatus.SKIP, skip_msg))
            self.log(f"Completed {len(self.results)} error pattern tests (skipped - API not available)")
            return self.results
        
        tests = [
            self.test_mode_not_unknown_when_stopped,
            self.test_mode_change_blocked_while_running,
            self.test_system_endpoint_structure,
            self.test_settings_endpoint_returns_all_fields,
            self.test_api_response_has_no_error_messages,
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                # Print result immediately for visibility
                if result:
                    status_symbol = "✓" if result.status == TestStatus.PASS else "✗" if result.status == TestStatus.FAIL else "⚠" if result.status == TestStatus.WARN else "-"
                    self.log(f"{status_symbol} {result.name}: {result.message if result.message else result.status.value}", 
                           "INFO" if result.status == TestStatus.PASS else "ERROR" if result.status == TestStatus.FAIL else "WARNING")
            except Exception as e:
                self.log(f"Test {test_func.__name__} raised exception: {e}", "ERROR")
                import traceback
                traceback.print_exc()
        
        self.log(f"Completed {len(self.results)} error pattern tests")
        return self.results
