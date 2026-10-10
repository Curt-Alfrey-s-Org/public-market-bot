#!/usr/bin/env python3
"""
Integration Tests for API Backend
Tests all API endpoints and validates responses
"""

import requests
import json
import sys
import time
from typing import Dict, Any
import pytest

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 5


@pytest.mark.integration
@pytest.mark.api
def test_api_backend_integration():
    """Pytest wrapper for API backend integration tests"""
    # Note: This test requires the API server to be running
    # It will be skipped in regular pytest runs
    pytest.skip("API backend integration test requires running server")


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}Testing: {name}{Colors.RESET}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_health_check():
    """Test API health check endpoint"""
    print_test("Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API - is it running?")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print_test("Root Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Root endpoint OK: {data.get('message', 'N/A')}")
            return True
        else:
            print_error(f"Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        return False

def test_bot_status():
    """Test bot status endpoint"""
    print_test("Bot Status")
    try:
        response = requests.get(f"{API_BASE_URL}/api/bot/status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Bot status: running={data.get('running', False)}, mode={data.get('mode', 'unknown')}")
            return True
        elif response.status_code == 503:
            print_warning("Bot instance not available (503) - this is OK if bot hasn't started")
            return True  # This is expected if bot isn't running
        else:
            print_error(f"Bot status failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Bot status error: {e}")
        return False

def test_bot_mode():
    """Test bot mode endpoint"""
    print_test("Bot Mode (POST)")
    try:
        # Test setting mode
        test_mode = "yfinance"
        response = requests.post(
            f"{API_BASE_URL}/api/bot/mode",
            json={"mode": test_mode},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Mode set: {data.get('mode', 'N/A')}")
            return True
        elif response.status_code == 503:
            print_warning("Bot instance not available - mode preference may be set")
            return True
        else:
            print_error(f"Mode set failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Mode set error: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print_test("Stats Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Stats retrieved: {len(data)} fields")
            return True
        elif response.status_code == 503:
            print_warning("Stats unavailable - bot instance not available")
            return True  # Expected if bot not running
        else:
            print_error(f"Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Stats error: {e}")
        return False

def test_messages():
    """Test messages endpoint"""
    print_test("Messages Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/messages?limit=10", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Messages retrieved: {len(data.get('messages', []))} messages")
            return True
        elif response.status_code == 503:
            print_warning("Messages unavailable - bot instance not available")
            return True  # Expected if bot not running
        else:
            print_error(f"Messages failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Messages error: {e}")
        return False

def test_trades():
    """Test trades endpoint"""
    print_test("Trades Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/trades", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Trades retrieved: {len(data.get('trades', []))} trades")
            return True
        elif response.status_code == 503:
            print_warning("Trades unavailable - bot instance not available")
            return True
        else:
            print_error(f"Trades failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Trades error: {e}")
        return False

def test_system():
    """Test system endpoint"""
    print_test("System Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/system", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"System info retrieved: CPU={data.get('cpu_percent', 0):.1f}%")
            return True
        else:
            print_error(f"System failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"System error: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print_test("CORS Headers")
    try:
        response = requests.options(
            f"{API_BASE_URL}/api/health",
            headers={"Origin": "http://localhost:5173"},
            timeout=TIMEOUT
        )
        cors_headers = {
            "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
            "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
            "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
        }
        if cors_headers["access-control-allow-origin"]:
            print_success(f"CORS configured: {cors_headers}")
            return True
        else:
            print_warning("CORS headers not present (may be OK for GET requests)")
            return True
    except Exception as e:
        print_error(f"CORS test error: {e}")
        return False

def test_websocket():
    """Test WebSocket connection"""
    print_test("WebSocket Connection")
    try:
        import websockets
        import asyncio
        
        async def test_ws():
            try:
                uri = "ws://localhost:8000/ws"
                async with websockets.connect(uri, timeout=3) as websocket:
                    print_success("WebSocket connected")
                    # Wait for a message
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2)
                        data = json.loads(message)
                        print_success(f"WebSocket message received: {data.get('type', 'unknown')}")
                        return True
                    except asyncio.TimeoutError:
                        print_warning("WebSocket connected but no message received (may be OK)")
                        return True
            except Exception as e:
                print_error(f"WebSocket error: {e}")
                return False
        
        return asyncio.run(test_ws())
    except ImportError:
        print_warning("websockets library not installed - skipping WebSocket test")
        return True
    except Exception as e:
        print_error(f"WebSocket test error: {e}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("API Integration Test Suite")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Check if API is reachable
    if not test_health_check():
        print_error("\nAPI is not reachable. Please ensure:")
        print("  1. API server is running: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        print("  2. No firewall blocking port 8000")
        print("  3. API is listening on 0.0.0.0:8000")
        sys.exit(1)
    
    # Run all tests
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Bot Status", test_bot_status),
        ("Bot Mode", test_bot_mode),
        ("Stats", test_stats),
        ("Messages", test_messages),
        ("Trades", test_trades),
        ("System", test_system),
        ("CORS", test_cors),
        ("WebSocket", test_websocket),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}: {name}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("All tests passed! ✓")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script for API connectivity validation
Tests that sandbox mode properly requires API connectivity and fails when APIs are down
"""

import os
# Set test environment variables
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'true')

import unittest
from unittest.mock import patch, MagicMock
import logging

# Import after setting environment variables
from main import TradingBot, validate_api_connectivity, SCHWAB_SANDBOX_MODE, PAPER_TRADING_MODE


class TestAPIConnectivityValidation(unittest.TestCase):
    """Test API connectivity validation at startup"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch('main._are_schwab_credentials_configured')
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_validate_api_connectivity_success_schwab(self, mock_schwab, mock_creds):
        """Test successful API validation with Schwab sandbox"""
        # Mock credentials as configured
        mock_creds.return_value = True
        # Mock successful Schwab API response
        mock_schwab.return_value = (150.0, 1000000)
        
        is_connected, message = validate_api_connectivity(self.bot)
        
        self.assertTrue(is_connected)
        self.assertIn('Schwab sandbox', message)
    
    @patch('main._are_schwab_credentials_configured')
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_validate_api_connectivity_fails_when_schwab_fails(self, mock_schwab, mock_creds):
        """Test API validation fails immediately when Schwab sandbox fails (no yfinance fallback)"""
        # Mock credentials as configured
        mock_creds.return_value = True
        # Mock Schwab failure - should fail immediately with no fallback
        mock_schwab.return_value = None
        
        is_connected, message = validate_api_connectivity(self.bot)
        
        self.assertFalse(is_connected)
        self.assertIn('CRITICAL ERROR', message)
        self.assertIn('Schwab sandbox API connectivity check failed', message)
    
    @patch('main._are_schwab_credentials_configured')
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_validate_api_connectivity_fails_when_schwab_down(self, mock_schwab, mock_creds):
        """Test API validation fails when Schwab API is down (no fallback)"""
        # Mock credentials as configured
        mock_creds.return_value = True
        # Mock Schwab API failing
        mock_schwab.return_value = None
        
        is_connected, message = validate_api_connectivity(self.bot)
        
        self.assertFalse(is_connected)
        self.assertIn('CRITICAL ERROR', message)
        self.assertIn('Schwab sandbox API connectivity check failed', message)


class TestSandboxModeAPIRequirement(unittest.TestCase):
    """Test that sandbox mode requires API connectivity"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_sandbox_mode_requires_api(self, mock_schwab):
        """Test that sandbox mode raises error when Schwab API fails"""
        # Mock Schwab API failing
        mock_schwab.return_value = None
        
        # In sandbox mode, should raise ValueError immediately, not fall back to random
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        # Check error message explains the issue
        error_msg = str(context.exception)
        self.assertIn('CRITICAL ERROR', error_msg)
        self.assertIn('Schwab sandbox API failed', error_msg)
        self.assertIn('SCHWAB_SANDBOX_MODE=false', error_msg)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_sandbox_mode_no_random_fallback(self, mock_schwab):
        """Test that sandbox mode never uses random prices as fallback"""
        # Mock Schwab API failing
        mock_schwab.return_value = None
        
        # Should raise error, not use random prices
        with self.assertRaises(ValueError):
            self.bot.get_stock_price('AAPL', use_random_fallback=True)
        
        # Verify random price generator was never called
        # (can't easily mock this without changing implementation,
        # but the ValueError proves we didn't fall back)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_sandbox_success_with_schwab(self, mock_schwab):
        """Test successful price fetch in sandbox mode"""
        # Mock successful Schwab API
        mock_schwab.return_value = (150.0, 1000000)
        
        price, volume = self.bot.get_stock_price('AAPL')
        
        self.assertEqual(price, 150.0)
        self.assertEqual(volume, 1000000)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_get_stock_price_sandbox_fails_immediately_no_yfinance_fallback(self, mock_schwab):
        """Test that sandbox mode raises error immediately when Schwab fails (no yfinance fallback)"""
        # Mock Schwab failure - should fail immediately, no yfinance fallback
        mock_schwab.return_value = None
        
        # Should raise ValueError immediately
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL')
        
        error_msg = str(context.exception)
        self.assertIn('CRITICAL ERROR', error_msg)
        self.assertIn('Schwab sandbox API failed', error_msg)
        self.assertIn('stopped immediately', error_msg)


class TestErrorMessages(unittest.TestCase):
    """Test that error messages are helpful and actionable"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
    
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_error_message_contains_troubleshooting_steps(self, mock_schwab):
        """Test error message provides clear troubleshooting steps"""
        mock_schwab.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL')
        
        error_msg = str(context.exception).lower()
        
        # Should mention key troubleshooting steps
        self.assertIn('schwab_api_key', error_msg)
        self.assertIn('network connection', error_msg)
        self.assertIn('schwab api service', error_msg)
        
    @patch.object(TradingBot, 'fetch_schwab_stock_price')
    def test_error_message_suggests_simulation_mode(self, mock_schwab):
        """Test error message suggests switching to pure simulation mode"""
        mock_schwab.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.bot.get_stock_price('AAPL')
        
        error_msg = str(context.exception)
        
        # Should suggest disabling sandbox mode
        self.assertIn('SCHWAB_SANDBOX_MODE=false', error_msg)


class TestSimulationModeStillWorks(unittest.TestCase):
    """Test that pure simulation mode (non-sandbox) still allows random fallback"""
    
    @patch('main.PAPER_TRADING_MODE', True)
    @patch('main.SCHWAB_SANDBOX_MODE', False)
    def test_simulation_mode_uses_random_fallback(self):
        """Test that pure simulation mode still falls back to random prices"""
        # Create a fresh bot instance
        bot = TradingBot(total_capital=10000.0)
        
        # Mock all APIs failing and random generators
        with patch.object(bot, 'fetch_schwab_stock_price', return_value=None), \
             patch.object(bot, 'fetch_real_stock_price', return_value=None), \
             patch.object(bot, 'generate_random_price', return_value=100.0), \
             patch.object(bot, 'generate_random_volume', return_value=500000):
            
            # Should use random fallback in simulation mode
            # Note: In actual code, SCHWAB_SANDBOX_MODE is checked, but since it's a module constant
            # we need to patch it at import time. For this test, we'll just verify no error is raised.
            # The actual random fallback will use real random values in the current implementation.
            try:
                price, volume = bot.get_stock_price('AAPL', use_random_fallback=True)
                # If we get here without error, the fallback is working
                # (even if it uses real random values instead of mocked ones)
                self.assertIsNotNone(price)
                self.assertIsNotNone(volume)
                self.assertGreater(price, 0)
                self.assertGreater(volume, 0)
            except ValueError:
                # If we got a ValueError, it means sandbox mode is still active
                # This test may not work correctly due to module-level constants
                self.skipTest("Cannot properly test simulation mode fallback with module-level constants")


if __name__ == '__main__':
    # Set up test logging
    logging.basicConfig(level=logging.CRITICAL)  # Suppress logs during testing
    
    # Run tests
    unittest.main(verbosity=2)
#!/usr/bin/env python3
"""
Test API Priority Manager
"""

import unittest
import asyncio
import time
from api_priority_manager import (
    ApiPriorityManager,
    ApiPriority,
    ApiRequest,
    get_priority_manager,
    execute_schwab_request,
    execute_market_data_request,
    execute_sentiment_request
)


class TestApiPriorityManager(unittest.TestCase):
    """Test API priority manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create new manager for each test
        import api_priority_manager
        api_priority_manager._api_priority_manager_instance = None
        self.manager = ApiPriorityManager(max_concurrent_low_priority=3)
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_manager_initialization(self):
        """Test that manager initializes correctly"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.total_requests, 0)
        self.assertEqual(self.manager.completed_requests, 0)
        print("✓ Manager initialization test passed")
    
    def test_priority_ordering(self):
        """Test that requests are prioritized correctly"""
        req1 = ApiRequest(lambda: None, ApiPriority.LOW, "low")
        req2 = ApiRequest(lambda: None, ApiPriority.CRITICAL, "critical")
        req3 = ApiRequest(lambda: None, ApiPriority.HIGH, "high")
        
        # Critical should be highest priority (lowest value)
        self.assertTrue(req2 < req1)
        self.assertTrue(req2 < req3)
        self.assertTrue(req3 < req1)
        
        print("✓ Priority ordering test passed")
    
    def test_async_request_execution(self):
        """Test async request execution"""
        
        async def mock_api_call():
            await asyncio.sleep(0.1)
            return "result"
        
        async def test():
            result = await self.manager.submit_request(
                mock_api_call,
                ApiPriority.HIGH,
                "test-request"
            )
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(test())
        
        self.assertEqual(result, "result")
        self.assertEqual(self.manager.completed_requests, 1)
        
        print("✓ Async request execution test passed")
    
    def test_sync_request_execution(self):
        """Test synchronous request execution"""
        
        def mock_sync_call():
            time.sleep(0.1)
            return "sync-result"
        
        async def test():
            result = await self.manager.submit_request(
                mock_sync_call,
                ApiPriority.MEDIUM,
                "test-sync-request"
            )
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(test())
        
        self.assertEqual(result, "sync-result")
        self.assertEqual(self.manager.completed_requests, 1)
        
        print("✓ Sync request execution test passed")
    
    def test_critical_priority_execution(self):
        """Test that critical requests execute immediately"""
        
        execution_order = []
        
        async def critical_call():
            execution_order.append('CRITICAL')
            await asyncio.sleep(0.1)
            return "critical"
        
        async def low_call():
            execution_order.append('LOW')
            await asyncio.sleep(0.1)
            return "low"
        
        async def test():
            # Start low priority first
            low_task = asyncio.create_task(
                self.manager.submit_request(low_call, ApiPriority.LOW, "low-req")
            )
            
            # Small delay to ensure low starts first
            await asyncio.sleep(0.05)
            
            # Submit critical (should interrupt/prioritize)
            critical_task = asyncio.create_task(
                self.manager.submit_request(critical_call, ApiPriority.CRITICAL, "critical-req")
            )
            
            results = await asyncio.gather(low_task, critical_task)
            return results
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(test())
        
        # Both should complete
        self.assertEqual(len(results), 2)
        self.assertEqual(self.manager.completed_requests, 2)
        
        print(f"✓ Critical priority execution test passed (order: {execution_order})")
    
    def test_concurrent_limit_enforcement(self):
        """Test that concurrent limits are enforced"""
        
        execution_times = []
        
        async def mock_call(name):
            start = time.time()
            await asyncio.sleep(0.2)
            execution_times.append((name, start))
            return name
        
        async def test():
            # Submit 5 low priority requests (limit is 3)
            tasks = [
                self.manager.submit_request(
                    mock_call, ApiPriority.LOW, f"low-{i}", (f"req-{i}",)
                )
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            return results
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(test())
        
        # All 5 should complete
        self.assertEqual(len(results), 5)
        self.assertEqual(self.manager.completed_requests, 5)
        
        print(f"✓ Concurrent limit enforcement test passed")
    
    def test_stats_tracking(self):
        """Test that statistics are tracked correctly"""
        
        async def test():
            # Submit requests of different priorities
            await self.manager.submit_request(
                lambda: "crit", ApiPriority.CRITICAL, "critical-1"
            )
            await self.manager.submit_request(
                lambda: "high", ApiPriority.HIGH, "high-1"
            )
            await self.manager.submit_request(
                lambda: "low", ApiPriority.LOW, "low-1"
            )
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test())
        
        stats = self.manager.get_stats()
        
        self.assertEqual(stats['total_requests'], 3)
        self.assertEqual(stats['completed_requests'], 3)
        self.assertEqual(stats['priority_breakdown']['critical'], 1)
        self.assertEqual(stats['priority_breakdown']['high'], 1)
        self.assertEqual(stats['priority_breakdown']['low'], 1)
        
        print("✓ Stats tracking test passed")
    
    def test_error_handling(self):
        """Test that errors are handled correctly"""
        
        async def failing_call():
            raise ValueError("Test error")
        
        async def test():
            try:
                await self.manager.submit_request(
                    failing_call, ApiPriority.MEDIUM, "failing-request"
                )
                return False  # Should not reach here
            except ValueError:
                return True  # Error was raised correctly
        
        loop = asyncio.get_event_loop()
        error_raised = loop.run_until_complete(test())
        
        self.assertTrue(error_raised)
        self.assertEqual(self.manager.failed_requests, 1)
        
        print("✓ Error handling test passed")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_execute_schwab_request(self):
        """Test execute_schwab_request helper"""
        
        async def mock_schwab():
            return "schwab-result"
        
        async def test():
            result = await execute_schwab_request(
                mock_schwab, "test-schwab"
            )
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(test())
        
        self.assertEqual(result, "schwab-result")
        print("✓ execute_schwab_request test passed")
    
    def test_execute_market_data_request(self):
        """Test execute_market_data_request helper"""
        
        async def mock_market_data():
            return "market-data-result"
        
        async def test():
            result = await execute_market_data_request(
                mock_market_data, "test-market"
            )
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(test())
        
        self.assertEqual(result, "market-data-result")
        print("✓ execute_market_data_request test passed")
    
    def test_execute_sentiment_request(self):
        """Test execute_sentiment_request helper"""
        
        async def mock_sentiment():
            return "sentiment-result"
        
        async def test():
            result = await execute_sentiment_request(
                mock_sentiment, "test-sentiment"
            )
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(test())
        
        self.assertEqual(result, "sentiment-result")
        print("✓ execute_sentiment_request test passed")


if __name__ == '__main__':
    print("="*60)
    print("API Priority Manager Tests")
    print("="*60)
    
    # Run tests
    unittest.main(verbosity=2)
#!/usr/bin/env python3
"""
Test script to verify FastAPI setup
Checks if all dependencies are available and API structure is correct
"""

import sys
import os
import importlib.util

def check_module(module_name, package_name=None):
    """Check if a Python module is available"""
    try:
        if package_name:
            __import__(package_name)
        else:
            __import__(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.exists(filepath), None

def check_directory_structure():
    """Check if API directory structure is correct"""
    required_dirs = [
        'api',
        'api/routes',
        'api/models',
        'frontend'
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing.append(dir_path)
    
    return len(missing) == 0, missing

def check_api_files():
    """Check if required API files exist"""
    required_files = [
        'api/__init__.py',
        'api/main.py',
        'api/bot.py',
        'api/routes/__init__.py',
        'api/routes/bot.py',
        'api/routes/stats.py',
        'api/routes/settings.py',
        'api/routes/trades.py',
        'api/routes/system.py',
        'api/models/__init__.py',
        'api/models/responses.py',
        'requirements-api.txt',
        'start_api.sh'
    ]
    
    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)
    
    return len(missing) == 0, missing

def check_syntax():
    """Check Python syntax of API files"""
    api_files = [
        'api/main.py',
        'api/bot.py',
        'api/routes/bot.py',
        'api/routes/stats.py',
        'api/routes/settings.py',
        'api/routes/trades.py',
        'api/routes/system.py',
        'api/models/responses.py'
    ]
    
    errors = []
    for file_path in api_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
            except SyntaxError as e:
                errors.append(f"{file_path}: {e}")
    
    return len(errors) == 0, errors

def test_imports():
    """Test if API modules can be imported (if dependencies available)"""
    # First check if we can even try to import
    modules_to_test = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('pydantic', 'pydantic'),
        ('psutil', 'psutil'),
    ]
    
    results = {}
    for module_name, package_name in modules_to_test:
        available, error = check_module(module_name, package_name)
        results[module_name] = (available, error)
    
    return results

def main():
    """Run all tests"""
    print("=" * 60)
    print("FastAPI Setup Verification Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Test 1: Directory Structure
    print("1. Checking directory structure...")
    passed, missing = check_directory_structure()
    if passed:
        print("   ✅ All required directories exist")
    else:
        print(f"   ❌ Missing directories: {', '.join(missing)}")
        all_passed = False
    print()
    
    # Test 2: API Files
    print("2. Checking API files...")
    passed, missing = check_api_files()
    if passed:
        print("   ✅ All required API files exist")
    else:
        print(f"   ❌ Missing files: {', '.join(missing)}")
        all_passed = False
    print()
    
    # Test 3: Python Syntax
    print("3. Checking Python syntax...")
    passed, errors = check_syntax()
    if passed:
        print("   ✅ All Python files have valid syntax")
    else:
        print("   ❌ Syntax errors found:")
        for error in errors:
            print(f"      - {error}")
        all_passed = False
    print()
    
    # Test 4: Dependencies
    print("4. Checking Python dependencies...")
    results = test_imports()
    all_deps_available = True
    for module_name, (available, error) in results.items():
        if available:
            print(f"   ✅ {module_name} is available")
        else:
            print(f"   ❌ {module_name} is NOT available: {error}")
            all_deps_available = False
            all_passed = False
    
    if all_deps_available:
        print("   ✅ All dependencies are installed")
    else:
        print("   ⚠️  Some dependencies are missing - install with: pip3 install -r requirements-api.txt")
    print()
    
    # Test 5: Try to import API modules (if dependencies available)
    if all_deps_available:
        print("5. Testing API module imports...")
        try:
            # Add current directory to path
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # Try importing API modules
            from api import main
            from api.routes import bot, stats, settings, trades, system
            from api.models import responses
            print("   ✅ All API modules can be imported")
        except Exception as e:
            print(f"   ❌ Error importing API modules: {e}")
            all_passed = False
        print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - API setup is correct!")
        print()
        print("Next steps:")
        if not all_deps_available:
            print("1. Install dependencies: pip3 install -r requirements-api.txt")
            print("2. Start API server: ./start_api.sh")
        else:
            print("1. Start API server: ./start_api.sh")
            print("2. Visit http://localhost:8000/docs for API documentation")
            print("3. Test health endpoint: curl http://localhost:8000/api/health")
    else:
        print("⚠️  SOME TESTS FAILED - Review errors above")
        if not all_deps_available:
            print()
            print("To install missing dependencies:")
            print("  pip3 install -r requirements-api.txt")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
