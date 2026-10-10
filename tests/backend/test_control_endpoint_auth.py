"""
Security review 2026-09-25, finding 8: control endpoints require an admin JWT.

Covers bot start/stop/shutdown, /api/bot/mode, pending-trade approve/reject and
settings writes being refused for:
  - anonymous requests (no credentials),
  - the backend API key alone (what the frontend bundle used to ship),
  - "guest" requests (client-sent X-User-Role: guest, or a token whose role is guest),
  - spoofed role headers (X-User-Role: admin) without / with a non-admin token,
  - tokens signed with the old public default JWT secret.

Every bot/trade side effect is replaced by a recording stub, so these tests can
never start the bot, change the trading mode, or approve a trade.
"""

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

import api.routes.bot as bot_routes
import api.routes.pending_trades as pending_routes
import api.routes.v1.bot as v1_bot_routes
from api.auth import ALGORITHM, create_access_token
from api.main import BOT_API_KEY, app
from api.utils.timeutils import utcnow as _utcnow

OLD_PUBLIC_DEFAULT_SECRET = "change-me"

CONTROL_REQUESTS = [
    ("post", "/api/bot/start", {"mode": "yfinance"}),
    ("post", "/api/bot/stop", None),
    ("post", "/api/bot/shutdown", None),
    ("post", "/api/bot/mode", {"mode": "live"}),
    ("post", "/api/pending-trades/approve", {"trade_id": "t-1"}),
    ("post", "/api/pending-trades/reject", {"trade_id": "t-1"}),
    ("put", "/api/settings", {"settings": {"MAX_POSITIONS": "5"}}),
    ("put", "/api/settings/ml-filter", {"enabled": False}),
]


class _Recorder:
    def __init__(self):
        self.calls = []

    def stub(self, name, result=None):
        def _fn(*args, **kwargs):
            self.calls.append(name)
            return result
        return _fn


class _FakeBot:
    """Stands in for TradingBot; records approve/reject instead of trading."""

    def __init__(self, recorder):
        self._rec = recorder

    def approve_pending_trade(self, trade_id):
        self._rec.calls.append("approve_pending_trade")
        return {"status": "ok"}

    def reject_pending_trade(self, trade_id, reason=None):
        self._rec.calls.append("reject_pending_trade")
        return {"status": "ok"}


