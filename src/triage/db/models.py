"""SQLAlchemy ORM models.

Design principles:
- Use natural keys (HPO IDs, Orphanet IDs) where they're stable and global.
- Arrays for bounded, write-mostly fields (synonyms, inheritance modes).
- Join tables with metadata for many-to-many with attributes (disease_phenotypes).
- JSONB for flexible/sparse attributes that don't justify dedicated columns.
- All timestamps are timezone-aware UTC.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Uses the modern SQLAlchemy 2.0 typed mapping style.
    """

    type_annotation_map: ClassVar[dict[Any, Any]] = {
        dict[str, Any]: JSONB,
        list[str]: ARRAY(String),
    }


# ---------------------------------------------------------------------------
# HPO (Human Phenotype Ontology)
# ---------------------------------------------------------------------------


class HpoTerm(Base):
    """A phenotype term from the HPO.

    Primary key is the HPO ID itself (e.g., 'HP:0001324').
    """

    __tablename__ = "hpo_terms"

    hpo_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list[str]] = mapped_column(default=list, server_default="{}")
    is_obsolete: Mapped[bool] = mapped_column(default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    disease_links: Mapped[list[DiseasePhenotype]] = relationship(
        back_populates="phenotype", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Trigram index for fuzzy matching on phenotype names.
        Index(
            "ix_hpo_terms_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<HpoTerm({self.hpo_id}: {self.name})>"


class HpoRelationship(Base):
    """Parent-child relationships in the HPO graph (is_a, part_of, etc)."""

    __tablename__ = "hpo_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_hpo_id: Mapped[str] = mapped_column(
        ForeignKey("hpo_terms.hpo_id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_hpo_id: Mapped[str] = mapped_column(
        ForeignKey("hpo_terms.hpo_id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="is_a", server_default="is_a"
    )

    __table_args__ = (
        Index(
            "ix_hpo_rel_unique", "child_hpo_id", "parent_hpo_id", "relationship_type", unique=True
        ),
    )


# ---------------------------------------------------------------------------
# Diseases (Orphanet primary source)
# ---------------------------------------------------------------------------


class Disease(Base):
    """A rare disease from Orphanet.

    Primary key is the Orphanet ID (e.g., 'ORPHA:558').
    """

    __tablename__ = "diseases"

    orphanet_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list[str]] = mapped_column(default=list, server_default="{}")
    inheritance_modes: Mapped[list[str]] = mapped_column(default=list, server_default="{}")
    # Prevalence has multiple structured fields per Orphanet schema, keep as JSONB.
    prevalence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_obsolete: Mapped[bool] = mapped_column(default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    phenotype_links: Mapped[list[DiseasePhenotype]] = relationship(
        back_populates="disease", cascade="all, delete-orphan"
    )
    external_refs: Mapped[list[DiseaseExternalRef]] = relationship(
        back_populates="disease", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_diseases_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Disease({self.orphanet_id}: {self.name})>"


class DiseasePhenotype(Base):
    """Many-to-many link between diseases and phenotypes, with frequency."""

    __tablename__ = "disease_phenotypes"

    id: Mapped[int] = mapped_column(primary_key=True)
    disease_id: Mapped[str] = mapped_column(
        ForeignKey("diseases.orphanet_id", ondelete="CASCADE"), nullable=False, index=True
    )
    hpo_id: Mapped[str] = mapped_column(
        ForeignKey("hpo_terms.hpo_id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Orphanet frequency labels: 'Obligate', 'Very frequent', 'Frequent',
    # 'Occasional', 'Very rare', 'Excluded'.
    frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Numeric frequency midpoint for ranking (0.0-1.0). Derived during ingestion.
    frequency_numeric: Mapped[float | None] = mapped_column(nullable=True)

    disease: Mapped[Disease] = relationship(back_populates="phenotype_links")
    phenotype: Mapped[HpoTerm] = relationship(back_populates="disease_links")

    __table_args__ = (Index("ix_disease_pheno_unique", "disease_id", "hpo_id", unique=True),)


class DiseaseExternalRef(Base):
    """Cross-references from Orphanet diseases to OMIM, ICD-10, MeSH, etc."""

    __tablename__ = "disease_external_refs"

    id: Mapped[int] = mapped_column(primary_key=True)
    disease_id: Mapped[str] = mapped_column(
        ForeignKey("diseases.orphanet_id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # 'OMIM', 'ICD10', etc.
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    disease: Mapped[Disease] = relationship(back_populates="external_refs")

    __table_args__ = (
        Index("ix_disease_extref_unique", "disease_id", "source", "external_id", unique=True),
        Index("ix_disease_extref_lookup", "source", "external_id"),
    )


# ---------------------------------------------------------------------------
# Cases (stub for later weeks)
# ---------------------------------------------------------------------------


class Case(Base):
    """De-identified clinical case submitted to the system.

    Populated starting Week 7 when we wire up the agent flow. Stubbed here
    so the schema is forward-compatible from the start.
    """

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_phenotypes: Mapped[list[str]] = mapped_column(default=list, server_default="{}")
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
