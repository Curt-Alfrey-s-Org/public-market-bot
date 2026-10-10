"""
Security review 2026-09-25, finding 10: no built-in default login accounts.

The web (/api/auth) and mobile (/api/v1/auth) env-credential loaders used to
ship admin/admin123 and user/user123 whenever the env did not override them.
An env account now exists only when both *_USERNAME and *_PASSWORD are set.
"""

import pytest

import api.routes.auth as web_auth
import api.routes.v1.auth as v1_auth

_ALL_ENV_ACCOUNT_VARS = (
    "ADMIN_USERNAME", "ADMIN_PASSWORD", "DIRECTOR_USERNAME", "DIRECTOR_PASSWORD",
    "USER_USERNAME", "USER_PASSWORD",
)


@pytest.fixture()
def no_env_accounts(monkeypatch):
    for name in _ALL_ENV_ACCOUNT_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(web_auth, "_ENV_USERS", {})
    monkeypatch.setattr(v1_auth, "_ENV_USERS", {})
    return monkeypatch


@pytest.mark.security
@pytest.mark.parametrize("module", [web_auth, v1_auth])
@pytest.mark.parametrize("username,password", [("admin", "admin123"), ("user", "user123")])
def test_old_default_accounts_do_not_log_in(no_env_accounts, module, username, password):
    ok, role = module._check_env_password(username, password)
    assert ok is False and role == ""


@pytest.mark.security
@pytest.mark.parametrize("module", [web_auth, v1_auth])
def test_env_account_requires_both_variables(no_env_accounts, module):
    no_env_accounts.setenv("ADMIN_USERNAME", "ops-admin")
    module._load_env_users()
    assert module._check_env_password("ops-admin", "") == (False, "")
    no_env_accounts.setenv("ADMIN_PASSWORD", "pytest-only-Passw0rd!")
    module._load_env_users()
    assert module._check_env_password("ops-admin", "pytest-only-Passw0rd!") == (True, "admin")
    assert module._check_env_password("ops-admin", "wrong") == (False, "")
    assert module._check_env_password("admin", "admin123") == (False, "")
