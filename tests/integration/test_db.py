"""Integration tests for the database layer.

Requires Postgres running locally (make dev-up).
Run only these: pytest -v -m integration
"""

import pytest
from sqlalchemy import text

from triage.db import engine, get_session
from triage.db.models import Disease, DiseasePhenotype, HpoTerm

pytestmark = pytest.mark.integration


def test_database_reachable() -> None:
    """We can connect to Postgres and execute a query."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_pgvector_installed() -> None:
    """The pgvector extension is installed."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        assert result.scalar() == "vector"


def test_pg_trgm_installed() -> None:
    """The pg_trgm extension is installed."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'"))
        assert result.scalar() == "pg_trgm"


def test_tables_exist() -> None:
    """All expected tables exist after migration."""
    expected = {
        "hpo_terms",
        "hpo_relationships",
        "diseases",
        "disease_phenotypes",
        "disease_external_refs",
        "cases",
        "alembic_version",
    }
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        actual = {row[0] for row in result}
    missing = expected - actual
    assert not missing, f"Missing tables: {missing}"


def test_insert_and_query_phenotype() -> None:
    """End-to-end ORM round-trip: insert, query, delete."""
    session_gen = get_session()
    session = next(session_gen)
    try:
        term = HpoTerm(
            hpo_id="HP:TEST001",
            name="Test phenotype",
            definition="A made-up phenotype for testing.",
            synonyms=["test alias 1", "test alias 2"],
        )
        session.add(term)
        session.commit()

        fetched = session.query(HpoTerm).filter_by(hpo_id="HP:TEST001").first()
        assert fetched is not None
        assert fetched.name == "Test phenotype"
        assert "test alias 1" in fetched.synonyms

        session.delete(fetched)
        session.commit()
    finally:
        session.close()


def test_disease_phenotype_relationship() -> None:
    """Many-to-many disease ↔ phenotype with frequency works."""
    session_gen = get_session()
    session = next(session_gen)
    try:
        term = HpoTerm(hpo_id="HP:TEST002", name="Weakness")
        disease = Disease(orphanet_id="ORPHA:TEST", name="Test syndrome")
        link = DiseasePhenotype(
            disease_id="ORPHA:TEST",
            hpo_id="HP:TEST002",
            frequency="Very frequent",
            frequency_numeric=0.8,
        )
        session.add_all([term, disease, link])
        session.commit()

        fetched = session.query(Disease).filter_by(orphanet_id="ORPHA:TEST").first()
        assert fetched is not None
        assert len(fetched.phenotype_links) == 1
        assert fetched.phenotype_links[0].phenotype.name == "Weakness"

        # Cascade delete: removing the disease should remove the link.
        session.delete(fetched)
        session.delete(term)
        session.commit()
    finally:
        session.close()
