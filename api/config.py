"""
Configuration management using Pydantic v2 BaseSettings.
Validates required environment variables at startup.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable validation."""
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL connection string")
    postgres_db: str = Field(default="marketbot", description="PostgreSQL database name")
    postgres_user: str = Field(default="marketbot_user", description="PostgreSQL username")
    postgres_password: str = Field(..., description="PostgreSQL password")
    
    # API Security
    # BOT_API_KEY: server-to-server/scripts only (X-API-Key). It must never be
    # built into the frontend; browsers authenticate with the user's JWT, and
    # admin-only control endpoints ignore the API key entirely.
    bot_api_key: str = Field(..., description="Bot API key for server-to-server authentication")
    # Deprecated and unused: the frontend no longer ships an API key.
    vite_api_key: str = Field(default="", description="Deprecated; ignored (frontend uses the user's JWT)")
    
    # Schwab Integration
    schwab_client_id: str = Field(default="", description="Schwab OAuth client ID")
    schwab_client_secret: str = Field(default="", description="Schwab OAuth client secret")
    schwab_sandbox_mode: bool = Field(default=True, description="Use Schwab sandbox environment")
    paper_trading_mode: bool = Field(default=True, description="Enable paper trading mode")
    
    # Credentials
    admin_username: str = Field(default="admin", description="Admin username")
    admin_password: str = Field(..., description="Admin password")
    director_username: str = Field(default="director", description="Director username")
    director_password: str = Field(..., description="Director password")
    user_username: str = Field(default="user", description="User username")
    user_password: str = Field(..., description="User password")
    
    # Database Connection Pooling
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Connection timeout in seconds")
    db_pool_recycle: int = Field(default=3600, description="Recycle connections after N seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Optional Services
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    
    # SettingsConfigDict per pydantic v2 (class-based Config is deprecated:
    # https://docs.pydantic.dev/
    # extra="ignore": the shared .env also feeds docker-compose and bot
    # subsystems, so it contains keys that are not Settings fields
    # (https://docs.pydantic.dev/
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.vite_api_key:
            import warnings
            warnings.warn(
                "VITE_API_KEY is deprecated and ignored: the frontend authenticates with the "
                "logged-in user's JWT. Remove VITE_API_KEY from your environment.",
                RuntimeWarning
            )


# Load settings from environment
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
    print("\nPlease ensure all required environment variables are set in .env file:", file=sys.stderr)
    print("  - DATABASE_URL", file=sys.stderr)
    print("  - POSTGRES_PASSWORD", file=sys.stderr)
    print("  - BOT_API_KEY", file=sys.stderr)
    print("  - ADMIN_PASSWORD", file=sys.stderr)
    print("  - DIRECTOR_PASSWORD", file=sys.stderr)
    print("  - USER_PASSWORD", file=sys.stderr)
    print("  - JWT_SECRET (required in production; see api/security_config.py)", file=sys.stderr)
    sys.exit(1)
