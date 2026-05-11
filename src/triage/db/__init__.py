"""Database access layer.

Exports the SQLAlchemy engine, session factory, and base model class.
All database access in the rest of the codebase should go through here.
"""

from triage.db.engine import engine, get_session
from triage.db.models import Base

__all__ = ["Base", "engine", "get_session"]
