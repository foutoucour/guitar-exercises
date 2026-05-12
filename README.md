# Guitar Exercises

A web service exposing exercises to learn the guitar fretboard.

## Concept

The fretboard is intimidating. This API delivers structured, repeatable exercises to build fretboard knowledge through
practice — knowing which note is where, finding all positions of a note, recognizing intervals, and more.

Exercises are exposed as a REST API. Frontend TBD — no JavaScript, ever.

## Exercises

> Exercises will be documented here as they are implemented.

## Stack

| Layer           | Technology     |
|-----------------|----------------|
| Language        | Python 3.14+   |
| Framework       | FastAPI        |
| Data validation | Pydantic       |
| Logging         | Loguru         |
| Dev environment | Docker Compose |
| Tests           | Pytest         |
| Dependencies    | Poetry         |

## Getting started

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up
```

API available at `http://localhost:8000`.

### Local dev

```bash
poetry install
poetry run uvicorn src.guitar_exercises.main:app --reload
```

## API

Health check:

```
GET /healthz
```

Exercise endpoints:

```
GET /v1/exercises
```

> Full API reference will be added once endpoints are implemented.

## Development

```bash
# Run tests
poetry run pytest
```

## License

MIT
