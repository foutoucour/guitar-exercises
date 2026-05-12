# Guitar Exercises — Project Instructions

## Stack

- Python 3.14+
- FastAPI / Starlette
- Pydantic (structured data and request/response models)
- Loguru (logging)
- Pytest + pytest-recording (tests)
- Poetry (dependency management)
- Docker Compose (dev environment)

**No JavaScript.** Frontend TBD — likely HTMX + Jinja2 or a pure-Python UI framework.

## Target viewport

- Primary target: 15" laptop (~1440×900 viewport, content area ~1200px wide).
- Optimise UI density for this size: prefer multi-column layouts that use horizontal space; avoid oversized typography, padding, or vertical scrolling that wastes the width.
- The dev/run command is `make run` (no-reload) or `make dev` (reload). After every code change, run tests via `make test` or `poetry run pytest`.

## Python conventions

- Use poetry to manage dependencies; pin with `">=x.y.z,<x+1"` version ranges
- Use Pydantic for all structured data (models, request/response schemas)
- Use loguru for all logging; use f-strings in log calls: `logger.info(f"Session {session_id} started")`
- Use async everywhere it makes sense (route handlers, I/O-bound operations)
- Use type hints throughout
- No global variables — use FastAPI dependency injection
- Keep functions short; split if a function grows too long

## Testing

- `poetry run pytest` — run from project root
- Use pytest-recording to avoid real network calls in tests
- Use FastAPI TestClient for API integration tests
- TDD: write a failing test first, then make it pass

## Always run tests

After every code change:

```bash
poetry run pytest
```

## Build & Test commands

```bash
poetry install          # install dependencies
poetry run uvicorn src.guitar_exercises.main:app --reload  # dev server
poetry run pytest       # tests
docker compose up       # full dev environment
```
