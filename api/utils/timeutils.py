"""
Naive-UTC timestamp helpers.

``datetime.utcnow()`` and ``datetime.utcfromtimestamp()`` are deprecated since
Python 3.12 (https://docs.python.org/
The documented replacement is ``datetime.now(timezone.utc)``; existing callers
and DB columns store naive UTC datetimes, so strip tzinfo to preserve exact
semantics (same comparisons, same ``isoformat() + "Z"`` output).
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now — drop-in replacement for the deprecated ``datetime.utcnow()``."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcfromtimestamp(ts: float) -> datetime:
    """Naive UTC from POSIX timestamp — replaces deprecated ``datetime.utcfromtimestamp()``."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
