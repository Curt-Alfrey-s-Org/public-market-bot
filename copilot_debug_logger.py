#!/usr/bin/env python3
"""
Copilot Debug Logger for market-pie5-bot
Provides detailed debug traces to help GitHub Copilot analyze bot behavior between runs
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class CopilotDebugLogger:
    """
    Specialized debug logger for capturing detailed execution traces
    that help GitHub Copilot analyze bot behavior between runs.
    """
    
    def __init__(self, log_dir: str = "logs", enabled: Optional[bool] = None):
        """
        Initialize the Copilot debug logger
        
        Args:
            log_dir: Directory to store debug log files
            enabled: Override enable state (defaults to COPILOT_DEBUG_MODE env var)
        """
        # Check if debug mode is enabled via environment variable
        if enabled is None:
            enabled = os.getenv('COPILOT_DEBUG_MODE', 'false').lower() == 'true'
        
        self.enabled = enabled
        self.log_dir = Path(log_dir)
        
        # Initialize all attributes to ensure consistent state
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"copilot_debug_{self.session_id}.jsonl"
        self.event_counter = 0
        self._file_handle = None
        
        # Create directory and check write permissions
        try:
            self.log_dir.mkdir(exist_ok=True)
            # Test write permissions by creating a temporary file
            test_file = self.log_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cannot write to log directory {log_dir}: {e}")
            self.enabled = False
            return
        
        # Open file handle for better performance (kept open during session)
        if self.enabled:
            try:
                self._file_handle = open(self.log_file, 'a')
                self._write_header()
            except (OSError, PermissionError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Cannot open log file {self.log_file}: {e}")
                self.enabled = False
    
    def _write_header(self):
        """Write session header to log file"""
        import sys
        header = {
            'event_type': 'session_start',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'environment': {
                'python_version': sys.version,
                'cwd': os.getcwd(),
            }
        }
        self._write_log(header)
    
    def _next_event_id(self) -> int:
        """Get next event ID"""
        self.event_counter += 1
        return self.event_counter
    
    def _write_log(self, data: Dict[str, Any]):
        """Write log entry to file"""
        if not self.enabled or self._file_handle is None:
            return
        
        try:
            self._file_handle.write(json.dumps(data, default=str) + '\n')
            self._file_handle.flush()  # Ensure data is written immediately
        except Exception as e:
            # Use logging module instead of print to maintain consistency
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to write debug log: {e}")
    
    def close(self):
        """Close the log file handle. Should be called at session end."""
        if self._file_handle:
            try:
                self._file_handle.close()
            except Exception:
                # Silently ignore errors during cleanup to avoid interfering with normal shutdown
                pass
            self._file_handle = None
    
    def __del__(self):
        """Destructor to ensure file handle is closed"""
        self.close()
    
    def log_initialization(self, config: Dict[str, Any]):
        """
        Log bot initialization details
        
        Args:
            config: Bot configuration dictionary
        """
        entry = {
            'event_type': 'bot_initialization',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'config': config
        }
        self._write_log(entry)
    
    def log_decision(self, decision_type: str, context: Dict[str, Any], 
                     result: Any, rationale: Optional[str] = None):
        """
        Log a decision point in bot execution
        
        Args:
            decision_type: Type of decision (e.g., 'trade_signal', 'position_sizing')
            context: Context information for the decision
            result: The decision result
            rationale: Optional explanation of why this decision was made
        """
        entry = {
            'event_type': 'decision',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'decision_type': decision_type,
            'context': context,
            'result': result,
            'rationale': rationale
        }
        self._write_log(entry)
    
    def log_trade_execution(self, symbol: str, action: str, 
                           quantity: Optional[float], price: float, 
                           metadata: Optional[Dict] = None):
        """
        Log trade execution details
        
        Args:
            symbol: Stock symbol
            action: Trade action (BUY/SELL)
            quantity: Number of shares (None if unknown at logging time)
            price: Execution price
            metadata: Additional metadata
        """
        entry = {
            'event_type': 'trade_execution',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,  # May be None if calculated elsewhere
            'price': price,
            'metadata': metadata or {}
        }
        self._write_log(entry)
    
    def log_strategy_selection(self, symbol: str, strategies_evaluated: List[str],
                               selected_strategy: str, scores: Dict[str, float],
                               rationale: Optional[str] = None):
        """
        Log strategy selection process
        
        Args:
            symbol: Stock symbol
            strategies_evaluated: List of strategy names evaluated
            selected_strategy: Name of selected strategy
            scores: Dictionary of strategy scores
            rationale: Optional explanation
        """
        entry = {
            'event_type': 'strategy_selection',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'symbol': symbol,
            'strategies_evaluated': strategies_evaluated,
            'selected_strategy': selected_strategy,
            'scores': scores,
            'rationale': rationale
        }
        self._write_log(entry)
    
    def log_error(self, error_type: str, error_message: str, 
                  context: Optional[Dict] = None, stack_trace: Optional[str] = None):
        """
        Log error details for debugging
        
        Args:
            error_type: Type/category of error
            error_message: Error message
            context: Context information when error occurred
            stack_trace: Optional stack trace
        """
        entry = {
            'event_type': 'error',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'stack_trace': stack_trace
        }
        self._write_log(entry)
    
    def log_state_snapshot(self, state_type: str, state_data: Dict[str, Any]):
        """
        Log a snapshot of bot state
        
        Args:
            state_type: Type of state (e.g., 'positions', 'capital', 'metrics')
            state_data: State data dictionary
        """
        entry = {
            'event_type': 'state_snapshot',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'state_type': state_type,
            'state_data': state_data
        }
        self._write_log(entry)
    
    def log_performance_metric(self, metric_name: str, metric_value: float,
                               context: Optional[Dict] = None):
        """
        Log performance metric
        
        Args:
            metric_name: Name of metric (e.g., 'win_rate', 'sharpe_ratio')
            metric_value: Metric value
            context: Optional context information
        """
        entry = {
            'event_type': 'performance_metric',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'metric_name': metric_name,
            'metric_value': metric_value,
            'context': context or {}
        }
        self._write_log(entry)
    
    def log_api_call(self, api_name: str, method: str, success: bool,
                     duration_ms: float, response_summary: Optional[Dict] = None):
        """
        Log API call details
        
        Args:
            api_name: Name of API (e.g., 'schwab', 'yfinance', 'litellm')
            method: API method/endpoint called
            success: Whether call succeeded
            duration_ms: Call duration in milliseconds
            response_summary: Optional summary of response
        """
        entry = {
            'event_type': 'api_call',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'api_name': api_name,
            'method': method,
            'success': success,
            'duration_ms': duration_ms,
            'response_summary': response_summary or {}
        }
        self._write_log(entry)
    
    def log_session_end(self, summary: Dict[str, Any]):
        """
        Log session end with summary
        
        Args:
            summary: Session summary dictionary
        """
        entry = {
            'event_type': 'session_end',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'event_id': self._next_event_id(),
            'summary': summary
        }
        self._write_log(entry)
        # Close file handle after session end
        self.close()
    
    def get_log_file_path(self) -> Optional[Path]:
        """
        Get path to current log file
        
        Returns:
            Path to log file if enabled, None otherwise
        """
        return self.log_file if self.enabled else None


# Singleton instance for global access
_debug_logger = None


def get_debug_logger() -> CopilotDebugLogger:
    """
    Get or create the global debug logger instance
    
    Returns:
        CopilotDebugLogger instance
    """
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = CopilotDebugLogger()
    return _debug_logger


def reset_debug_logger():
    """
    Reset the global debug logger singleton.
    Primarily used for testing to avoid state pollution between tests.
    
    Ensures that any underlying resources (such as open file handles)
    held by the existing logger instance are explicitly closed before
    the singleton reference is cleared.
    """
    global _debug_logger
    if _debug_logger is not None:
        # Best-effort cleanup: close the logger if it exposes a close method
        close_method = getattr(_debug_logger, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception:
                # Ignore errors during cleanup to avoid masking test failures
                pass
    _debug_logger = None


if __name__ == "__main__":
    # Example usage
    print("Copilot Debug Logger Example")
    print("=" * 60)
    
    # Enable debug mode for example
    os.environ['COPILOT_DEBUG_MODE'] = 'true'
    
    # Create logger
    logger = CopilotDebugLogger()
    
    # Log initialization
    logger.log_initialization({
        'total_capital': 10000.0,
        'risk_threshold': 0.02,
        'paper_trading_mode': True
    })
    print(f"✓ Logged initialization")
    
    # Log a decision
    logger.log_decision(
        decision_type='trade_signal',
        context={'symbol': 'AAPL', 'price': 150.0, 'indicators': {'rsi': 65, 'macd': 0.5}},
        result='BUY',
        rationale='RSI indicates oversold, MACD shows bullish momentum'
    )
    print(f"✓ Logged decision")
    
    # Log trade execution
    logger.log_trade_execution(
        symbol='AAPL',
        action='BUY',
        quantity=10.0,
        price=150.25,
        metadata={'strategy': 'momentum', 'confidence': 0.85}
    )
    print(f"✓ Logged trade execution")
    
    # Log state snapshot
    logger.log_state_snapshot(
        state_type='positions',
        state_data={
            'AAPL': {'quantity': 10, 'entry_price': 150.25, 'current_price': 152.0},
            'total_capital': 9850.0
        }
    )
    print(f"✓ Logged state snapshot")
    
    # Log session end
    logger.log_session_end({
        'total_trades': 5,
        'winning_trades': 3,
        'win_rate': 0.60,
        'total_pnl': 150.0
    })
    print(f"✓ Logged session end")
    
    print(f"\n✓ Debug log created at: {logger.get_log_file_path()}")
