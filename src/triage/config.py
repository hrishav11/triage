"""Centralized configuration with environment variable support."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Values can be overridden via environment variables or a .env file.
    Secrets use SecretStr to prevent accidental logging.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: Literal["dev", "test", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    raw_data_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    processed_data_dir: Path = Field(default_factory=lambda: Path("data/processed"))

    # Database
    postgres_user: str = "triage"
    postgres_password: SecretStr = SecretStr("triage_dev")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "triage"

    # External APIs (added in later weeks)
    pubmed_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    @property
    def database_url(self) -> str:
        """Construct the SQLAlchemy database URL."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton.

    Using lru_cache ensures we don't re-parse the .env file on every call.
    """
    return Settings()