@pytest.fixture()
def recorder(monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr(bot_routes, "start_bot", rec.stub("start_bot", True))
    monkeypatch.setattr(bot_routes, "stop_bot", rec.stub("stop_bot", True))
    monkeypatch.setattr(bot_routes, "shutdown_bot", rec.stub("shutdown_bot", True))
    monkeypatch.setattr(bot_routes, "is_bot_running", lambda: False)
    monkeypatch.setattr(bot_routes, "get_bot_instance", lambda: None)
    monkeypatch.setattr(bot_routes, "_apply_mode_to_env", rec.stub("_apply_mode_to_env"))
    monkeypatch.setattr(pending_routes, "get_bot_instance", lambda: _FakeBot(rec))
    return rec


def _call(client, method, path, body, headers=None):
    fn = getattr(client, method)
    if body is None:
        return fn(path, headers=headers or {})
    return fn(path, json=body, headers=headers or {})


def _token(role, secret=None):
    if secret is None:
        return create_access_token(role, subject=f"pytest-{role}")
    payload = {"sub": f"pytest-{role}", "role": role, "iat": _utcnow(), "exp": _utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_anonymous_request_refused(client, recorder, method, path, body):
    r = _call(client, method, path, body)
    assert r.status_code == 401
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_api_key_alone_cannot_drive_control_endpoints(client, recorder, method, path, body):
    r = _call(client, method, path, body, {"X-API-Key": BOT_API_KEY})
    assert r.status_code in (401, 403)
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_guest_header_without_session_refused(client, recorder, method, path, body):
    r = _call(client, method, path, body, {"X-User-Role": "guest"})
    assert r.status_code == 401
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_guest_role_token_refused(client, recorder, method, path, body):
    from api.auth import SECRET_KEY

    r = _call(client, method, path, body, {"Authorization": f"Bearer {_token('guest', SECRET_KEY)}"})
    assert r.status_code == 401
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_spoofed_admin_header_without_session_refused(client, recorder, method, path, body):
    r = _call(client, method, path, body, {"X-User-Role": "admin"})
    assert r.status_code == 401
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("role", ["user", "director"])
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_spoofed_admin_header_with_non_admin_token_refused(client, recorder, role, method, path, body):
    headers = {"Authorization": f"Bearer {_token(role)}", "X-User-Role": "admin", "X-API-Key": BOT_API_KEY}
    r = _call(client, method, path, body, headers)
    assert r.status_code == 403
    assert recorder.calls == []


@pytest.mark.security
@pytest.mark.parametrize("method,path,body", CONTROL_REQUESTS)
def test_token_signed_with_old_public_default_secret_refused(client, recorder, method, path, body):
    forged = _token("admin", OLD_PUBLIC_DEFAULT_SECRET)
    r = _call(client, method, path, body, {"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401
    assert recorder.calls == []


CONTROL_ROUTES = [
    ("api.routes.bot", "/start"), ("api.routes.bot", "/stop"), ("api.routes.bot", "/shutdown"),
    ("api.routes.bot", "/shutdown-server"), ("api.routes.bot", "/mode"),
    ("api.routes.pending_trades", "/approve"), ("api.routes.pending_trades", "/reject"),
    ("api.routes.settings", ""), ("api.routes.settings", "/ml-filter"),
    ("api.routes.trades", "/reset"), ("api.routes.network", "/network/access"),
    ("api.routes.system", "/run-tests"),
]


@pytest.mark.security
@pytest.mark.parametrize("module_name,path", CONTROL_ROUTES)
def test_control_routes_declare_require_admin(module_name, path):
    """Static check (no request is sent): every control route depends on require_admin.

    /api/bot/shutdown-server is only checked this way, because calling it would
    exit the test process if the dependency were ever removed.
    """
    import importlib

    from api.auth import require_admin

    def _deps(dependant):
        for d in dependant.dependencies:
            yield d.call
            yield from _deps(d)

    router = importlib.import_module(module_name).router
    routes = [
        r for r in router.routes
        if getattr(r, "path", None) == path and ({"POST", "PUT"} & set(getattr(r, "methods", None) or ()))
    ]
    assert routes, f"route not found: {module_name} {path!r}"
    for r in routes:
        assert require_admin in set(_deps(r.dependant)), f"{module_name} {path!r} is missing Depends(require_admin)"


@pytest.mark.security
def test_anonymous_read_endpoint_refused(client):
    assert client.get("/api/bot/status").status_code == 401


@pytest.mark.security
def test_health_and_login_stay_open(client):
    assert client.get("/api/health").status_code != 401
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
    assert r.status_code == 200
    assert r.json()["success"] is False


@pytest.mark.security
def test_user_session_can_read_and_role_header_is_ignored(client, recorder):
    headers = {"Authorization": f"Bearer {_token('user')}", "X-User-Role": "guest"}
    assert client.get("/api/bot/status", headers=headers).status_code == 200


@pytest.mark.security
def test_admin_session_passes_auth_on_control_endpoints(client, recorder):
    headers = {"Authorization": f"Bearer {_token('admin')}"}
    # Bot reported as not running -> handler returns without calling stop_bot.
    r = client.post("/api/bot/stop", headers=headers)
    assert r.status_code == 200
    # Approve reaches the (fake) bot only with an admin session.
    r = client.post("/api/pending-trades/approve", json={"trade_id": "t-1"}, headers=headers)
    assert r.status_code == 200
    assert recorder.calls == ["approve_pending_trade"]


V1_TEST_USER = "pytest-v1-user"
V1_TEST_USER_PASSWORD = "change-me"  # test fixture only


@pytest.fixture()
def v1_user_token(client):
    """JWT for a DB-backed, email-verified account with role 'user' (not admin)."""
    from api.auth import hash_password
    from api.models.user import User
    from database import SessionLocal

    db = SessionLocal()
    try:
        if not db.query(User).filter_by(username=V1_TEST_USER).first():
            db.add(User(
                username=V1_TEST_USER,
                email=f"{V1_TEST_USER}@pytest.local",
                password_hash=hash_password(V1_TEST_USER_PASSWORD),
                role="user",
                email_verified=True,
                is_active=True,
            ))
            db.commit()
    finally:
        db.close()
    r = client.post("/api/v1/auth/login", json={"username": V1_TEST_USER, "password": V1_TEST_USER_PASSWORD})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.mark.security
@pytest.mark.parametrize("path", ["/api/v1/bot/start", "/api/v1/bot/stop"])
def test_v1_bot_control_refused_for_non_admin_user(client, monkeypatch, v1_user_token, path):
    rec = _Recorder()
    monkeypatch.setattr(v1_bot_routes, "start_bot", rec.stub("start_bot", True))
    monkeypatch.setattr(v1_bot_routes, "stop_bot", rec.stub("stop_bot", True))
    monkeypatch.setattr(v1_bot_routes, "is_bot_running", lambda: path.endswith("/stop"))
    r = client.post(path, headers={"Authorization": f"Bearer {v1_user_token}", "X-User-Role": "admin"})
    assert r.status_code == 403
    assert rec.calls == []


@pytest.mark.security
@pytest.mark.parametrize("path", ["/api/v1/bot/start", "/api/v1/bot/stop"])
def test_v1_bot_control_refused_anonymous(client, monkeypatch, path):
    rec = _Recorder()
    monkeypatch.setattr(v1_bot_routes, "start_bot", rec.stub("start_bot", True))
    monkeypatch.setattr(v1_bot_routes, "stop_bot", rec.stub("stop_bot", True))
    r = client.post(path, headers={"X-User-Role": "admin"})
    assert r.status_code == 401
    assert rec.calls == []
