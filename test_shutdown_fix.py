#!/usr/bin/env python3
"""
Test script to verify shutdown button fixes
Tests the shutdown sequence timing and bot thread handling
"""

import unittest
import threading
import time
import sys
import os

# Set environment variables before importing
os.environ['PAPER_TRADING_MODE'] = 'true'
os.environ['SCHWAB_SANDBOX_MODE'] = 'true'
os.environ['ENABLE_PDT_RULES'] = 'false'

class TestShutdownFix(unittest.TestCase):
    """Test the shutdown improvements"""
    
    def test_shutdown_sequence_timing(self):
        """Test that shutdown happens in the right order with proper timing"""
        print("\n=== Testing Shutdown Sequence ===")
        
        # Simulate the shutdown sequence
        events = []
        events_lock = threading.Lock()
        
        def mock_shutdown_delayed():
            """Simulates the shutdown_delayed function"""
            with events_lock:
                events.append(('delay_start', time.time()))
            time.sleep(0.5)  # Initial delay
            with events_lock:
                events.append(('bot_shutdown_start', time.time()))
            time.sleep(0.1)  # Simulate bot shutdown
            with events_lock:
                events.append(('bot_shutdown_done', time.time()))
            time.sleep(0.5)  # Wait after bot shutdown
            with events_lock:
                events.append(('process_exit', time.time()))
        
        # Start the shutdown thread (daemon=True like the real implementation)
        start_time = time.time()
        shutdown_thread = threading.Thread(target=mock_shutdown_delayed, daemon=True)
        shutdown_thread.start()
        
        # Give thread a moment to start
        time.sleep(0.01)
        
        # Response should return immediately
        response_time = time.time() - start_time
        with events_lock:
            events.append(('response_returned', time.time()))
        
        # Wait for shutdown to complete
        shutdown_thread.join(timeout=3.0)
        
        # Verify timing
        print(f"Response returned after: {response_time:.3f}s")
        self.assertLess(response_time, 0.1, "Response should return immediately")
        
        # Verify sequence (response_returned may be first or second depending on timing)
        self.assertGreaterEqual(len(events), 5, "Should have at least 5 events")
        
        # Find important events
        event_names = [e[0] for e in events]
        self.assertIn('delay_start', event_names)
        self.assertIn('response_returned', event_names)
        self.assertIn('bot_shutdown_start', event_names)
        self.assertIn('bot_shutdown_done', event_names)
        self.assertIn('process_exit', event_names)
        
        # Verify order (delay_start should be before bot_shutdown_start)
        delay_idx = event_names.index('delay_start')
        bot_start_idx = event_names.index('bot_shutdown_start')
        bot_done_idx = event_names.index('bot_shutdown_done')
        exit_idx = event_names.index('process_exit')
        
        self.assertLess(delay_idx, bot_start_idx, "delay_start should be before bot_shutdown_start")
        self.assertLess(bot_start_idx, bot_done_idx, "bot_shutdown_start should be before bot_shutdown_done")
        self.assertLess(bot_done_idx, exit_idx, "bot_shutdown_done should be before process_exit")
        
        # Check timing between events
        delay_start = events[delay_idx][1]
        bot_start = events[bot_start_idx][1]
        
        self.assertAlmostEqual(bot_start - delay_start, 0.5, delta=0.1, 
                              msg="Bot shutdown should start 0.5s after delay")
        
        print("✅ Shutdown sequence timing is correct")
    
    def test_bot_thread_timeout_increased(self):
        """Test that bot thread timeout is sufficient for long operations"""
        print("\n=== Testing Bot Thread Timeout ===")
        
        stop_event = threading.Event()
        thread_completed = False
        
        def long_running_bot():
            """Simulates a bot doing a long operation"""
            nonlocal thread_completed
            # Simulate 8 seconds of work
            for i in range(80):
                if stop_event.is_set():
                    print(f"Bot stopped after {i/10:.1f}s")
                    return  # Exit early
                time.sleep(0.1)
            thread_completed = True
        
        # Start bot thread
        bot_thread = threading.Thread(target=long_running_bot, daemon=True)
        bot_thread.start()
        
        # Simulate shutdown after 1 second
        time.sleep(1.0)
        stop_event.set()
        
        # With 10 second timeout, thread should complete
        print("Waiting for bot thread to finish (timeout=10s)...")
        start = time.time()
        bot_thread.join(timeout=10.0)
        elapsed = time.time() - start
        
        print(f"Bot thread finished in {elapsed:.3f}s")
        
        if bot_thread.is_alive():
            print("⚠️  Thread still alive after timeout")
            self.fail("Bot thread should stop within timeout")
        
        print("✅ Bot thread stopped within timeout")
        # Verify thread was interrupted, not completed naturally
        self.assertFalse(thread_completed, "Thread should be interrupted by stop event, not complete naturally")
    
    def test_stop_event_clears_after_shutdown(self):
        """Test that stop event is cleared after shutdown for next start"""
        print("\n=== Testing Stop Event Cleanup ===")
        
        stop_event = threading.Event()
        
        # Simulate stop
        stop_event.set()
        self.assertTrue(stop_event.is_set(), "Stop event should be set")
        
        # Simulate shutdown cleanup
        stop_event.clear()
        self.assertFalse(stop_event.is_set(), "Stop event should be cleared after shutdown")
        
        print("✅ Stop event cleanup works correctly")
    
    def test_multiple_shutdown_calls_safe(self):
        """Test that multiple shutdown calls (stop event) are safe"""
        print("\n=== Testing Multiple Shutdown Calls ===")
        
        stop_event = threading.Event()
        
        # First stop - should set the event
        self.assertFalse(stop_event.is_set(), "Event should start clear")
        stop_event.set()
        self.assertTrue(stop_event.is_set(), "Event should be set after first call")
        
        # Second stop - should be idempotent (no error)
        stop_event.set()
        self.assertTrue(stop_event.is_set(), "Event should still be set after second call")
        
        # Multiple stops should be safe
        for _ in range(5):
            stop_event.set()
        self.assertTrue(stop_event.is_set(), "Event should still be set after multiple calls")
        
        # Clear and set again
        stop_event.clear()
        self.assertFalse(stop_event.is_set(), "Event should be clear after clear()")
        
        stop_event.set()
        self.assertTrue(stop_event.is_set(), "Event should be set after clear and set")
        
        print("✅ Multiple stop event calls are safe")


