"""
Password Hashing Tests: pwdlib argon2 + legacy bcrypt migration
================================================================
Covers the passlib -> pwdlib[argon2] migration (docs/ROADMAP.md, P0):
- New hashes are argon2 (current scheme per FastAPI security tutorial)
- Legacy bcrypt hashes (created under passlib) keep verifying
- verify_and_update semantics: valid bcrypt hash returns an argon2 re-hash
- verify_db_user_password persists the re-hash (transparent migration on login)
"""

import bcrypt
import pytest

from api.auth import (
    _verify_password,
    hash_password,
    verify_and_update_password,
    verify_db_user_password,
)

PASSWORD = "change-me"
WRONG_PASSWORD = "change-me"


def _legacy_bcrypt_hash(password: str) -> str:
    """Hash like passlib's bcrypt scheme did (raw bcrypt, $2b$ prefix)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class TestNewHashes:
    """New hashes use argon2 and verify."""

    def test_hash_password_produces_argon2(self):
        hashed = hash_password(PASSWORD)
        assert hashed.startswith("$argon2id$")

    def test_new_hash_verifies(self):
        hashed = hash_password(PASSWORD)
        assert _verify_password(PASSWORD, hashed) is True

    def test_new_hash_rejects_wrong_password(self):
        hashed = hash_password(PASSWORD)
        assert _verify_password(WRONG_PASSWORD, hashed) is False

    def test_argon2_hash_needs_no_update(self):
        hashed = hash_password(PASSWORD)
        valid, updated = verify_and_update_password(PASSWORD, hashed)
        assert valid is True
        assert updated is None


class TestLegacyBcryptHashes:
    """Legacy bcrypt hashes keep verifying and trigger a re-hash."""

    def test_legacy_bcrypt_hash_verifies(self):
        legacy = _legacy_bcrypt_hash(PASSWORD)
        assert _verify_password(PASSWORD, legacy) is True

    def test_legacy_bcrypt_hash_rejects_wrong_password(self):
        legacy = _legacy_bcrypt_hash(PASSWORD)
        assert _verify_password(WRONG_PASSWORD, legacy) is False

    def test_verify_and_update_rehashes_bcrypt_to_argon2(self):
        legacy = _legacy_bcrypt_hash(PASSWORD)
        valid, updated = verify_and_update_password(PASSWORD, legacy)
        assert valid is True
        assert updated is not None
        assert updated.startswith("$argon2id$")
        # The re-hash itself verifies and needs no further update
        valid2, updated2 = verify_and_update_password(PASSWORD, updated)
        assert valid2 is True
        assert updated2 is None

    def test_verify_and_update_wrong_password_no_rehash(self):
        legacy = _legacy_bcrypt_hash(PASSWORD)
        valid, updated = verify_and_update_password(WRONG_PASSWORD, legacy)
        assert valid is False
        assert updated is None


class TestMalformedInput:
    """Malformed/empty hashes fail closed without raising."""

    @pytest.mark.parametrize("hashed", ["", "not-a-hash", "$unknown$abc"])
    def test_verify_malformed_hash_returns_false(self, hashed):
        assert _verify_password(PASSWORD, hashed) is False

    @pytest.mark.parametrize("hashed", ["", "not-a-hash", "$unknown$abc"])
    def test_verify_and_update_malformed_hash(self, hashed):
        assert verify_and_update_password(PASSWORD, hashed) == (False, None)

    def test_empty_password_returns_false(self):
        hashed = hash_password(PASSWORD)
        assert _verify_password("", hashed) is False
        assert verify_and_update_password("", hashed) == (False, None)


class _FakeUser:
    def __init__(self, password_hash: str):
        self.username = "rehash-user"
        self.password_hash = password_hash


class _FakeSession:
    def __init__(self):
        self.committed = 0
        self.rolled_back = 0

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1


class TestVerifyDbUserPassword:
    """Re-hash path: verify_db_user_password persists the argon2 re-hash."""

    def test_legacy_hash_persisted_as_argon2_on_login(self):
        user = _FakeUser(_legacy_bcrypt_hash(PASSWORD))
        db = _FakeSession()
        assert verify_db_user_password(db, user, PASSWORD) is True
        assert user.password_hash.startswith("$argon2id$")
        assert db.committed == 1
        # Subsequent login verifies against the new hash without another commit
        assert verify_db_user_password(db, user, PASSWORD) is True
        assert db.committed == 1

    def test_wrong_password_does_not_rehash(self):
        legacy = _legacy_bcrypt_hash(PASSWORD)
        user = _FakeUser(legacy)
        db = _FakeSession()
        assert verify_db_user_password(db, user, WRONG_PASSWORD) is False
        assert user.password_hash == legacy
        assert db.committed == 0

    def test_argon2_hash_no_commit(self):
        user = _FakeUser(hash_password(PASSWORD))
        db = _FakeSession()
        assert verify_db_user_password(db, user, PASSWORD) is True
        assert db.committed == 0
