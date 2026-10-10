"""
Admin authentication helper for the operator scripts in scripts/.

Every /api/* call needs a JWT, and the control endpoints (bot start/stop/mode,
settings writes) need an ADMIN JWT; the X-API-Key alone is refused there
(security review 2026-09-25). Scripts get the token from the environment:

  MARKET_BOT_ADMIN_TOKEN=<admin JWT>                        (preferred), or
  MARKET_BOT_ADMIN_USERNAME / MARKET_BOT_ADMIN_PASSWORD     (one login at startup).

Tokens are only ever sent as an Authorization header; never print or log them.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

MISSING_TOKEN_HELP = (
    "No admin token: set MARKET_BOT_ADMIN_TOKEN, or MARKET_BOT_ADMIN_USERNAME and "
    "MARKET_BOT_ADMIN_PASSWORD (admin account). /api endpoints require authentication."
)


def login(api_url: str, username: str, password: str, timeout: float = 10) -> Optional[str]:
    """POST /api/auth/login and return the JWT, or None on failure."""
    url = f"{api_url.rstrip('/')}/api/auth/login"
    body = {"username": username, "password": password}
    data: object = {}
    try:
        import requests  # type: ignore

        resp = requests.post(url, json=body, timeout=timeout)
        data = resp.json() if resp.status_code == 200 else {}
    except ImportError:
        from urllib.request import Request, urlopen

        req = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception:
            data = {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        return None
    return data.get("token") or data.get("access_token") or None


def resolve_admin_token(api_url: str) -> Optional[str]:
    """Admin JWT from MARKET_BOT_ADMIN_TOKEN, else a login with MARKET_BOT_ADMIN_USERNAME/PASSWORD."""
    token = os.getenv("MARKET_BOT_ADMIN_TOKEN", "").strip()
    if token:
        return token
    username = os.getenv("MARKET_BOT_ADMIN_USERNAME", "").strip()
    password = os.getenv("MARKET_BOT_ADMIN_PASSWORD", "")
    if username and password:
        return login(api_url, username, password)
    return None


def auth_headers(token: Optional[str]) -> Dict[str, str]:
    """Authorization header dict for requests/urllib (empty when there is no token)."""
    return {"Authorization": f"Bearer {token}"} if token else {}
