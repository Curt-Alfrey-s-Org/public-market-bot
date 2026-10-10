"""
Base Test Framework
Provides common functionality for all test modules
"""

import os
import sys
import time
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestStatus(Enum):
    """Test result status"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


class TestResult:
    """Individual test result"""
    def __init__(self, name: str, status: TestStatus, message: str = "", duration: float = 0.0, data: Any = None):
        self.name = name
        self.status = status
        self.message = message
        self.duration = duration
        self.data = data
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "data": self.data
        }


class BaseTestModule(ABC):
    """Base class for all test modules"""
    
    def __init__(self, name: str, api_base_url: str = "http://localhost:8002", timeout: int = 5):
        self.name = name
        self.api_base_url = api_base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [{self.name}] {message}")
    
    def run_test(self, name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a test function and record result"""
        start = time.time()
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start
            
            if isinstance(result, TestResult):
                result.duration = duration
                self.results.append(result)
                return result
            elif isinstance(result, bool):
                status = TestStatus.PASS if result else TestStatus.FAIL
                result_obj = TestResult(name, status, duration=duration)
                self.results.append(result_obj)
                return result_obj
            else:
                result_obj = TestResult(name, TestStatus.PASS, duration=duration, data=result)
                self.results.append(result_obj)
                return result_obj
        except Exception as e:
            duration = time.time() - start
            result = TestResult(name, TestStatus.FAIL, str(e), duration)
            self.results.append(result)
            self.log(f"Test '{name}' failed: {e}", "ERROR")
            return result
    
    def api_available(self) -> bool:
        """Check if API is reachable (for skipping API-dependent tests when API is not running)."""
        try:
            r = requests.get(f"{self.api_base_url}/api/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def api_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            return response
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Cannot connect to API at {url}. Is the API running? Start with: ./start_api.sh or ./fix_api_connection.sh")
        except requests.exceptions.Timeout:
            raise Exception(f"API request to {url} timed out after {self.timeout}s")
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def assert_status(self, response: requests.Response, expected_status: int, message: str = ""):
        """Assert HTTP status code"""
        if response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {response.status_code}. "
                f"Response: {response.text[:200]}. {message}"
            )
    
    def assert_json(self, response: requests.Response, message: str = ""):
        """Assert response is valid JSON"""
        try:
            return response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"Response is not valid JSON. {message}")
    
    def assert_field_exists(self, data: Dict, field: str, message: str = ""):
        """Assert field exists in response data"""
        if field not in data:
            raise AssertionError(f"Field '{field}' not found in response. {message}")
        return data[field]
    
    def assert_field_type(self, data: Dict, field: str, expected_type: type, message: str = ""):
        """Assert field is of expected type"""
        value = self.assert_field_exists(data, field, message)
        if not isinstance(value, expected_type):
            raise AssertionError(
                f"Field '{field}' is {type(value).__name__}, expected {expected_type.__name__}. {message}"
            )
        return value
    
    @abstractmethod
    def run(self) -> List[TestResult]:
        """Run all tests in this module"""
        pass
    
    def get_summary(self) -> Dict:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        warnings = sum(1 for r in self.results if r.status == TestStatus.WARN)
        
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        return {
            "module": self.name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "warnings": warnings,
            "duration": duration,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }
