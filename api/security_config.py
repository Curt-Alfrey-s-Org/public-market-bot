"""
Central resolution of security-critical configuration (JWT signing secret).

Both token systems in this repo (web/legacy tokens in ``api/auth.py`` and the
mobile v1 tokens in ``api/utils/jwt.py``) sign with the same secret, resolved
here once per process:

- ``JWT_SECRET`` (preferred) or ``JWT_SECRET_KEY`` (legacy alias).
- Production (the default unless ``ENVIRONMENT`` is development/dev/test/
  testing/local): the secret is REQUIRED. A missing value, or one of the old
  public placeholder strings, raises ``RuntimeError`` naming ``JWT_SECRET`` so
  the API fails fast at startup instead of accepting forgeable tokens.
- Non-production: if unset, a random per-process secret is generated (tokens
  stop working after a restart). Set ``JWT_SECRET`` to keep sessions across
  restarts or when running several workers.

Generate a value with:  python -c "import secrets; print(secrets.token_urlsafe(48))"
"""

from __future__ import annotations

import logging
import os
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

JWT_SECRET_ENV = "change-me"
JWT_SECRET_ENV_ALIASES = ("JWT_SECRET", "JWT_SECRET_KEY")
MIN_RECOMMENDED_JWT_SECRET_LENGTH = 32

# Values that were committed as defaults at some point (or are obvious
# placeholders). Anyone can sign tokens with these, so they are refused in
# production.
_PUBLIC_PLACEHOLDER_SECRETS = frozenset(
    {
        "market-bot-change-in-production",
        "your-secret-key-change-in-production",
        "your-secret-key",
        "change-me",
        "changeme",
        "secret",
        "replace-me",
        "<generate-a-long-random-value>",
    }
)

_NON_PRODUCTION_ENVIRONMENTS = frozenset({"development", "dev", "test", "testing", "local"})

_cached_secret: Optional[str] = None


def get_environment() -> str:
    """Deployment environment name (ENVIRONMENT, else APP_ENV). Empty means unspecified."""
    for name in ("ENVIRONMENT", "APP_ENV"):
        value = os.getenv(name, "").strip().lower()
        if value:
            return value
    return ""


def is_production() -> bool:
    """Secure default: anything that is not explicitly a dev/test environment is production."""
    return get_environment() not in _NON_PRODUCTION_ENVIRONMENTS


def _read_configured_secret() -> str:
    """Single read path for the secret: JWT_SECRET wins; JWT_SECRET_KEY is a legacy alias.

    If both are set to different values, JWT_SECRET is used and a warning names the
    ignored variable, so the two names can't silently disagree.
    """
    values = {name: os.getenv(name, "").strip() for name in JWT_SECRET_ENV_ALIASES}
    configured = [(name, value) for name, value in values.items() if value]
    if len(configured) > 1 and len({value for _, value in configured}) > 1:
        logger.warning(
            "Both %s and %s are set to different values; using %s and ignoring %s. "
            "Remove the legacy variable.",
            configured[0][0], configured[1][0], configured[0][0], configured[1][0],
        )
    return configured[0][1] if configured else ""


def resolve_jwt_secret() -> str:
    """Resolve the JWT secret from the environment (uncached). Raises RuntimeError in production if unusable."""
    value = _read_configured_secret()
    if value and value.lower() in _PUBLIC_PLACEHOLDER_SECRETS:
        if is_production():
            raise RuntimeError(
                f"{JWT_SECRET_ENV} is set to a public placeholder value. Set {JWT_SECRET_ENV} to a long "
                "random secret (python -c \"import secrets; print(secrets.token_urlsafe(48))\")."
            )
        logger.warning("%s is a public placeholder value; generating a throwaway secret (non-production only)", JWT_SECRET_ENV)
        value = ""
    if value:
        if len(value) < MIN_RECOMMENDED_JWT_SECRET_LENGTH:
            logger.warning(
                "%s is shorter than %d characters; use a longer random value",
                JWT_SECRET_ENV,
                MIN_RECOMMENDED_JWT_SECRET_LENGTH,
            )
        return value
    if is_production():
        raise RuntimeError(
            f"{JWT_SECRET_ENV} is not set. It is required in production (ENVIRONMENT="
            f"{get_environment() or 'unset'}). Set {JWT_SECRET_ENV} to a long random secret "
            "(python -c \"import secrets; print(secrets.token_urlsafe(48))\"), or set "
            "ENVIRONMENT=development for local development."
        )
    logger.warning(
        "%s not set (ENVIRONMENT=%s): using a random per-process secret; sessions end on restart",
        JWT_SECRET_ENV,
        get_environment(),
    )
    return secrets.token_urlsafe(48)


def get_jwt_secret() -> str:
    """Process-wide JWT secret (resolved once so both token modules share it)."""
    global _cached_secret
    if _cached_secret is None:
        _cached_secret = resolve_jwt_secret()
    return _cached_secret
