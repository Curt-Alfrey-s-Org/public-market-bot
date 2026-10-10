"""
Security review 2026-09-25 follow-up: GET /api/network/access/forbid and
/allow change the outbound firewall, so like POST /api/network/access they need
an ADMIN JWT. The firewall helper is replaced by a recorder, so no iptables
command can run.
"""

import pytest
from fastapi.testclient import TestClient

import api.routes.network as network_routes
from api.auth import create_access_token
from api.main import BOT_API_KEY, app


class _FakeControl:
    def __init__(self):
        self.calls = []

    def set_internet_access(self, allowed):
        self.calls.append(allowed)
        return {"allowed": allowed, "allowed_str": "ALLOWED" if allowed else "FORBIDDEN", "updated_at": "t"}

    def get_internet_access(self):
        return {"allowed": True, "allowed_str": "ALLOWED", "updated_at": "t"}


@pytest.fixture()
def fake(monkeypatch):
    f = _FakeControl()
    monkeypatch.setattr(network_routes, "internet_control", f)
    return f


def _auth(role):
    return {"Authorization": f"Bearer {create_access_token(role, subject=f'pytest-{role}')}"}


@pytest.mark.security
@pytest.mark.parametrize("path", ["/api/network/access/forbid", "/api/network/access/allow"])
def test_firewall_toggle_refuses_anonymous(fake, path):
    assert TestClient(app).get(path).status_code == 401
    assert fake.calls == []


@pytest.mark.security
@pytest.mark.parametrize("path", ["/api/network/access/forbid", "/api/network/access/allow"])
def test_firewall_toggle_refuses_api_key_alone(fake, path):
    assert TestClient(app).get(path, headers={"X-API-Key": BOT_API_KEY}).status_code in (401, 403)
    assert fake.calls == []


@pytest.mark.security
@pytest.mark.parametrize("role", ["user", "director"])
@pytest.mark.parametrize("path", ["/api/network/access/forbid", "/api/network/access/allow"])
def test_firewall_toggle_refuses_non_admin(fake, path, role):
    headers = {**_auth(role), "X-User-Role": "admin"}
    assert TestClient(app).get(path, headers=headers).status_code == 403
    assert fake.calls == []


@pytest.mark.security
def test_admin_can_toggle_and_anyone_logged_in_can_read(fake):
    client = TestClient(app)
    assert client.get("/api/network/access/forbid", headers=_auth("admin")).status_code == 200
    assert client.get("/api/network/access/allow", headers=_auth("admin")).status_code == 200
    assert fake.calls == [False, True]
    assert client.get("/api/network/access", headers=_auth("user")).status_code == 200