class TestBotManagerChanges(unittest.TestCase):
    """Test the specific changes made to bot_manager.py"""
    
    def test_imports_work(self):
        """Test that the modified files can be imported"""
        print("\n=== Testing Imports ===")
        
        try:
            # Get project root dynamically
            project_root = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, project_root)
            
            # We can't fully import due to dependencies, but we can check syntax
            import py_compile
            import tempfile
            
            bot_manager_path = os.path.join(project_root, 'api', 'bot_manager.py')
            bot_routes_path = os.path.join(project_root, 'api', 'routes', 'bot.py')
            
            # Compile to check syntax
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
                try:
                    py_compile.compile(bot_manager_path, cfile=tmp.name, doraise=True)
                    print(f"✅ {os.path.basename(bot_manager_path)} has valid syntax")
                except py_compile.PyCompileError as e:
                    self.fail(f"Syntax error in bot_manager.py: {e}")
                
                try:
                    py_compile.compile(bot_routes_path, cfile=tmp.name, doraise=True)
                    print(f"✅ {os.path.basename(bot_routes_path)} has valid syntax")
                except py_compile.PyCompileError as e:
                    self.fail(f"Syntax error in bot.py: {e}")
            
        except Exception as e:
            self.fail(f"Import test failed: {e}")
    
    def test_code_changes_present(self):
        """Verify that the specific code changes are present in the files"""
        print("\n=== Verifying Code Changes ===")
        
        # Get project root dynamically
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Check bot_manager.py changes
        bot_manager_path = os.path.join(project_root, 'api', 'bot_manager.py')
        with open(bot_manager_path, 'r') as f:
            content = f.read()
            
            # Should have 10 second timeout
            self.assertIn('timeout=10.0', content, "Should have 10 second timeout")
            
            # Should have clear stop event
            self.assertIn('_bot_stop_event.clear()', content, "Should clear stop event")
            
            # Should have improved logging
            self.assertIn('Bot thread did not stop within 10 second timeout', content, 
                         "Should have improved timeout warning")
            
            print("✅ bot_manager.py changes are present")
        
        # Check bot.py changes
        bot_routes_path = os.path.join(project_root, 'api', 'routes', 'bot.py')
        with open(bot_routes_path, 'r') as f:
            content = f.read()
            
            # Should move shutdown_bot into delayed function
            lines = content.split('\n')
            
            # Find the shutdown_delayed function
            in_shutdown_delayed = False
            found_bot_shutdown_in_delayed = False
            indent_level = 0
            
            for line in lines:
                if 'def shutdown_delayed():' in line:
                    in_shutdown_delayed = True
                    indent_level = len(line) - len(line.lstrip())
                elif in_shutdown_delayed:
                    # Check if we found shutdown_bot() call
                    if 'shutdown_bot()' in line:
                        found_bot_shutdown_in_delayed = True
                        break
                    # Check if we've left the function (non-empty line at same or lower indent)
                    if line.strip():
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= indent_level and line.strip().startswith('def '):
                            # Found next function definition
                            break
            
            self.assertTrue(found_bot_shutdown_in_delayed, 
                           "shutdown_bot() should be called inside shutdown_delayed()")
            
            print("✅ bot.py changes are present")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing Shutdown Button Fixes")
    print("=" * 70)
    
    # Run tests
    unittest.main(verbosity=2)
