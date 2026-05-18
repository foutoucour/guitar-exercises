.PHONY: help install run dev test test-watch lint format check clean

APP := guitar_exercises.main:app
HOST ?= 127.0.0.1
PORT ?= 8000

help:
	@echo "Targets:"
	@echo "  install     Install dependencies (poetry install)"
	@echo "  run         Run server locally (no reload)"
	@echo "  dev         Run dev server with reload"
	@echo "  test        Run pytest"
	@echo "  test-watch  Re-run pytest on file changes"
	@echo "  lint        Ruff lint"
	@echo "  format      Ruff format + auto-fix"
	@echo "  check       Run pre-commit hooks on all files"
	@echo "  clean       Remove caches and build artifacts"

install:
	poetry install

run:
	poetry run uvicorn $(APP) --host $(HOST) --port $(PORT)

dev:
	poetry run uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

test:
	poetry run pytest

test-watch:
	poetry run pytest --looponfail

lint:
	poetry run ruff check src tests

format:
	poetry run ruff format src tests
	poetry run ruff check --fix src tests

check:
	poetry run pre-commit run --all-files

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	rm -rf dist build *.egg-info
