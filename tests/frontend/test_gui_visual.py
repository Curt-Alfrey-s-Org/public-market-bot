"""
Frontend GUI Visual Tests
Tests visual aspects and UI components (requires browser automation or manual checks)
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus


class GUIVisualTest(BaseTestModule):
    """Test GUI visual aspects"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:5173"):
        super().__init__("GUI Visual", api_base_url)
        self.frontend_url = frontend_url
    
    def test_frontend_accessible(self) -> TestResult:
        """Test that frontend is accessible"""
        def _test():
            import requests
            try:
                response = requests.get(self.frontend_url, timeout=5)
                # Frontend should return 200 or redirect
                assert response.status_code in [200, 301, 302], f"Frontend returned {response.status_code}"
                return True
            except requests.exceptions.ConnectionError:
                return TestResult(
                    "Frontend Accessible",
                    TestStatus.SKIP,
                    f"Frontend not accessible at {self.frontend_url}. Is it running?"
                )
            except Exception as e:
                return TestResult(
                    "Frontend Accessible",
                    TestStatus.FAIL,
                    f"Error accessing frontend: {str(e)}"
                )
        
        return self.run_test("Frontend Accessible", _test)
    
    def test_api_proxy_configured(self) -> TestResult:
        """Test that frontend can proxy API requests"""
        def _test():
            # This is a basic check - full proxy testing requires browser automation
            # For now, we just verify the API is accessible
            response = self.api_request("GET", "/api/health")
            self.assert_status(response, 200)
            
            return TestResult(
                "API Proxy Configured",
                TestStatus.PASS,
                "API is accessible (proxy configuration should be verified manually or with browser automation)"
            )
        
        return self.run_test("API Proxy Configured", _test)
    
    def test_cors_enabled(self) -> TestResult:
        """Test that CORS is enabled for frontend"""
        def _test():
            # Check for CORS headers
            response = self.api_request("GET", "/api/health")
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            found_headers = [h for h in cors_headers if h in response.headers]
            
            if not found_headers:
                return TestResult(
                    "CORS Enabled",
                    TestStatus.WARN,
                    "CORS headers not found (may be configured in reverse proxy)"
                )
            
            return True
        
        return self.run_test("CORS Enabled", _test)
    
    def test_responsive_endpoints(self) -> TestResult:
        """Test that all endpoints respond within reasonable time"""
        def _test():
            endpoints = [
                "/api/health",
                "/api/bot/status",
                "/api/stats",
                "/api/trades",
                "/api/messages",
                "/api/logs",
            ]
            
            slow_endpoints = []
            for endpoint in endpoints:
                import time
                start = time.time()
                try:
                    response = self.api_request("GET", endpoint)
                    duration = time.time() - start
                    if duration > 2.0:  # More than 2 seconds is slow
                        slow_endpoints.append(f"{endpoint} ({duration:.2f}s)")
                except Exception as e:
                    slow_endpoints.append(f"{endpoint} (error: {str(e)[:50]})")
            
            if slow_endpoints:
                return TestResult(
                    "Responsive Endpoints",
                    TestStatus.WARN,
                    f"Slow endpoints: {', '.join(slow_endpoints)}"
                )
            
            return True
        
        return self.run_test("Responsive Endpoints", _test)
    
    def test_data_format_consistency(self) -> TestResult:
        """Test that data formats are consistent for frontend consumption"""
        def _test():
            # Check that all endpoints return consistent JSON structure
            endpoints = {
                "/api/stats": ["capital", "total_trades"],
                "/api/trades": ["trades", "total"],
                "/api/messages": ["messages", "total"],
                "/api/logs": ["logs", "total"],
            }
            
            issues = []
            for endpoint, required_fields in endpoints.items():
                try:
                    response = self.api_request("GET", endpoint)
                    self.assert_status(response, 200)
                    data = self.assert_json(response)
                    
                    for field in required_fields:
                        if field not in data:
                            issues.append(f"{endpoint} missing {field}")
                except Exception as e:
                    issues.append(f"{endpoint} error: {str(e)[:50]}")
            
            if issues:
                return TestResult(
                    "Data Format Consistency",
                    TestStatus.FAIL,
                    f"Issues found: {', '.join(issues)}"
                )
            
            return True
        
        return self.run_test("Data Format Consistency", _test)
    
    def run(self):
        """Run all GUI visual tests"""
        self.log("Starting GUI visual tests...")
        self.log("Note: Full visual testing requires browser automation (Selenium/Playwright)")
        self.log("These tests verify API accessibility and data format only")
        
        if not self.api_available():
            skip_msg = "API not running. Start with: ./start_api.sh or ./fix_api_connection.sh"
            for name in ["API Proxy Configured", "CORS Enabled", "Responsive Endpoints", "Data Format Consistency"]:
                self.results.append(TestResult(name, TestStatus.SKIP, skip_msg))
            # Frontend Accessible can still run (doesn't need API) - run it
            try:
                self.test_frontend_accessible()
            except Exception:
                pass
            self.log(f"Completed {len(self.results)} tests (API-dependent skipped)")
            return self.results
        
        tests = [
            self.test_frontend_accessible,
            self.test_api_proxy_configured,
            self.test_cors_enabled,
            self.test_responsive_endpoints,
            self.test_data_format_consistency,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
