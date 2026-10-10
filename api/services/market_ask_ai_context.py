"""
Safe context assembly for the per-page "Ask AI" narrative feature.

Trust boundary: the Ask AI feature narrates *domain* data only (performance
stats, symbols, decision factors, settings labels). It must NEVER receive
Schwab account numbers, balances, OAuth tokens, API keys, or other secrets,
even if the frontend accidentally includes them in the page payload. This
module re-sanitizes every context dict server-side (denylist + size caps)
before it is sent to the LiteLLM brain.
"""

import re
from typing import Any, Dict

# Pages allowed to use the Ask AI narrative.
ALLOWED_PAGES = {
    "dashboard",
    "trades",
    "pending-trades",
    "decision-report",
    "settings",
}

# Substrings that mark a key as sensitive. Any matching key is dropped.
_SENSITIVE_KEY_PATTERNS = [
    "token",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "balance",
    "cash",
    "account_number",
    "account_id",
    "accountnumber",
    "acct",
    "ssn",
    "schwab",
    "refresh",
    "access_token",
    "private",
    "credential",
]

_MAX_STRING = 2000
_MAX_ITEMS = 50
_MAX_DEPTH = 4


def _is_sensitive_key(key: str) -> bool:
    k = str(key).lower()
    return any(pat in k for pat in _SENSITIVE_KEY_PATTERNS)


def sanitize_context(value: Any, depth: int = 0) -> Any:
    """Recursively drop sensitive keys and cap sizes. Pure domain data remains."""
    if depth > _MAX_DEPTH:
        return "[truncated]"
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in list(value.items())[:_MAX_ITEMS]:
            if _is_sensitive_key(k):
                continue
            out[str(k)] = sanitize_context(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [sanitize_context(v, depth + 1) for v in list(value)[:_MAX_ITEMS]]
    if isinstance(value, str):
        return value[:_MAX_STRING]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:_MAX_STRING]


def build_page_context(page: str, payload: Any) -> Dict[str, Any]:
    """Return a sanitized context dict for the given page."""
    safe = sanitize_context(payload if isinstance(payload, dict) else {"data": payload})
    return {"page": page, "context": safe}


def is_allowed_page(page: str) -> bool:
    return (page or "").strip().lower() in ALLOWED_PAGES
