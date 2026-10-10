"""
Backend test fixtures.

In the container the FastAPI lifespan creates/migrates tables at startup.
Module-level TestClient(app) (used across these tests) does not run lifespan
events, so create the schema explicitly in the test database
(DATABASE_URL must point at a scratch DB — never the live Postgres).
"""

import os
import secrets

import pytest

# ---------------------------------------------------------------------------
# Test-process environment (set before any test module imports api.main).
# - JWT_SECRET: per-run throwaway value; the app has no public default any more
#   and refuses to start in production without one.
# - Env login accounts: the app no longer ships built-in admin/user default
#   passwords, so the fixture accounts the existing tests log in with are
#   provided here, for this pytest process only. They are not app defaults.
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))
TEST_ENV_ADMIN_USERNAME = "admin"
TEST_ENV_ADMIN_PASSWORD = "change-me"  # test fixture only
TEST_ENV_USER_USERNAME = "user"
TEST_ENV_USER_PASSWORD = "user123"  # test fixture only
os.environ["ADMIN_USERNAME"] = TEST_ENV_ADMIN_USERNAME
os.environ["ADMIN_PASSWORD"] = TEST_ENV_ADMIN_PASSWORD
os.environ["USER_USERNAME"] = TEST_ENV_USER_USERNAME
os.environ["USER_PASSWORD"] = TEST_ENV_USER_PASSWORD

# DB-backed test account: /api/v1 protected endpoints resolve the token `sub`
# to a users-table row (api/dependencies/auth.py), so env-credential logins
# (hash(username) sub) cannot access them. Tests must use a real DB user.
TEST_DB_ADMIN_USERNAME = "pytest-v1-admin"
TEST_DB_ADMIN_PASSWORD = "change-me"


@pytest.fixture(scope="session", autouse=True)
def _create_db_schema():
    """Create all ORM tables once per test session and seed the DB test admin."""
    import api.models  # noqa: F401  (registers all models on Base.metadata)
    from api.auth import hash_password
    from api.models.user import User
    from database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if not db.query(User).filter_by(username=TEST_DB_ADMIN_USERNAME).first():
            db.add(User(
                username=TEST_DB_ADMIN_USERNAME,
                email=f"{TEST_DB_ADMIN_USERNAME}@pytest.local",
                password_hash=hash_password(TEST_DB_ADMIN_PASSWORD),
                role="admin",
                email_verified=True,
                is_active=True,
            ))
            db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def db_admin_token():
    """JWT for the DB-backed test admin (required for protected /api/v1 endpoints)."""
    from fastapi.testclient import TestClient
    from api.main import app, BOT_API_KEY

    c = TestClient(app, headers={"X-API-Key": BOT_API_KEY})
    response = c.post(
        "/api/v1/auth/login",
        json={"username": TEST_DB_ADMIN_USERNAME, "password": TEST_DB_ADMIN_PASSWORD},
    )
    return response.json()["access_token"] if response.status_code == 200 else None


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset slowapi's in-memory limiter so rate-limit tests don't starve later tests."""
    from api.middleware.rate_limit import limiter

    limiter.reset()
    yield
