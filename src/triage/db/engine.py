"""SQLAlchemy engine and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from triage.config import get_settings
from triage.logging import get_logger

logger = get_logger(__name__)


def _make_engine() -> Engine:
    """Create the SQLAlchemy engine with sensible pool settings."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        echo=False,  # set True to log every SQL statement (very noisy)
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # validates connections before use, handles stale conns
        pool_recycle=3600,  # recycle connections every hour
    )
    logger.info("database engine created", host=settings.postgres_host, db=settings.postgres_db)
    return engine


# Module-level singletons. SQLAlchemy engines are thread-safe and should be
# shared across the entire application.
engine: Engine = _make_engine()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and ensure it's closed.

    Usage:
        with get_session() as session:
            session.query(...)

    Designed to be FastAPI-compatible for dependency injection in later weeks.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
