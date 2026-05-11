.PHONY: help install dev-up dev-down test test-unit test-integration lint format type-check clean

help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  dev-up           Start local infrastructure (Postgres + pgvector)"
	@echo "  dev-down         Stop local infrastructure"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
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
	@echo "Waiting for Postgres..."
	@sleep 3
	@echo "Infrastructure ready."

dev-down:
	docker compose -f docker/docker-compose.yml down

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
