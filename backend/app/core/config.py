"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "ZT Suite API"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./zt_suite.db"

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:5173"]

    # JWT Configuration
    secret_key: str = "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_cookie_name: str = "refresh_token"
    refresh_token_cookie_secure: bool = False
    refresh_token_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # MFA Configuration
    mfa_issuer_name: str = "ZT Suite"
    trusted_device_expire_days: int = 30
    trusted_device_cookie_name: str = "trusted_device_token"
    trusted_device_cookie_secure: bool = False
    trusted_device_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # First Admin (created on startup if no users exist)
    first_admin_email: str = "admin@example.com"
    first_admin_password: str = "changeme123"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
