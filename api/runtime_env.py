"""
Where runtime mode/settings changes are persisted.

``POST /api/bot/mode``, ``POST /api/bot/start`` (with a mode) and
``PUT /api/settings`` save their changes as ``KEY=value`` lines in an env file
so that every API worker and the next bot start see the same values.

Security review 2026-09-25 (low): inside the Docker image that file used to be
``/app/.env``, i.e. a file inside the container layer. It is not the operator's
``.env`` (that one is excluded by ``.dockerignore`` and never mounted), so a
write there is lost on the next ``docker compose up`` and would place
configuration in the image filesystem. The rules are now:

- ``BOT_RUNTIME_ENV_FILE`` set: runtime changes go to that file (for Docker,
  point it at the mounted data volume, e.g. ``/app/data/runtime.env``). The
  file is created if missing and holds only the keys the API writes.
- Running in a container without ``BOT_RUNTIME_ENV_FILE``: nothing is written.
  Mode changes apply to the current API process only, and settings writes are
  reported back with ``persisted: false``.
- Host install (not a container): the project ``.env`` exactly as before.

This module only decides *where* values are stored. It does not change any
trading default: with no runtime file the compose/env values
(``PAPER_TRADING_MODE`` etc.) apply unchanged.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ENV_FILE_VAR = "BOT_RUNTIME_ENV_FILE"
RUNNING_IN_CONTAINER_VAR = "RUNNING_IN_CONTAINER"

_TRUE = ("1", "true", "yes", "on")
_FALSE = ("0", "false", "no", "off")


def running_in_container() -> bool:
    """True inside Docker/containers. ``RUNNING_IN_CONTAINER`` (true/false) overrides detection."""
    flag = os.getenv(RUNNING_IN_CONTAINER_VAR, "").strip().lower()
    if flag in _TRUE:
        return True
    if flag in _FALSE:
        return False
    return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")


def runtime_env_file_is_explicit() -> bool:
    """True when the operator chose the file with ``BOT_RUNTIME_ENV_FILE``."""
    return bool(os.getenv(RUNTIME_ENV_FILE_VAR, "").strip())


def runtime_env_file() -> Optional[Path]:
    """Env file used for runtime changes, or ``None`` when changes must not be written to disk."""
    override = os.getenv(RUNTIME_ENV_FILE_VAR, "").strip()
    if override:
        return Path(override)
    if running_in_container():
        return None
    return PROJECT_ROOT / ".env"


def not_persisted_reason() -> str:
    """Human-readable reason used in logs/responses when ``runtime_env_file()`` is ``None``."""
    return (
        "running in a container without "
        f"{RUNTIME_ENV_FILE_VAR}; the change applies to this API process only. Set "
        f"{RUNTIME_ENV_FILE_VAR} to a file on a mounted volume (e.g. /app/data/runtime.env) to persist it."
    )


def writable_runtime_env_file() -> Optional[Path]:
    """
    File that runtime changes may be written to, or ``None``.

    An explicitly configured file is created (with its parent directory) when
    missing. The implicit host ``.env`` is only updated if it already exists,
    as before.
    """
    path = runtime_env_file()
    if path is None:
        return None
    if path.exists():
        return path
    if not runtime_env_file_is_explicit():
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        logger.info("Created runtime env file %s", path)
        return path
    except FileExistsError:
        return path
    except OSError as e:
        logger.warning("Could not create runtime env file %s: %s", path, e)
        return None


def read_runtime_env() -> Dict[str, str]:
    """Parse ``KEY=value`` lines of the runtime env file (empty dict when there is none)."""
    path = runtime_env_file()
    values: Dict[str, str] = {}
    if path is None or not path.exists():
        return values
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                    val = val[1:-1]
                values[key] = val
    except OSError as e:
        logger.warning("Could not read runtime env file %s: %s", path, e)
    return values
