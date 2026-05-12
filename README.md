# Guitar Exercises

A web app of structured exercises for learning the guitar fretboard.

## Concept

The fretboard is intimidating. This app delivers small, repeatable exercises that build fretboard
knowledge through practice — naming notes from chord shapes, finding all positions of a note,
recognizing intervals, and more.

Server-rendered HTML with HTMX for partial updates. No JavaScript written by us — HTMX is loaded
from a CDN.

## Exercises

### Chord Note Recognition

Displays one open-position chord (diagram + name), and asks you to name the note produced by each
string. Immediate feedback per string.

- URL: `GET /exercises/chord-notes`
- Submit a single answer: `POST /exercises/chord-notes/check` (HTMX, swaps the string row)
- Chord catalog: 23 open-position chords across five qualities (Major, minor, 7, Maj7, m7) for the
  roots A, B, C, D, E, F, G that can be played in open position
- Tuning: standard EADGBe
- Notes use sharps only for v1 (flats and enharmonic equivalents are out of scope)

> Future: hidden-chord-name mode, more exercises (interval recognition, full-fretboard note quiz),
> score tracking.

## Stack

| Layer           | Technology              |
|-----------------|-------------------------|
| Language        | Python 3.14+            |
| Framework       | FastAPI / Starlette     |
| Templates       | Jinja2                  |
| Interactivity   | HTMX 2.x (CDN)          |
| Data validation | Pydantic 2              |
| Logging         | Loguru                  |
| Tests           | Pytest + pytest-recording |
| Dependencies    | Poetry                  |

## Getting started

```bash
poetry install
poetry run uvicorn src.guitar_exercises.main:app --reload
```

Open <http://127.0.0.1:8000/exercises/chord-notes>.

> Docker Compose support is planned but not yet shipped.

## API

| Method | Path                            | Purpose                                            |
|--------|---------------------------------|----------------------------------------------------|
| GET    | `/healthz`                      | Health check, returns `{"status": "ok"}`           |
| GET    | `/exercises/chord-notes`        | Renders a random chord exercise page               |
| POST   | `/exercises/chord-notes/check`  | HTMX endpoint — validates one string's answer      |

## Development

```bash
# Run the test suite
poetry run pytest

# Run a single module
poetry run pytest tests/domain/test_notes.py
```

### Project layout

```
src/guitar_exercises/
  main.py              FastAPI app factory
  config.py            Pydantic Settings
  logging.py           Loguru intercept of uvicorn handlers
  routes/              health.py, exercises.py
  domain/              notes.py, tuning.py, chords.py (Pydantic models + catalog)
  rendering/           chord_svg.py — SVG chord-diagram renderer
  templates/           Jinja2 templates (base, chord_notes, partials)
  static/css/          app.css
tests/
  domain/              note + chord model unit tests
  rendering/           SVG renderer tests
  routes/              FastAPI TestClient integration tests
```

## License

MIT
