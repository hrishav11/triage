-- Enable pgvector for dense embedding storage and similarity search.
-- Runs once on first container startup (when the volume is empty).
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable trigram matching for fuzzy text search on phenotype/disease names.
-- Useful when clinicians type "myasthenia" and we need to match "Myasthenia Gravis".
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gin for compound indexes mixing scalars and arrays.
-- Needed later for indexing phenotype arrays on diseases.
CREATE EXTENSION IF NOT EXISTS btree_gin;
