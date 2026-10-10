"""
Security review 2026-09-25 follow-up: GET /api/settings must not return
third-party API keys (Schwab, Hugging Face, Alpha Vantage, News API, Finnhub)
to logged-in users. Configured keys come back as a fixed mask, unset keys as "".
The mask echoed back by the GUI on save must never be stored as a key.

All values below are fake, generated per test; no real credential is used.
"""

import secrets

import pytest
from fastapi.testclient import TestClient

import api.routes.settings as settings_routes
from api.auth import create_access_token
from api.main import app
from api.routes.settings import MASKED_SECRET_VALUE, SECRET_SETTING_KEYS


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def fake_keys(monkeypatch, tmp_path):
    """Set every secret key to a random fake value, via the environment only."""
    # Keep the settings routes away from any real .env on disk.
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(tmp_path / "runtime.env"))
    values = {}
    for key in SECRET_SETTING_KEYS:
        values[key] = "fake-" + secrets.token_hex(12)
        monkeypatch.setenv(key, values[key])
    return values


def _auth(role):
    return {"Authorization": f"Bearer {create_access_token(role, subject=f'pytest-{role}')}"}


@pytest.mark.security
@pytest.mark.parametrize("role", ["user", "director", "admin"])
def test_get_settings_masks_api_keys_for_every_role(client, fake_keys, role):
    r = client.get("/api/settings", headers=_auth(role))
    assert r.status_code == 200
    body = r.json()
    for key, real in fake_keys.items():
        assert body[key] == MASKED_SECRET_VALUE
        assert real not in r.text


@pytest.mark.security
def test_get_settings_reports_unset_keys_as_empty(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(tmp_path / "runtime.env"))
    for key in SECRET_SETTING_KEYS:
        monkeypatch.delenv(key, raising=False)
    r = client.get("/api/settings", headers=_auth("user"))
    assert r.status_code == 200
    for key in SECRET_SETTING_KEYS:
        assert r.json()[key] == ""


@pytest.mark.security
def test_get_settings_masks_keys_read_from_runtime_env_file(client, monkeypatch, tmp_path):
    env_file = tmp_path / "runtime.env"
    fake = "fake-" + secrets.token_hex(12)
    env_file.write_text(f"FINNHUB_API_KEY={fake}\n", encoding="utf-8")
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(env_file))
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    r = client.get("/api/settings", headers=_auth("user"))
    assert r.status_code == 200
    assert r.json()["FINNHUB_API_KEY"] == MASKED_SECRET_VALUE
    assert fake not in r.text


@pytest.mark.security
def test_put_settings_never_stores_or_echoes_keys(client, fake_keys, monkeypatch, tmp_path):
    env_file = tmp_path / "runtime.env"
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(env_file))
    monkeypatch.setenv("LOG_LEVEL", "INFO")  # restored after the test (PUT updates os.environ)
    new_fake = "fake-" + secrets.token_hex(12)
    payload = {"settings": {
        "LOG_LEVEL": "INFO",
        "SCHWAB_APP_KEY": MASKED_SECRET_VALUE,   # what the GUI echoes back
        "NEWS_API_KEY": new_fake,
    }}
    r = client.put("/api/settings", json=payload, headers=_auth("admin"))
    assert r.status_code == 200
    body = r.json()
    assert "SCHWAB_APP_KEY" not in body["settings"]
    assert body["settings"]["NEWS_API_KEY"] == MASKED_SECRET_VALUE
    assert new_fake not in r.text
    stored = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "LOG_LEVEL=INFO" in stored
    assert MASKED_SECRET_VALUE not in stored
    assert new_fake not in stored
    for real in fake_keys.values():
        assert real not in stored


def test_mask_helper():
    assert settings_routes._mask_secret("") == ""
    assert settings_routes._mask_secret(None) == ""
    assert settings_routes._mask_secret("anything") == MASKED_SECRET_VALUE
