"""
Review 2026-09-25 follow-up: POST /api/assets/upload writes files (up to 100 MB
each) into the served assets folder, so it needs an ADMIN JWT. Uploads go to a
pytest tmp dir, never the real assets folder.
"""

import pytest
from fastapi.testclient import TestClient

import api.routes.assets as assets_routes
from api.auth import create_access_token
from api.main import BOT_API_KEY, app

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest.fixture()
def uploads_dir(tmp_path, monkeypatch):
    d = tmp_path / "uploads"
    monkeypatch.setattr(assets_routes, "UPLOADS_DIR", d)
    return d


def _auth(role):
    return {"Authorization": f"Bearer {create_access_token(role, subject=f'pytest-{role}')}"}


def _files():
    return {"files": ("pic.png", _PNG, "image/png")}


def _written(d):
    return list(d.glob("*")) if d.exists() else []


@pytest.mark.security
def test_upload_refuses_anonymous(uploads_dir):
    assert TestClient(app).post("/api/assets/upload", files=_files()).status_code == 401
    assert _written(uploads_dir) == []


@pytest.mark.security
def test_upload_refuses_api_key_alone(uploads_dir):
    r = TestClient(app).post("/api/assets/upload", files=_files(), headers={"X-API-Key": BOT_API_KEY})
    assert r.status_code in (401, 403)
    assert _written(uploads_dir) == []


@pytest.mark.security
@pytest.mark.parametrize("role", ["user", "director"])
def test_upload_refuses_non_admin(uploads_dir, role):
    headers = {**_auth(role), "X-User-Role": "admin"}
    r = TestClient(app).post("/api/assets/upload", files=_files(), headers=headers)
    assert r.status_code == 403
    assert _written(uploads_dir) == []


@pytest.mark.security
def test_admin_can_upload_and_user_can_list(uploads_dir):
    client = TestClient(app)
    r = client.post("/api/assets/upload", files=_files(), headers=_auth("admin"))
    assert r.status_code == 200
    urls = r.json()["urls"]
    assert len(urls) == 1 and urls[0].startswith("/assets/uploads/pic_")
    assert len(_written(uploads_dir)) == 1
    assert client.get("/api/assets", headers=_auth("user")).status_code == 200
