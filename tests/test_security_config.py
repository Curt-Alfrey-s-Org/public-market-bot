"""
Security review 2026-09-25, findings 9 and 10 (unit tests, no database needed).

- JWT secret: required in production, public placeholders refused, throwaway
  secret only outside production (api/security_config.py).
- LiteLLM brain config: startup error names the missing variable
  (api/services/litellm_client.py, api/bot_manager.py). start_bot() is only
  exercised on the refusal path, before any bot is created.
"""

import pytest

from api import security_config


@pytest.fixture()
def clean_env(monkeypatch):
    for name in ("ENVIRONMENT", "APP_ENV", "JWT_SECRET", "JWT_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.mark.security
@pytest.mark.parametrize("value,expected", [("", True), ("production", True), ("staging", True),
                                            ("development", False), ("dev", False), ("test", False), ("local", False)])
def test_is_production_defaults_to_secure(clean_env, value, expected):
    if value:
        clean_env.setenv("ENVIRONMENT", value)
    assert security_config.is_production() is expected


@pytest.mark.security
def test_missing_jwt_secret_fails_fast_in_production(clean_env):
    clean_env.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        security_config.resolve_jwt_secret()


@pytest.mark.security
def test_missing_jwt_secret_fails_when_environment_unset(clean_env):
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        security_config.resolve_jwt_secret()


@pytest.mark.security
@pytest.mark.parametrize("placeholder", ["market-bot-change-in-production", "your-secret-key-change-in-production"])
def test_public_placeholder_secret_refused_in_production(clean_env, placeholder):
    clean_env.setenv("ENVIRONMENT", "production")
    clean_env.setenv("JWT_SECRET", placeholder)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        security_config.resolve_jwt_secret()


@pytest.mark.security
def test_configured_secret_is_used(clean_env):
    clean_env.setenv("ENVIRONMENT", "production")
    clean_env.setenv("JWT_SECRET", "x" * 48)
    assert security_config.resolve_jwt_secret() == "x" * 48


@pytest.mark.security
def test_legacy_jwt_secret_key_alias_is_used(clean_env):
    clean_env.setenv("ENVIRONMENT", "production")
    clean_env.setenv("JWT_SECRET_KEY", "y" * 48)
    assert security_config.resolve_jwt_secret() == "y" * 48


@pytest.mark.security
def test_non_production_without_secret_gets_random_throwaway(clean_env):
    clean_env.setenv("ENVIRONMENT", "development")
    a = security_config.resolve_jwt_secret()
    b = security_config.resolve_jwt_secret()
    assert a and b and a != b
    assert a not in ("market-bot-change-in-production", "your-secret-key-change-in-production")


# ---------------------------------------------------------------------------
# Finding 9: LiteLLM / BOT_REQUIRE_BRAIN startup error names the variable
# ---------------------------------------------------------------------------

@pytest.fixture()
def litellm_env(monkeypatch):
    for name in ("LITELLM_ENABLED", "LITELLM_API_KEY", "BOT_REQUIRE_BRAIN"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_litellm_missing_config_names_variables(litellm_env):
    from api.services.litellm_client import litellm_missing_config

    assert litellm_missing_config() == ["LITELLM_ENABLED", "LITELLM_API_KEY"]
    litellm_env.setenv("LITELLM_ENABLED", "true")
    assert litellm_missing_config() == ["LITELLM_API_KEY"]
    litellm_env.setenv("LITELLM_API_KEY", "test-placeholder-key")
    assert litellm_missing_config() == []


def test_brain_config_error_names_missing_variable(litellm_env):
    from api.bot_manager import brain_config_error

    litellm_env.setenv("BOT_REQUIRE_BRAIN", "true")
    litellm_env.setenv("LITELLM_ENABLED", "true")
    msg = brain_config_error()
    assert msg and "LITELLM_API_KEY" in msg and "BOT_REQUIRE_BRAIN" in msg
    litellm_env.delenv("LITELLM_ENABLED")
    assert "LITELLM_ENABLED" in brain_config_error()


def test_brain_config_error_none_when_brain_not_required(litellm_env):
    from api.bot_manager import brain_config_error

    litellm_env.setenv("BOT_REQUIRE_BRAIN", "false")
    assert brain_config_error() is None


def test_start_bot_refuses_with_named_variable_before_creating_bot(litellm_env):
    import api.bot_manager as bm

    litellm_env.setenv("BOT_REQUIRE_BRAIN", "true")
    litellm_env.setenv("LITELLM_ENABLED", "true")

    def _must_not_run():
        raise AssertionError("bot must not be initialised when the brain is not configured")

    litellm_env.setattr(bm, "initialize_bot_from_main", _must_not_run)
    litellm_env.setattr(bm, "_brain_status", lambda: _must_not_run())
    with pytest.raises(bm.BrainUnavailableError, match="LITELLM_API_KEY"):
        bm.start_bot()
    assert "LITELLM_API_KEY" in (bm.get_last_start_error() or "")


def test_jwt_secret_single_read_path_warns_on_conflicting_names(clean_env, caplog):
    """Review 2026-09-25 (low): JWT_SECRET / JWT_SECRET_KEY must not silently disagree."""
    clean_env.setenv("JWT_SECRET", "a" * 48)
    clean_env.setenv("JWT_SECRET_KEY", "b" * 48)
    with caplog.at_level("WARNING", logger="api.security_config"):
        assert security_config.resolve_jwt_secret() == "a" * 48
    assert any("JWT_SECRET_KEY" in rec.getMessage() for rec in caplog.records)


def test_jwt_secret_same_value_under_both_names_is_quiet(clean_env, caplog):
    clean_env.setenv("JWT_SECRET", "c" * 48)
    clean_env.setenv("JWT_SECRET_KEY", "c" * 48)
    with caplog.at_level("WARNING", logger="api.security_config"):
        assert security_config.resolve_jwt_secret() == "c" * 48
    assert not any("different values" in rec.getMessage() for rec in caplog.records)
