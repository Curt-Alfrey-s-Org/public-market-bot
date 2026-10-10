"""
API V1 Routes
All endpoints under /api/v1/ prefix
"""

from . import auth
from . import bot
from . import trades
from . import stats
from . import reports
from . import settings
from . import config

__all__ = ['auth', 'bot', 'trades', 'stats', 'reports', 'settings', 'config']
