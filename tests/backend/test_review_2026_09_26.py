"""
Review 2026-09-26 regression tests.

- DELETE /api/users/{username} must work when foreign keys are enforced
  (Postgres always enforces them; SQLite only with PRAGMA foreign_keys=ON).
- The legacy /api/auth/login used by the web GUI is rate limited.
- Settings values containing line breaks are never written to the env file.

Every value here is generated per test; nothing touches a real .env or DB.
"""

import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.models  # noqa: F401  (registers all models)
import api.routes.settings as settings_routes
from api.auth import create_access_token
from api.main import app
from api.models.audit import AuditLog
from api.models.auth_token import EmailVerificationToken
from api.models.backup_code import BackupCode
from api.models.user import User
from api.utils.timeutils import utcnow
from database import Base, get_db


def _admin():
    return {"Authorization": f"Bearer {create_access_token('admin', subject='pytest-admin')}"}


@pytest.fixture()
def fk_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    try:
        yield Session
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_delete_registered_user_with_fk_rows(fk_db):
    db = fk_db()
    user = User(username="pytest-del", email="operator@example.com",
                password_hash="x", role="user", email_verified=False)
    db.add(user)
    db.flush()
    db.add(EmailVerificationToken(token=secrets.token_urlsafe(16), user_id=user.id,
                                  expires_at=utcnow(), used=False))
    db.add(BackupCode(user_id=user.id, code_hash="pytest-not-a-secret", used=False))
    db.add(AuditLog(user_id=user.id, event_type="register", success=True))
    db.commit()
    uid = user.id
    db.close()

    r = TestClient(app).delete("/api/users/pytest-del", headers=_admin())
    assert r.status_code == 200, r.text

    db = fk_db()
    try:
        assert db.query(User).filter_by(username="pytest-del").first() is None
        assert db.query(EmailVerificationToken).filter_by(user_id=uid).count() == 0
        assert db.query(BackupCode).filter_by(user_id=uid).count() == 0
        # audit history is kept, detached from the deleted user
        assert db.query(AuditLog).filter_by(event_type="register").count() == 1
        assert db.query(AuditLog).filter_by(user_id=uid).count() == 0
    finally:
        db.close()


def test_legacy_login_is_rate_limited():
    c = TestClient(app)
    body = {"username": "nobody-" + secrets.token_hex(4), "password": secrets.token_hex(8)}
    codes = [c.post("/api/auth/login", json=body).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10  # failed logins answer 200 with success=false
    assert codes[10] == 429


def test_env_file_refuses_line_breaks(monkeypatch, tmp_path):
    target = tmp_path / "runtime.env"
    target.write_text("DEBUG=false\n", encoding="utf-8")
    monkeypatch.setenv("BOT_RUNTIME_ENV_FILE", str(target))
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    settings_routes._update_env_file({"DEBUG": "true\nJWT_SECRET=injected", "LOG_LEVEL": "WARNING"})
    text = target.read_text(encoding="utf-8")
    assert "JWT_SECRET" not in text
    assert "DEBUG=false" in text
    assert "LOG_LEVEL=WARNING" in text
