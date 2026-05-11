"""Smoke tests for configuration and logging.

These tests verify the scaffolding works end-to-end. If these pass,
the foundation is solid enough to build on.
"""

from triage.config import Settings, get_settings
from triage.logging import get_logger


def test_settings_loads() -> None:
    """Settings should load with valid defaults."""
    settings = get_settings()
    assert settings.env in ("dev", "test", "prod")
    assert settings.postgres_db == "triage"


def test_database_url_constructed() -> None:
    """Database URL should be assembled correctly from components."""
    settings = Settings(
        postgres_user="testuser",
        postgres_password="testpass",  # type: ignore[arg-type]
        postgres_host="testhost",
        postgres_port=1234,
        postgres_db="testdb",
    )
    expected = "postgresql+psycopg://testuser:testpass@testhost:1234/testdb"
    assert settings.database_url == expected


def test_logger_works() -> None:
    """Logger should be obtainable and callable without errors."""
    logger = get_logger("test")
    logger.info("smoke test", value=42, status="ok")
