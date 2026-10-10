"""
Review 2026-09-25 (low): "Mode writes .env inside the container".

Runtime mode/settings changes go to BOT_RUNTIME_ENV_FILE when set; inside a
container without it nothing is written to disk; host installs keep using the
project .env. Trading defaults are not changed by any of this.

Every test points the helpers at tmp_path or disables persistence, so the real
project .env is never read or written.
"""

import os

import pytest
from fastapi.testclient import TestClient

import api.routes.bot as bot_routes
import api.runtime_env as runtime_env
from api.auth import create_access_token
from api.main import app

MODE_KEYS = ("PAPER_TRADING_MODE", "SCHWAB_SANDBOX_MODE", "SCHWAB_API_ENABLED", "DRY_RUN_MODE",
             "WEB_GUI_CONTINUOUS_TRADING", "WEB_GUI_DEBUG", "ENABLE_PDT_RULES")


@pytest.fixture(autouse=True)
def _restore_mode_env(monkeypatch):
    # _apply_mode_to_env writes os.environ directly; monkeypatch restores it afterwards.
    for key in MODE_KEYS:
        monkeypatch.setenv(key, os.environ.get(key, ""))
    yield


def _admin():
    return {"Authorization": f"Bearer {create_access_token('admin', subject='pytest-admin')}"}


def test_explicit_file_wins(monkeypatch, tmp_path):
    target = tmp_path / "data" / "runtime.env"
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    monkeypatch.setenv("RUNNING_IN_CONTAINER", "true")
    assert runtime_env.runtime_env_file() == target


def test_container_without_explicit_file_does_not_persist(monkeypatch):
    monkeypatch.delenv("BOT_RUNTIME_ENV_FILE", raising=False)
    monkeypatch.setenv("RUNNING_IN_CONTAINER", "true")
    assert runtime_env.runtime_env_file() is None
    assert runtime_env.writable_runtime_env_file() is None
    assert runtime_env.read_runtime_env() == {}


def test_host_install_keeps_project_dotenv(monkeypatch):
    monkeypatch.delenv("BOT_RUNTIME_ENV_FILE", raising=False)
    monkeypatch.setenv("RUNNING_IN_CONTAINER", "false")
    assert runtime_env.runtime_env_file() == runtime_env.PROJECT_ROOT / ".env"
    assert not runtime_env.runtime_env_file_is_explicit()


def test_explicit_file_is_created_private(monkeypatch, tmp_path):
    target = tmp_path / "data" / "runtime.env"
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    path = runtime_env.writable_runtime_env_file()
    assert path == target and target.exists()
    assert (target.stat().st_mode & 0o777) == 0o600


def test_apply_mode_in_container_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.delenv("BOT_RUNTIME_ENV_FILE", raising=False)
    monkeypatch.setenv("RUNNING_IN_CONTAINER", "true")
    opened = []
    real_open = open

    def spy_open(path, mode="r", *a, **kw):
        if "w" in mode or "a" in mode:
            opened.append(str(path))
        return real_open(path, mode, *a, **kw)

    monkeypatch.setattr("builtins.open", spy_open)
    bot_routes._apply_mode_to_env("yfinance")
    assert opened == []
    # still applied to this process
    assert os.environ["PAPER_TRADING_MODE"] == "true"
    assert os.environ["SCHWAB_API_ENABLED"] == "off"


def test_apply_mode_writes_explicit_runtime_file(monkeypatch, tmp_path):
    target = tmp_path / "runtime.env"
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    bot_routes._apply_mode_to_env("sandbox")
    text = target.read_text(encoding="utf-8")
    assert "PAPER_TRADING_MODE=true" in text
    assert "SCHWAB_SANDBOX_MODE=true" in text
    # status reads it back when the bot is not running
    assert bot_routes._get_mode_from_env_file() == "sandbox"


def test_apply_mode_preserves_other_lines(monkeypatch, tmp_path):
    target = tmp_path / "runtime.env"
    target.write_text("# comment\nLOG_LEVEL=DEBUG\nPAPER_TRADING_MODE=false\n", encoding="utf-8")
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    bot_routes._apply_mode_to_env("yfinance")
    lines = target.read_text(encoding="utf-8").splitlines()
    assert "# comment" in lines and "LOG_LEVEL=DEBUG" in lines
    assert lines.count("PAPER_TRADING_MODE=true") == 1
    assert "PAPER_TRADING_MODE=false" not in lines


def test_settings_put_in_container_reports_not_persisted(monkeypatch):
    monkeypatch.delenv("BOT_RUNTIME_ENV_FILE", raising=False)
    monkeypatch.setenv("RUNNING_IN_CONTAINER", "true")
    r = TestClient(app).put("/api/settings", json={"settings": {"LOG_LEVEL": "INFO"}}, headers=_admin())
    assert r.status_code == 200
    body = r.json()
    assert body["persisted"] is False
    assert "BOT_RUNTIME_ENV_FILE" in body.get("detail", "")


def test_settings_put_with_runtime_file_persists(monkeypatch, tmp_path):
    target = tmp_path / "runtime.env"
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    monkeypatch.setenv("LOG_LEVEL", os.environ.get("LOG_LEVEL", "INFO"))
    r = TestClient(app).put("/api/settings", json={"settings": {"LOG_LEVEL": "WARNING"}}, headers=_admin())
    assert r.status_code == 200
    assert r.json()["persisted"] is True
    assert "LOG_LEVEL=WARNING" in target.read_text(encoding="utf-8")
