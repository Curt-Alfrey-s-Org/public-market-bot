"""
Phase 2-E Tests: Config Endpoint Expansion
============================================
Verify feature flags, maintenance mode, version checks, and configuration.
"""

import pytest
from fastapi.testclient import TestClient
import os

from api.main import app, BOT_API_KEY

# All /api/* routes except health and /api/auth require X-API-Key (RequireApiKeyMiddleware)
client = TestClient(app, headers={"X-API-Key": BOT_API_KEY})


class TestConfigEndpoint:
    """Test GET /api/v1/config endpoint."""
    
    def test_config_endpoint_exists(self):
        """Test config endpoint is accessible."""
        response = client.get("/api/v1/config")
        
        # Should return 200 (no auth required)
        assert response.status_code == 200
    
    def test_config_response_structure(self):
        """Test config response has required fields."""
        response = client.get("/api/v1/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "apiVersion" in data
        assert "minAppVersion" in data
        assert "maintenanceMode" in data
        assert "features" in data
        assert "limits" in data
        assert "environment" in data


class TestFeatureFlags:
    """Test feature flags in config."""
    
    def test_feature_flags_structure(self):
        """Test features field has correct structure."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        features = data["features"]
        
        # Verify known features
        assert isinstance(features, dict)
        assert "live_trading" in features
        assert "advanced_orders" in features
        assert "ai_signals" in features
        assert "paper_trading" in features
        
        # All values should be booleans
        for feature, enabled in features.items():
            assert isinstance(enabled, bool)
    
    def test_default_feature_flags(self):
        """Test default feature flag values."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        features = data["features"]
        
        # Default values (from environment or hardcoded)
        assert features["paper_trading"] == True
        assert features["ai_signals"] == True
        assert features["live_trading"] == False  # Beta
        assert features["advanced_orders"] == False  # Beta


class TestVersionChecks:
    """Test version checking fields."""
    
    def test_min_app_version_format(self):
        """Test minAppVersion has valid format."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        version = data["minAppVersion"]
        
        # Should be semantic versioning
        assert isinstance(version, str)
        assert version.count(".") >= 2  # X.Y.Z
        
        # Parse version
        parts = version.split(".")
        assert len(parts) >= 3
        assert all(part.isdigit() or part[0].isdigit() for part in parts)
    
    def test_api_version_field(self):
        """Test apiVersion field."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        api_version = data["apiVersion"]
        
        assert isinstance(api_version, str)
        assert api_version == "v1"


class TestMaintenanceMode:
    """Test maintenance mode functionality."""
    
    def test_maintenance_mode_field_exists(self):
        """Test maintenanceMode field exists."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        assert "maintenanceMode" in data
        assert isinstance(data["maintenanceMode"], bool)
    
    def test_maintenance_message_when_enabled(self):
        """Test maintenance message is configurable."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        # maintenanceMessage should be None or string
        msg = data.get("maintenanceMessage")
        assert msg is None or isinstance(msg, str)


class TestLimitsConfiguration:
    """Test trading limits in config."""
    
    def test_limits_structure(self):
        """Test limits field has correct structure."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        limits = data["limits"]
        
        # Verify required fields
        assert "max_positions" in limits
        assert "max_trades_per_day" in limits
        assert "min_account_value" in limits
    
    def test_limits_are_integers(self):
        """Test limit values are integers."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        limits = data["limits"]
        
        assert isinstance(limits["max_positions"], int)
        assert isinstance(limits["max_trades_per_day"], int)
        assert isinstance(limits["min_account_value"], int)
    
    def test_limits_have_reasonable_values(self):
        """Test limit values are reasonable."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        limits = data["limits"]
        
        # Sanity checks
        assert limits["max_positions"] > 0
        assert limits["max_trades_per_day"] > 0
        assert limits["min_account_value"] >= 0


class TestEnvironmentField:
    """Test environment field."""
    
    def test_environment_value(self):
        """Test environment field is valid."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        env = data["environment"]
        
        # Should be one of these values
        assert env in ("production", "staging", "development")


class TestMobileIntegration:
    """Test config responds to mobile app use cases."""
    
    def test_app_launch_scenario(self):
        """
        Test typical mobile app launch scenario:
        1. Get config
        2. Check maintenance mode
        3. Check version
        4. Check feature flags
        """
        response = client.get("/api/v1/config")
        assert response.status_code == 200
        config = response.json()
        
        # Simulate mobile app checks
        # Check 1: Is app in maintenance?
        if config["maintenanceMode"]:
            msg = config.get("maintenanceMessage", "Maintenance in progress")
            assert isinstance(msg, (str, type(None)))
        
        # Check 2: Does app version meet minimum?
        min_version = config["minAppVersion"]
        assert isinstance(min_version, str)
        
        # Check 3: Are features enabled?
        for feature, enabled in config["features"].items():
            assert isinstance(enabled, bool)
    
    def test_feature_flag_disable_ui_elements(self):
        """
        Test config correctly disables UI elements.
        Mobile app uses features dict like:
        - if not config.features.live_trading: hide_live_trading_button()
        """
        response = client.get("/api/v1/config")
        config = response.json()
        
        # Example: live_trading is disabled by default
        assert config["features"]["live_trading"] == False


class TestConfigCacheability:
    """Test config endpoint response can be cached."""
    
    def test_config_response_is_consistent(self):
        """Test multiple calls to config return same values."""
        response1 = client.get("/api/v1/config")
        response2 = client.get("/api/v1/config")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Should be identical
        assert data1 == data2
    
    def test_config_has_no_time_dependent_fields(self):
        """Test config doesn't have timestamp (allows caching)."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        # Should not have timestamp (unlike error responses)
        assert "timestamp" not in data


class TestEnvironmentVariableIntegration:
    """Test config respects environment variables."""
    
    def test_min_app_version_from_env(self):
        """Test MIN_APP_VERSION env var is respected."""
        # Get current config
        response = client.get("/api/v1/config")
        data = response.json()
        
        min_version = data["minAppVersion"]
        env_version = os.getenv("MIN_APP_VERSION", "1.0.0")
        
        # Should match env var (or default)
        assert min_version == env_version
    
    def test_environment_from_env(self):
        """Test ENVIRONMENT env var is respected."""
        response = client.get("/api/v1/config")
        data = response.json()
        
        env = data["environment"]
        env_setting = os.getenv("ENVIRONMENT", "production").lower()
        
        # Should match (or default to production)
        assert env == env_setting


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
