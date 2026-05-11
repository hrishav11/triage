# Triage

Clinical evidence synthesis platform for rare disease diagnosis. Decision support, not diagnosis.

## Status

🚧 Week 1 of 12. Building foundation.

## Quick Start

```bash
git clone <your-repo-url>
cd triage
cp .env.example .env
make install
make test
```

## Architecture

Multi-agent RAG system for rare disease differential diagnosis. Full architecture doc coming Week 2.

**Key design principles:**
- Decision support, not diagnosis
- Every claim traces to a source (citation provenance)
- Explicit abstention when evidence is thin (calibration > confidence)
- No PHI without de-identification

## Development

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make lint` | Lint code with ruff |
| `make format` | Auto-format code |
| `make type-check` | Run mypy strict type checking |
| `make dev-up` | Start Postgres locally (Stage 2+) |
| `make dev-down` | Stop local infrastructure |

## Data Sources

All public. No PHI processed without de-identification.

- **HPO** — Human Phenotype Ontology
- **Orphanet** — Rare disease catalog
- **ClinVar** — Variant-disease associations
- **PubMed Open Access** — Biomedical literature
- **bioRxiv / medRxiv** — Preprints

## License

MIT (project code). Data sources retain their original licenses.
