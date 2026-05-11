.PHONY: help install dev-up dev-down dev-logs db-shell db-migrate db-revision test test-unit test-integration lint format type-check clean

help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  dev-up           Start local infrastructure (Postgres + pgvector)"
	@echo "  dev-down         Stop local infrastructure"
	@echo "  dev-logs         Tail Postgres logs"
	@echo "  db-shell         Open psql shell into the running DB"
	@echo "  db-migrate       Apply pending migrations"
	@echo "  db-revision      Generate a new migration from model changes"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests (requires DB)"
	@echo "  lint             Run ruff linter"
	@echo "  format           Format code with ruff"
	@echo "  type-check       Run mypy"
	@echo "  clean            Remove build artifacts"

install:
	uv venv --python 3.11
	uv pip install -e ".[dev]"
	python -m spacy download en_core_web_lg
	pre-commit install

dev-up:
	docker compose -f docker/docker-compose.yml up -d
	@echo "Waiting for Postgres to be healthy..."
	@until docker exec triage_postgres pg_isready -U triage -d triage > /dev/null 2>&1; do sleep 1; done
	@echo "Infrastructure ready."

dev-down:
	docker compose -f docker/docker-compose.yml down

dev-logs:
	docker compose -f docker/docker-compose.yml logs -f postgres

db-shell:
	docker exec -it triage_postgres psql -U triage -d triage

db-migrate:
	alembic upgrade head

db-revision:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

test:
	pytest -v

test-unit:
	pytest -v -m "not integration"

test-integration:
	pytest -v -m integration

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

type-check:
	mypy src

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -exec rm -rf {} +
