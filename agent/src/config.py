"""Agent configuration settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the traffic capture agent.

    Settings are loaded from environment variables or a .env file.
    Environment variables are prefixed with ZT_AGENT_ (e.g., ZT_AGENT_INTERFACE).
    """

    model_config = SettingsConfigDict(
        env_prefix="ZT_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Network capture settings
    interface: str | None = None
    """Network interface to capture on. None = all interfaces."""

    target_ip: str | None = None
    """Filter traffic to/from this IP only (e.g., host IP). None = capture all traffic."""

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    """Logging level for agent logs (output to stderr)."""

    # Output settings
    output_mode: Literal["stdout", "file", "none"] = "file"
    """Where to output captured traffic records."""

    output_file: str = "./traffic.jsonl"
    """File path for traffic records when output_mode=file."""

    batch_interval: int = 60
    """Interval in seconds to batch traffic records before output."""


# Global settings instance - loaded once at module import
settings = Settings()
