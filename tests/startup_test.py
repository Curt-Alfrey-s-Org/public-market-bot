#!/usr/bin/env python3
"""
Startup Self-Test
Lightweight test suite for bot startup validation
Runs quickly and provides pass/fail status
"""

import os
import sys
import json
import requests
import importlib
import traceback
import time
from typing import Dict, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StartupTest:
    """Lightweight startup tests with timing"""
    
    def __init__(self, api_url: str = "http://localhost:8000", timeout: int = 2):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.results: List[Dict] = []
        self.start_time = None
        self.end_time = None
        self.timings: Dict[str, float] = {}
    
    def test_imports(self) -> bool:
        """Test that critical modules can be imported without circular import errors"""
        start = time.time()
        try:
            # Test api.main import (most critical - catches circular imports)
            import api.main
            if not hasattr(api.main, 'app'):
                self.timings['test_imports'] = time.time() - start
                return False
            
            # Test route imports
            from api.routes import bot, stats, settings, trades, system, messages, ai, tax, logs
            self.timings['test_imports'] = time.time() - start
            return True
        except ImportError as e:
            error_msg = str(e)
            self.timings['test_imports'] = time.time() - start
            if "partially initialized" in error_msg or "circular" in error_msg.lower():
                print(f"ERROR: Circular import detected: {error_msg}")
                traceback.print_exc()
                return False
            print(f"ERROR: Import error: {error_msg}")
            traceback.print_exc()
            return False
        except Exception as e:
            self.timings['test_imports'] = time.time() - start
            print(f"ERROR: Unexpected error during import test: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=self.timeout)
            elapsed = time.time() - start
            self.timings['test_api_health'] = elapsed
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception:
            self.timings['test_api_health'] = time.time() - start
            return False
    
    def test_bot_status(self) -> bool:
        """Test bot status endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/api/bot/status", timeout=self.timeout)
            elapsed = time.time() - start
            self.timings['test_bot_status'] = elapsed
            return response.status_code == 200
        except Exception:
            self.timings['test_bot_status'] = time.time() - start
            return False
    
    def test_stats_endpoint(self) -> bool:
        """Test stats endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/api/stats", timeout=self.timeout)
            elapsed = time.time() - start
            self.timings['test_stats_endpoint'] = elapsed
            return response.status_code == 200
        except Exception:
            self.timings['test_stats_endpoint'] = time.time() - start
            return False
    
    def test_trades_endpoint(self) -> bool:
        """Test trades endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/api/trades", timeout=self.timeout)
            elapsed = time.time() - start
            self.timings['test_trades_endpoint'] = elapsed
            return response.status_code == 200
        except Exception:
            self.timings['test_trades_endpoint'] = time.time() - start
            return False
    
    def test_messages_endpoint(self) -> bool:
        """Test messages endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/api/messages", timeout=self.timeout)
            elapsed = time.time() - start
            self.timings['test_messages_endpoint'] = elapsed
            return response.status_code == 200
        except Exception:
            self.timings['test_messages_endpoint'] = time.time() - start
            return False
    
    def run_all(self) -> Dict:
        """Run all startup tests with timing"""
        self.start_time = time.time()
        self.timings = {}
        
        tests = [
            ("Module Imports", self.test_imports),  # Run first - doesn't need API
            ("API Health", self.test_api_health),
            ("Bot Status", self.test_bot_status),
            ("Stats Endpoint", self.test_stats_endpoint),
            ("Trades Endpoint", self.test_trades_endpoint),
            ("Messages Endpoint", self.test_messages_endpoint),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            test_start = time.time()
            try:
                result = test_func()
                test_elapsed = time.time() - test_start
                
                # Get timing from test if available, otherwise use test_elapsed
                timing_key = name.lower().replace(' ', '_')
                test_timing = self.timings.get(timing_key, test_elapsed)
                
                self.results.append({
                    "name": name,
                    "status": "PASS" if result else "FAIL",
                    "passed": result,
                    "duration_ms": round(test_timing * 1000, 2)
                })
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                test_elapsed = time.time() - test_start
                self.results.append({
                    "name": name,
                    "status": "FAIL",
                    "passed": False,
                    "error": str(e),
                    "duration_ms": round(test_elapsed * 1000, 2)
                })
                failed += 1
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        total = len(tests)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "all_passed": failed == 0,
            "results": self.results,
            "timings": {
                "total_duration_ms": round(total_duration * 1000, 2),
                "total_duration_s": round(total_duration, 3),
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "test_timings": {k: round(v * 1000, 2) for k, v in self.timings.items()}
            }
        }


def main():
    """Run startup tests and return JSON result"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run startup self-tests")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    
    args = parser.parse_args()
    
    tester = StartupTest(api_url=args.api_url)
    result = tester.run_all()
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("Startup Self-Test")
        print("=" * 60)
        print(f"Total: {result['total']}")
        print(f"Passed: {result['passed']}")
        print(f"Failed: {result['failed']}")
        print(f"Success Rate: {result['success_rate']:.1f}%")
        print("=" * 60)
        for test_result in result['results']:
            status = "✓" if test_result['passed'] else "✗"
            duration = test_result.get('duration_ms', 0)
            print(f"{status} {test_result['name']:<20} ({duration:>6.2f}ms)")
        
        # Print timing summary
        if 'timings' in result:
            timings = result['timings']
            print("=" * 60)
            print("Timing Summary:")
            print(f"  Total Duration: {timings.get('total_duration_s', 0):.3f}s ({timings.get('total_duration_ms', 0):.2f}ms)")
            if 'test_timings' in timings:
                print("  Individual Tests:")
                for test_name, duration_ms in timings['test_timings'].items():
                    print(f"    {test_name}: {duration_ms:.2f}ms")
    
    # Exit with error code if any tests failed
    sys.exit(0 if result['all_passed'] else 1)


if __name__ == '__main__':
    main()
