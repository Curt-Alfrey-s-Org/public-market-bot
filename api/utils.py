"""
Utility functions for API
Separated to avoid circular imports
"""

import time
from datetime import datetime

# Global bot instance (will be set when bot starts)
bot_instance = None

# Startup timing tracking
_startup_timings = {}

def set_bot_instance(bot):
    """Set the global bot instance. Pass None to clear (e.g. on shutdown). Always replace so Restart uses the new bot and Decision Report shows live data."""
    global bot_instance
    bot_instance = bot
    return bot_instance

def get_bot_instance():
    """Get the global bot instance"""
    return bot_instance

def record_startup_timing(phase: str, duration: float):
    """Record timing for a startup phase"""
    _startup_timings[phase] = {
        'duration_s': duration,
        'duration_ms': duration * 1000,
        'timestamp': datetime.now().isoformat()
    }

def get_startup_timings():
    """Get all recorded startup timings"""
    return _startup_timings.copy()
