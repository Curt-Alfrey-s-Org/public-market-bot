"""Pytest configuration. Ensures project root is in sys.path for imports like 'from main import TradingBot'."""
import sys
from pathlib import Path

# Add project root so tests can import main, api, etc.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
