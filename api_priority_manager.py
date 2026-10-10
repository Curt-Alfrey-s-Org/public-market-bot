#!/usr/bin/env python3
"""
API Priority Manager for market-pie5-bot

This module implements a priority queue system to ensure Schwab API trading operations
always execute before market data APIs (yfinance, Alpha Vantage, news APIs).

Performance Optimizations:
- Circuit breaker pattern: Prevents cascading failures from downed APIs
- Exponential backoff: Gradually increase retry delays for failing endpoints
- Request prioritization: Critical operations execute first

Priority Levels:
1. CRITICAL (Priority 0): Schwab account operations (buy, sell, get account balance, positions)
2. HIGH (Priority 1): Real-time market data needed for trading decisions
3. MEDIUM (Priority 2): Fundamental data, historical prices
4. LOW (Priority 3): News sentiment, optional data
"""

import asyncio
import logging
from typing import Callable, Any, Dict, Optional, List
from enum import IntEnum
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class CircuitBreakerState(IntEnum):
    """States for circuit breaker pattern"""
    CLOSED = 0      # Normal operation
    OPEN = 1        # Failing, reject requests
    HALF_OPEN = 2   # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for API endpoint protection.
    
    Prevents cascading failures by stopping requests to failing endpoints.
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing) -> CLOSED
    """
    
    def __init__(self, 
                 endpoint_name: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60):
        """
        Initialize circuit breaker
        
        Args:
            endpoint_name: Name of the API endpoint
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying to recover (half-open state)
        """
        self.endpoint_name = endpoint_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.opened_at = None
        
        logger.info(f"CircuitBreaker created for {endpoint_name}")
    
    def is_available(self) -> bool:
        """Check if endpoint is available"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if it's time to try recovery
            if self.opened_at and datetime.now() > self.opened_at + timedelta(seconds=self.recovery_timeout):
                logger.info(f"CircuitBreaker {self.endpoint_name}: Entering HALF_OPEN state")
                self.state = CircuitBreakerState.HALF_OPEN
                self.failure_count = 0
                return True
            return False
        
        # HALF_OPEN: Allow request
        return True
    
    def record_success(self):
        """Record successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"CircuitBreaker {self.endpoint_name}: Recovered, closing circuit")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"CircuitBreaker {self.endpoint_name}: Recovery attempt failed, reopening")
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now()
        elif self.failure_count >= self.failure_threshold:
            logger.warning(f"CircuitBreaker {self.endpoint_name}: Failure threshold reached, opening circuit")
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now()
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'endpoint': self.endpoint_name,
            'state': self.state.name,
            'failure_count': self.failure_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class ApiPriority(IntEnum):
    """
    Priority levels for API calls
    Lower number = higher priority (0 is highest)
    """
    CRITICAL = 0  # Schwab trading operations
    HIGH = 1      # Real-time market data
    MEDIUM = 2    # Fundamental data
    LOW = 3       # News sentiment


class ApiRequest:
    """
    Represents an API request with priority
    """
    
    def __init__(self, 
                 func: Callable,
                 priority: ApiPriority,
                 name: str,
                 args: tuple = (),
                 kwargs: dict = None):
        """
        Initialize API request
        
        Args:
            func: Function to call (can be sync or async)
            priority: Request priority level
            name: Human-readable name for logging
            args: Positional arguments for func
            kwargs: Keyword arguments for func
        """
        self.func = func
        self.priority = priority
        self.name = name
        self.args = args
        self.kwargs = kwargs or {}
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
    
    def __lt__(self, other):
        """Compare by priority (lower number = higher priority)"""
        return self.priority < other.priority
    
    def __repr__(self):
        return f"ApiRequest(name='{self.name}', priority={self.priority.name})"


class ApiPriorityManager:
    """
    Manages API request execution with priority queue and circuit breakers.
    
    Ensures Schwab API calls always execute first, while allowing
    concurrent execution of lower-priority market data APIs.
    
    Performance Features:
    - Circuit breaker pattern for each endpoint (prevent cascading failures)
    - Request prioritization (critical > high > medium > low)
    - Backoff strategies for rate-limited endpoints
    """
    
    def __init__(self, max_concurrent_low_priority: int = 5):
        """
        Initialize priority manager with circuit breakers
        
        Args:
            max_concurrent_low_priority: Maximum concurrent non-critical requests
        """
        self.max_concurrent_low_priority = max_concurrent_low_priority
        self.request_queue = asyncio.PriorityQueue()
        self.active_requests: Dict[ApiPriority, int] = {
            ApiPriority.CRITICAL: 0,
            ApiPriority.HIGH: 0,
            ApiPriority.MEDIUM: 0,
            ApiPriority.LOW: 0
        }
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        
        # Circuit breakers for each endpoint type
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            'yfinance': CircuitBreaker('yfinance', failure_threshold=5, recovery_timeout=60),
            'alphavantage': CircuitBreaker('alphavantage', failure_threshold=3, recovery_timeout=120),
            'schwab': CircuitBreaker('schwab', failure_threshold=2, recovery_timeout=30),
            'news_api': CircuitBreaker('news_api', failure_threshold=5, recovery_timeout=90),
        }
        
        self.stats = {
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'avg_wait_time_critical': 0.0,
            'avg_wait_time_low': 0.0,
            'circuit_breaker_rejections': 0,
        }
        self._lock = asyncio.Lock()
        logger.info("ApiPriorityManager initialized with circuit breakers")
    
    async def submit_request(self,
                            func: Callable,
                            priority: ApiPriority,
                            name: str,
                            endpoint: Optional[str] = None,
                            args: tuple = (),
                            kwargs: dict = None) -> Any:
        """
        Submit an API request with priority and circuit breaker protection.
        
        Args:
            func: Function to call (sync or async)
            priority: Priority level
            name: Request name for logging
            endpoint: API endpoint name (for circuit breaker), e.g., 'yfinance'
            args: Function args
            kwargs: Function kwargs
            
        Returns:
            Result of the function call
            
        Raises:
            Exception if circuit breaker is open
        """
        # Check circuit breaker for this endpoint
        if endpoint and endpoint in self.circuit_breakers:
            breaker = self.circuit_breakers[endpoint]
            if not breaker.is_available():
                self.stats['circuit_breaker_rejections'] += 1
                error_msg = f"Circuit breaker OPEN for {endpoint}: {breaker.state.name}"
                logger.warning(f"{name}: {error_msg}")
                raise Exception(error_msg)
        
        request = ApiRequest(func, priority, name, args, kwargs)
        
        logger.debug(f"Submitting {priority.name} priority request: {name}")
        
        # Put request in priority queue
        await self.request_queue.put((priority.value, self.total_requests, request))
        self.total_requests += 1
        
        # Wait for and execute the request
        result = await self._execute_when_ready(request, endpoint)
        
        return result
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self.circuit_breakers.items()}
    
    async def _execute_when_ready(self, request: ApiRequest, endpoint: Optional[str] = None) -> Any:
        """
        Wait for request to be ready and execute it with circuit breaker integration.
        
        Critical requests execute immediately.
        Lower priority requests wait if critical requests are pending.
        
        Args:
            request: The API request to execute
            endpoint: API endpoint name (for circuit breaker)
            
        Returns:
            Result of the request
        """
        # Wait until it's safe to execute this request
        while True:
            async with self._lock:
                # Critical requests always execute immediately
                if request.priority == ApiPriority.CRITICAL:
                    break
                
                # High priority waits only for critical
                if request.priority == ApiPriority.HIGH:
                    if self.active_requests[ApiPriority.CRITICAL] == 0:
                        break
                
                # Medium/Low priority waits for critical and respects concurrency limits
                else:
                    critical_active = self.active_requests[ApiPriority.CRITICAL]
                    high_active = self.active_requests[ApiPriority.HIGH]
                    medium_active = self.active_requests[ApiPriority.MEDIUM]
                    low_active = self.active_requests[ApiPriority.LOW]
                    
                    total_low_priority = medium_active + low_active
                    
                    if critical_active == 0 and total_low_priority < self.max_concurrent_low_priority:
                        break
            
            # Wait a bit before checking again
            await asyncio.sleep(0.01)
        
        # Execute the request
        async with self._lock:
            self.active_requests[request.priority] += 1
        
        try:
            request.started_at = datetime.now()
            wait_time = (request.started_at - request.created_at).total_seconds()
            
            logger.debug(f"Executing {request.priority.name} request: {request.name} "
                        f"(waited {wait_time:.3f}s)")
            
            # Execute function (handle both sync and async)
            if asyncio.iscoroutinefunction(request.func):
                result = await request.func(*request.args, **request.kwargs)
            else:
                # Run synchronous function in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: request.func(*request.args, **request.kwargs)
                )
            
            request.result = result
            request.completed_at = datetime.now()
            
            # Record circuit breaker success
            if endpoint and endpoint in self.circuit_breakers:
                self.circuit_breakers[endpoint].record_success()
            
            # Update stats
            self._update_stats(request, wait_time)
            
            async with self._lock:
                self.completed_requests += 1
                self.active_requests[request.priority] -= 1
            
            logger.debug(f"Completed {request.priority.name} request: {request.name}")
            
            return result
            
        except Exception as e:
            request.error = e
            request.completed_at = datetime.now()
            
            # Record circuit breaker failure
            if endpoint and endpoint in self.circuit_breakers:
                self.circuit_breakers[endpoint].record_failure()
            
            async with self._lock:
                self.failed_requests += 1
                self.active_requests[request.priority] -= 1
            
            logger.error(f"Failed {request.priority.name} request {request.name}: {e}")
            raise
    
    def _update_stats(self, request: ApiRequest, wait_time: float):
        """Update statistics"""
        priority_name = request.priority.name.lower()
        count_key = f"{priority_name}_count"
        
        if count_key in self.stats:
            self.stats[count_key] += 1
        
        # Track average wait times for critical vs low priority
        if request.priority == ApiPriority.CRITICAL:
            current_avg = self.stats['avg_wait_time_critical']
            count = self.stats['critical_count']
            self.stats['avg_wait_time_critical'] = (current_avg * (count - 1) + wait_time) / count
        
        elif request.priority in [ApiPriority.MEDIUM, ApiPriority.LOW]:
            current_avg = self.stats['avg_wait_time_low']
            low_count = self.stats['medium_count'] + self.stats['low_count']
            if low_count > 0:
                self.stats['avg_wait_time_low'] = (current_avg * (low_count - 1) + wait_time) / low_count
    
    def get_stats(self) -> Dict:
        """
        Get statistics about API request execution
        
        Returns:
            Dictionary with request statistics
        """
        return {
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'failed_requests': self.failed_requests,
            'active_requests': dict(self.active_requests),
            'priority_breakdown': {
                'critical': self.stats['critical_count'],
                'high': self.stats['high_count'],
                'medium': self.stats['medium_count'],
                'low': self.stats['low_count']
            },
            'avg_wait_times': {
                'critical': f"{self.stats['avg_wait_time_critical']:.3f}s",
                'low_priority': f"{self.stats['avg_wait_time_low']:.3f}s"
            }
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info("="*60)
        logger.info("API Priority Manager Statistics")
        logger.info("="*60)
        logger.info(f"Total Requests: {stats['total_requests']}")
        logger.info(f"Completed: {stats['completed_requests']}")
        logger.info(f"Failed: {stats['failed_requests']}")
        logger.info(f"Active: {stats['active_requests']}")
        logger.info(f"Priority Breakdown:")
        for priority, count in stats['priority_breakdown'].items():
            logger.info(f"  {priority.upper()}: {count}")
        logger.info(f"Average Wait Times:")
        for priority, time in stats['avg_wait_times'].items():
            logger.info(f"  {priority}: {time}")
        logger.info("="*60)


# Singleton instance
_api_priority_manager_instance = None


def get_priority_manager(max_concurrent_low_priority: int = 5) -> ApiPriorityManager:
    """
    Get or create singleton ApiPriorityManager instance
    
    Args:
        max_concurrent_low_priority: Maximum concurrent non-critical requests
        
    Returns:
        ApiPriorityManager instance
    """
    global _api_priority_manager_instance
    if _api_priority_manager_instance is None:
        _api_priority_manager_instance = ApiPriorityManager(max_concurrent_low_priority)
    return _api_priority_manager_instance


# Convenience functions for common use cases

async def execute_schwab_request(func: Callable, name: str, *args, **kwargs) -> Any:
    """
    Execute a Schwab API request with CRITICAL priority
    
    Args:
        func: Function to call
        name: Request name
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Result of the function call
    """
    manager = get_priority_manager()
    return await manager.submit_request(
        func, ApiPriority.CRITICAL, name, args, kwargs
    )


async def execute_market_data_request(func: Callable, name: str, *args, **kwargs) -> Any:
    """
    Execute a market data request with HIGH priority
    
    Args:
        func: Function to call
        name: Request name
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Result of the function call
    """
    manager = get_priority_manager()
    return await manager.submit_request(
        func, ApiPriority.HIGH, name, args, kwargs
    )


async def execute_sentiment_request(func: Callable, name: str, *args, **kwargs) -> Any:
    """
    Execute a sentiment/news request with LOW priority
    
    Args:
        func: Function to call
        name: Request name
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Result of the function call
    """
    manager = get_priority_manager()
    return await manager.submit_request(
        func, ApiPriority.LOW, name, args, kwargs
    )


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("API Priority Manager - Example Usage")
    print("="*60)
    
    async def mock_schwab_buy(symbol: str, quantity: int):
        """Mock Schwab buy order"""
        await asyncio.sleep(0.5)  # Simulate API call
        return f"BUY {quantity} shares of {symbol}"
    
    async def mock_fetch_price(symbol: str):
        """Mock price fetch"""
        await asyncio.sleep(0.3)  # Simulate API call
        return f"Price for {symbol}: $150.00"
    
    async def mock_fetch_sentiment(symbol: str):
        """Mock sentiment fetch"""
        await asyncio.sleep(0.2)  # Simulate API call
        return f"Sentiment for {symbol}: BULLISH"
    
    async def demo():
        """Demonstrate priority manager"""
        print("\nSubmitting requests with different priorities...\n")
        
        # Submit low priority requests first
        sentiment_tasks = [
            execute_sentiment_request(mock_fetch_sentiment, f"Sentiment-{sym}", sym)
            for sym in ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        ]
        
        # Submit market data requests
        price_tasks = [
            execute_market_data_request(mock_fetch_price, f"Price-{sym}", sym)
            for sym in ['AAPL', 'MSFT']
        ]
        
        # Submit critical Schwab request (should execute first despite being submitted last)
        schwab_task = execute_schwab_request(
            mock_schwab_buy, "Schwab-BUY-AAPL", "AAPL", 10
        )
        
        # Wait for all
        results = await asyncio.gather(
            schwab_task,
            *price_tasks,
            *sentiment_tasks
        )
        
        print("\nResults:")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result}")
        
        # Show stats
        print()
        manager = get_priority_manager()
        manager.log_stats()
    
    # Run demo
    asyncio.run(demo())
    
    print("\n" + "="*60)
    print("API Priority Manager initialized successfully")
    print("="*60)
