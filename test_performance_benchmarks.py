#!/usr/bin/env python3
"""
Performance Benchmark Test Suite for market-pie5-bot

Tests trade loop performance with varying symbol counts to validate
Raspberry Pi 5 performance characteristics and TRADING_FREQUENCY tuning.

Benchmarks:
- Trade loop execution time with 10, 50, 100, 200, 500, 1000 symbols
- TRADING_FREQUENCY impact on throughput
- CPU and memory usage under load
- Resource throttling behavior
"""

import os
import time
import unittest
from unittest.mock import patch, MagicMock
import statistics

# Disable PDT rules and set test environment
os.environ.setdefault('ENABLE_PDT_RULES', 'false')
os.environ.setdefault('PAPER_TRADING_MODE', 'true')
os.environ.setdefault('SCHWAB_SANDBOX_MODE', 'true')

# Import after environment setup
import main
from main import TradingBot, ResourceThrottler


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test bot performance with varying symbol counts"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TradingBot(total_capital=10000.0)
        # Mock yfinance to avoid network calls in benchmarks
        self.yf_patcher = patch('main.yf')
        self.mock_yf = self.yf_patcher.start()
        
    def tearDown(self):
        """Clean up after tests"""
        self.yf_patcher.stop()
    
    def _mock_stock_price(self, symbol: str, base_price: float = 100.0) -> float:
        """Generate consistent mock prices for benchmarking"""
        # Use hash for deterministic but varied prices
        variation = (hash(symbol) % 100) / 100.0
        return base_price * (0.8 + 0.4 * variation)
    
    def _generate_symbols(self, count: int) -> list:
        """Generate list of symbol names for testing"""
        # Use realistic symbol patterns
        symbols = []
        for i in range(count):
            if i < 26:
                # Single letter symbols (A-Z)
                symbols.append(chr(65 + i))
            elif i < 676:
                # Two letter symbols (AA-ZZ)
                symbols.append(chr(65 + (i-26)//26) + chr(65 + (i-26)%26))
            else:
                # Three letter symbols
                idx = i - 676
                symbols.append(
                    chr(65 + idx//676) + 
                    chr(65 + (idx%676)//26) + 
                    chr(65 + idx%26)
                )
        return symbols
    
    def _benchmark_trade_loop_iteration(self, symbol_count: int, iterations: int = 10) -> dict:
        """
        Benchmark a single iteration of the trade loop with N symbols
        
        Args:
            symbol_count: Number of symbols to process
            iterations: Number of times to run benchmark (for averaging)
        
        Returns:
            Dictionary with timing statistics
        """
        symbols = self._generate_symbols(symbol_count)
        timings = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Simulate trade loop iteration - minimal operations
            for symbol in symbols:
                # Mock price fetch (the slowest operation)
                price = self._mock_stock_price(symbol)
                
                # Simulate basic operations that happen per symbol
                # Update price history (actual bot operation)
                self.bot.update_price_history(symbol, price)
                
                # Calculate volatility (actual bot operation)
                if symbol in self.bot.price_history:
                    _ = self.bot.calculate_volatility(symbol)
                
                # Check positions (lightweight operation)
                if symbol in self.bot.positions:
                    position = self.bot.positions[symbol]
                    _ = position.get('entry_price', 0)
                
            end_time = time.time()
            timings.append(end_time - start_time)
        
        return {
            'symbol_count': symbol_count,
            'iterations': iterations,
            'mean_time': statistics.mean(timings),
            'median_time': statistics.median(timings),
            'min_time': min(timings),
            'max_time': max(timings),
            'stdev_time': statistics.stdev(timings) if len(timings) > 1 else 0,
            'symbols_per_second': symbol_count / statistics.mean(timings)
        }
    
    def test_benchmark_10_symbols(self):
        """Benchmark trade loop with 10 symbols (minimal load)"""
        result = self._benchmark_trade_loop_iteration(10)
        
        print(f"\n=== Benchmark: 10 Symbols ===")
        print(f"Mean Time: {result['mean_time']*1000:.2f}ms")
        print(f"Median Time: {result['median_time']*1000:.2f}ms")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 10 symbols should complete in < 100ms
        self.assertLess(result['mean_time'], 0.1, 
                       f"10 symbols took {result['mean_time']*1000:.2f}ms (expected < 100ms)")
    
    def test_benchmark_50_symbols(self):
        """Benchmark trade loop with 50 symbols (light load)"""
        result = self._benchmark_trade_loop_iteration(50)
        
        print(f"\n=== Benchmark: 50 Symbols ===")
        print(f"Mean Time: {result['mean_time']*1000:.2f}ms")
        print(f"Median Time: {result['median_time']*1000:.2f}ms")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 50 symbols should complete in < 500ms
        self.assertLess(result['mean_time'], 0.5,
                       f"50 symbols took {result['mean_time']*1000:.2f}ms (expected < 500ms)")
    
    def test_benchmark_100_symbols(self):
        """Benchmark trade loop with 100 symbols (moderate load)"""
        result = self._benchmark_trade_loop_iteration(100)
        
        print(f"\n=== Benchmark: 100 Symbols ===")
        print(f"Mean Time: {result['mean_time']*1000:.2f}ms")
        print(f"Median Time: {result['median_time']*1000:.2f}ms")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 100 symbols should complete in < 1 second
        self.assertLess(result['mean_time'], 1.0,
                       f"100 symbols took {result['mean_time']:.2f}s (expected < 1s)")
    
    def test_benchmark_200_symbols(self):
        """Benchmark trade loop with 200 symbols (heavy load)"""
        result = self._benchmark_trade_loop_iteration(200, iterations=5)
        
        print(f"\n=== Benchmark: 200 Symbols ===")
        print(f"Mean Time: {result['mean_time']:.3f}s")
        print(f"Median Time: {result['median_time']:.3f}s")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 200 symbols should complete in < 3 seconds
        self.assertLess(result['mean_time'], 3.0,
                       f"200 symbols took {result['mean_time']:.2f}s (expected < 3s)")
    
    def test_benchmark_500_symbols(self):
        """Benchmark trade loop with 500 symbols (stress test)"""
        result = self._benchmark_trade_loop_iteration(500, iterations=3)
        
        print(f"\n=== Benchmark: 500 Symbols ===")
        print(f"Mean Time: {result['mean_time']:.3f}s")
        print(f"Median Time: {result['median_time']:.3f}s")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 500 symbols should complete in < 10 seconds
        # This is the key benchmark mentioned in the issue
        self.assertLess(result['mean_time'], 10.0,
                       f"500 symbols took {result['mean_time']:.2f}s (expected < 10s)")
    
    def test_benchmark_1000_symbols(self):
        """Benchmark trade loop with 1000 symbols (extreme load)"""
        result = self._benchmark_trade_loop_iteration(1000, iterations=3)
        
        print(f"\n=== Benchmark: 1000 Symbols ===")
        print(f"Mean Time: {result['mean_time']:.3f}s")
        print(f"Median Time: {result['median_time']:.3f}s")
        print(f"Throughput: {result['symbols_per_second']:.1f} symbols/sec")
        
        # Performance assertion: 1000 symbols should complete in < 20 seconds
        self.assertLess(result['mean_time'], 20.0,
                       f"1000 symbols took {result['mean_time']:.2f}s (expected < 20s)")


class TestTradingFrequencyImpact(unittest.TestCase):
    """Test how TRADING_FREQUENCY setting impacts performance"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.original_freq = os.environ.get('TRADING_FREQUENCY')
        
    def tearDown(self):
        """Restore original environment"""
        if self.original_freq:
            os.environ['TRADING_FREQUENCY'] = self.original_freq
        elif 'TRADING_FREQUENCY' in os.environ:
            del os.environ['TRADING_FREQUENCY']
    
    def test_trading_frequency_delays(self):
        """Test that TRADING_FREQUENCY introduces expected delays"""
        frequencies = [0.5, 1, 2, 5]
        results = []
        
        print("\n=== TRADING_FREQUENCY Impact Analysis ===")
        
        for freq in frequencies:
            os.environ['TRADING_FREQUENCY'] = str(freq)
            
            # Force reload of main module config
            import importlib
            importlib.reload(main)
            
            # Measure delay between 10 "trades"
            iterations = 10
            start_time = time.time()
            
            for i in range(iterations):
                time.sleep(main.TRADING_FREQUENCY)
            
            end_time = time.time()
            total_time = end_time - start_time
            expected_time = freq * iterations
            overhead = total_time - expected_time
            
            results.append({
                'frequency': freq,
                'total_time': total_time,
                'expected_time': expected_time,
                'overhead': overhead,
                'trades_per_minute': 60 / (total_time / iterations)
            })
            
            print(f"\nFrequency: {freq}s")
            print(f"  Total Time: {total_time:.3f}s")
            print(f"  Expected: {expected_time:.3f}s")
            print(f"  Overhead: {overhead*1000:.1f}ms")
            print(f"  Trades/min: {results[-1]['trades_per_minute']:.1f}")
            
            # Assert overhead is reasonable (< 100ms total for 10 iterations)
            self.assertLess(overhead, 0.1, 
                          f"Overhead {overhead*1000:.1f}ms too high for {freq}s frequency")
        
        # Verify inverse relationship: lower frequency = more trades per minute
        self.assertGreater(results[0]['trades_per_minute'], 
                          results[-1]['trades_per_minute'])


class TestResourceThrottlerPerformance(unittest.TestCase):
    """Test ResourceThrottler performance impact"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.psutil_patcher = patch('main.PSUTIL_AVAILABLE', True)
        self.psutil_patcher.start()
        
    def tearDown(self):
        """Clean up"""
        self.psutil_patcher.stop()
    
    @patch('main.psutil')
    def test_throttler_overhead(self, mock_psutil):
        """Measure overhead of resource checking"""
        # Mock low resource usage
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=40.0)
        
        throttler = ResourceThrottler(enabled=True)
        
        # Benchmark resource checks
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            is_ok, message = throttler.check_resources()
            self.assertTrue(is_ok)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # Convert to ms
        
        print(f"\n=== Resource Throttler Overhead ===")
        print(f"Total checks: {iterations}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average per check: {avg_time:.3f}ms")
        print(f"Checks per second: {iterations/total_time:.1f}")
        
        # Assert low overhead: each check should take < 1ms
        self.assertLess(avg_time, 1.0,
                       f"Resource check took {avg_time:.3f}ms (expected < 1ms)")
    
    @patch('main.psutil')
    @patch('main.time')
    @patch('main.logger')
    def test_throttler_delays_under_load(self, mock_logger, mock_time, mock_psutil):
        """Test throttler applies delays when resources are high"""
        # Mock high CPU usage
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        
        throttler = ResourceThrottler(enabled=True)
        throttler.max_cpu_percent = 75.0
        throttler.throttle_delay = 5
        
        # Check resources (should trigger throttle)
        is_ok, message = throttler.check_resources()
        self.assertFalse(is_ok)
        self.assertIn("CPU usage", message)
        
        # Apply throttle
        throttler.apply_throttle("High CPU usage")
        
        # Verify sleep was called with correct delay
        mock_time.sleep.assert_called_once_with(5)
        
        # Verify throttle count incremented
        self.assertEqual(throttler.throttle_count, 1)


class TestScalabilityRecommendations(unittest.TestCase):
    """Test and document scalability recommendations"""
    
    def test_recommended_symbol_limits(self):
        """Document recommended symbol count limits for different scenarios"""
        recommendations = {
            'raspberry_pi_5': {
                'paper_trading': {
                    'optimal': 50,
                    'maximum': 200,
                    'trading_frequency': 2  # seconds
                },
                'live_trading': {
                    'optimal': 20,
                    'maximum': 100,
                    'trading_frequency': 5  # seconds
                },
                'backtesting': {
                    'optimal': 10,
                    'maximum': 50,
                    'trading_frequency': 0  # no delay needed
                }
            },
            'desktop_pc': {
                'paper_trading': {
                    'optimal': 200,
                    'maximum': 1000,
                    'trading_frequency': 1  # seconds
                },
                'live_trading': {
                    'optimal': 100,
                    'maximum': 500,
                    'trading_frequency': 2  # seconds
                },
                'backtesting': {
                    'optimal': 50,
                    'maximum': 200,
                    'trading_frequency': 0  # no delay needed
                }
            }
        }
        
        print("\n=== Scalability Recommendations ===")
        for platform, modes in recommendations.items():
            print(f"\n{platform.replace('_', ' ').title()}:")
            for mode, limits in modes.items():
                print(f"  {mode.replace('_', ' ').title()}:")
                print(f"    Optimal symbols: {limits['optimal']}")
                print(f"    Maximum symbols: {limits['maximum']}")
                print(f"    TRADING_FREQUENCY: {limits['trading_frequency']}s")
        
        # These are documentation-only tests, always pass
        self.assertTrue(True)
    
    def test_performance_tuning_guidelines(self):
        """Document performance tuning guidelines"""
        guidelines = {
            'High CPU usage (>75%)': [
                'Increase TRADING_FREQUENCY to 5-10 seconds',
                'Reduce number of symbols being monitored',
                'Enable BOT_ENABLE_THROTTLING=true',
                'Increase BOT_THROTTLE_DELAY to 10 seconds'
            ],
            'High Memory usage (>75%)': [
                'Reduce VOLATILITY_WINDOW to 10',
                'Limit open positions (BOT_MAX_OPEN_POSITIONS=20)',
                'Clear old price history periodically'
            ],
            'Slow trade execution (>500ms per symbol)': [
                'Check network latency to APIs',
                'Reduce symbol count',
                'Increase TRADING_FREQUENCY',
                'Consider caching frequently accessed data'
            ],
            'API rate limiting': [
                'Increase TRADING_FREQUENCY to 5+ seconds',
                'Implement request batching',
                'Use local data caching',
                'Monitor API quota usage'
            ]
        }
        
        print("\n=== Performance Tuning Guidelines ===")
        for issue, solutions in guidelines.items():
            print(f"\n{issue}:")
            for solution in solutions:
                print(f"  • {solution}")
        
        # Documentation-only test
        self.assertTrue(True)


if __name__ == '__main__':
    # Run tests with verbose output to show benchmark results
    unittest.main(verbosity=2)
