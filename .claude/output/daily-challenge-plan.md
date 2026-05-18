# Daily Challenge + Auth — Implementation Plan

## Context

Guitar-exercises FastAPI app is currently stateless (in-memory chord YAML, no DB, no users). User wants to add a **Daily Challenge**: every day all users see the same round containing one question per exercise type (currently 4 on `main`: `chord-notes`, `chord-name`, `find-note`, `name-note`; more may follow). One attempt per user per UTC day. Track a Wordle-style streak. New exercise types must auto-join future dailies without touching the daily logic.

This requires three foundational pieces the project doesn't yet have:
1. **Persistence** — Postgres + SQLAlchemy 2.0 async + Alembic (user identity, attempts, streaks).
2. **Authentication** — Google + GitHub OAuth via Authlib + Starlette `SessionMiddleware`.
3. **Exercise registry** — small refactor of the existing 2 routes so each exercise type registers a `generate / check / template` triple that the daily-challenge engine iterates over.

End outcome: a logged-in user lands on `/daily`, plays one question per registered exercise type sequentially, gets a final score, and a streak counter that increments only when consecutive UTC days are completed.

---

## Architecture decisions

- **DB**: Postgres in `docker-compose.yml`; SQLAlchemy 2.0 async + `asyncpg`; Alembic for migrations.
- **Auth**: Authlib OAuth (`google`, `github`); session stored via Starlette `SessionMiddleware` (cookie, signed with `itsdangerous`). No JWT, no separate auth service — server-side session keyed by user id.
- **Seed**: `date.today()` in UTC, ISO-format hashed to an `int` → seeded `random.Random` instance used to pick exercise material. Same date → same questions globally.
- **Registry**: each `ExerciseType` exposes `slug`, `generate(rng) -> dict`, `check_answer(question, guess) -> bool`, `question_template`. The daily engine just enumerates `EXERCISE_REGISTRY` in fixed order.
- **Day boundary**: UTC midnight, hard-coded (no per-user TZ).
- **Sequential UX**: one question per page, HTMX-style feedback fragment (matches existing `/exercises/*/check` pattern), then "Next" link advances to next slug. After last slug → `/daily/summary`.

---

## File map

**New files**

| Path | Purpose |
|------|---------|
| `src/guitar_exercises/db/__init__.py`, `session.py` | Async engine, sessionmaker, `get_session` FastAPI dep |
| `src/guitar_exercises/db/models.py` | `User`, `DailyAttempt`, `DailyAnswer` SQLAlchemy models |
| `src/guitar_exercises/auth/__init__.py`, `oauth.py` | Authlib `OAuth` registry with Google + GitHub clients |
| `src/guitar_exercises/auth/dependencies.py` | `get_current_user` (optional) + `require_user` (raises 401/redirects) |
| `src/guitar_exercises/routes/auth.py` | `GET /auth/login/{provider}`, `GET /auth/callback/{provider}`, `POST /auth/logout` |
| `src/guitar_exercises/domain/exercise_types.py` | `ExerciseType` protocol + `EXERCISE_REGISTRY` list (chord-notes, chord-name, find-note, name-note) |
| `src/guitar_exercises/domain/daily_challenge.py` | `daily_seed(date)`, `build_daily_questions(date)`, `score_attempt(answers)`, `update_streak(user, today)` |
| `src/guitar_exercises/routes/daily.py` | Landing, per-question render + check, summary |
| `src/guitar_exercises/templates/daily/landing.html` | Pre-play state: "Start" CTA + current streak |
| `src/guitar_exercises/templates/daily/question.html` | Single question wrapper (delegates to per-type fragment) |
| `src/guitar_exercises/templates/daily/summary.html` | Score + streak update + share-text placeholder |
| `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py` | Migration scaffolding + initial schema |
| `.env.example` | `GUITAR_DATABASE_URL`, `GUITAR_SESSION_SECRET`, `GUITAR_GOOGLE_CLIENT_ID/SECRET`, `GUITAR_GITHUB_CLIENT_ID/SECRET` |
| `tests/routes/test_daily.py`, `tests/routes/test_auth.py` | Route tests with TestClient |
| `tests/domain/test_daily_challenge.py` | Seed determinism + streak logic tests |

**Modified files**

| Path | Change |
|------|--------|
| `pyproject.toml` | Add `authlib`, `httpx` (already dev — promote), `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `itsdangerous` |
| `src/guitar_exercises/main.py` | Add `SessionMiddleware`, include `auth` + `daily` routers, register lifespan that opens/closes engine |
| `src/guitar_exercises/config.py` | Add DB URL, session secret, OAuth client ids/secrets fields (all read from `GUITAR_*` env) |
| `src/guitar_exercises/routes/exercises.py` | Move generate/check logic into `EXERCISE_REGISTRY`; route handlers become thin shells that call registry |
| `src/guitar_exercises/routes/home.py` | Add "Daily Challenge" card + login/logout button using `current_user` from session |
| `src/guitar_exercises/templates/base.html` | Top-right login/logout + streak badge for logged-in users |
| `docker-compose.yml` | Add `postgres:16` service + volume, wire `GUITAR_DATABASE_URL` |
| `Makefile` (if present) | Add `make migrate`, `make db-up` |

---

## Data model

```
User
  id              uuid PK
  email           text unique not null
  name            text
  provider        text not null   -- 'google' | 'github'
  provider_sub    text not null   -- provider's user id
  current_streak  int  not null default 0
  best_streak     int  not null default 0
  last_completed  date null
  created_at      timestamptz default now()
  unique(provider, provider_sub)

DailyAttempt
  id              uuid PK
  user_id         uuid FK -> users.id
  challenge_date  date not null   -- UTC date
  completed_at    timestamptz null  -- null until last question submitted
  score           int null
  unique(user_id, challenge_date)

DailyAnswer
  id              uuid PK
  attempt_id      uuid FK -> daily_attempts.id
  exercise_slug   text not null
  question_data   jsonb not null   -- frozen snapshot of the question shown
  user_guess      text not null
  correct         bool not null
  unique(attempt_id, exercise_slug)
```

---

## Reuse from existing code

- `src/guitar_exercises/domain/chords.py` — `pick_chord(rng)`, `get_chord_by_id`, `is_correct_chord_guess` → call from `chord-notes` / `chord-name` registry entries
- `src/guitar_exercises/domain/notes.py` — `CHROMATIC`, `is_correct_guess` → call from note-recognition registry entries
- `src/guitar_exercises/domain/find_note.py` / `name_note.py` — existing fretboard-note exercise generators/checkers → wrap in `find-note` / `name-note` registry entries
- `src/guitar_exercises/domain/tuning.py` — fretboard tuning helpers used by the note exercises
- `src/guitar_exercises/domain/recent.py` — recent-chord/cookie tracking; reuse for "don't repeat yesterday's chord" if needed
- `src/guitar_exercises/rendering/chord_svg.py` (and fretboard rendering) → reuse unchanged inside daily question templates
- `src/guitar_exercises/templates/exercises/_answer_feedback.html`, `_chord_name_feedback.html`, `_find_note_feedback.html`, `_name_note_feedback.html`, `_fretboard.html`, `_string_row.html` — reused as fragments in daily-question flow
- `tests/conftest.py` `client` + `seeded_rng` fixtures → reuse; add `db_session` + `authed_client` fixtures

---

## Registry shape (concrete)

```python
# domain/exercise_types.py
class ExerciseType(Protocol):
    slug: str                       # e.g. "chord-notes"
    title: str                      # display label
    def generate(self, rng: Random) -> dict: ...      # question payload (JSON-serialisable)
    def check_answer(self, question: dict, guess: str) -> bool: ...
    question_template: str          # path under templates/

EXERCISE_REGISTRY: list[ExerciseType] = [
    ChordNotesExercise(),
    ChordNameExercise(),
    FindNoteExercise(),
    NameNoteExercise(),
]
# Adding a new type later = append one line.
```

`build_daily_questions(date)` enumerates the registry, seeds one `Random` per slug from `(date_hash, slug_hash)`, calls `generate`, returns ordered `[{slug, title, question}]`.

---

## Route plan

| Method + path | Behaviour |
|---------------|-----------|
| `GET /auth/login/{provider}` | Authlib `authorize_redirect` |
| `GET /auth/callback/{provider}` | Exchange code, upsert `User`, set `request.session["user_id"]`, redirect `/daily` |
| `POST /auth/logout` | Clear session, redirect `/` |
| `GET /daily` | Landing — show streak, "Play today" if no attempt today, "Resume" if partial, "Completed ✓" if done |
| `GET /daily/play` | Create `DailyAttempt` if missing; redirect to first unanswered question |
| `GET /daily/{slug}` | Render question for slug from today's seed; if already answered, render the prior result |
| `POST /daily/{slug}` | Validate guess, insert `DailyAnswer`, return feedback fragment with "Next" link |
| `GET /daily/summary` | Finalize attempt (set `completed_at`, `score`), apply `update_streak`, render score + streak |

All `/daily/*` use `require_user` dependency → 302 to `/auth/login/google` when anonymous.

---

## Streak rule

On first transition of an attempt to `completed_at = now()`:
```
if user.last_completed == today: no-op   # idempotent guard
elif user.last_completed == today - 1 day: current_streak += 1
else: current_streak = 1
best_streak = max(best_streak, current_streak)
last_completed = today
```

---

## Verification

1. `docker compose up -d postgres` — Postgres healthy.
2. `poetry install && poetry run alembic upgrade head` — schema created; inspect `\dt` in psql.
3. Set OAuth creds in `.env`; `make dev`; visit `/`, click "Login with Google" → consent → redirected to `/daily`. User row exists in `users`.
4. `GET /daily` shows streak 0 and "Play today".
5. Play through all questions → summary shows score and streak = 1.
6. Reload `/daily` → "Completed ✓"; `POST /daily/{slug}` for any slug returns 409 or redirect to summary.
7. **Determinism**: from a second browser/account, observe identical questions for today's date.
8. **Streak**: manually set `last_completed = today - 1` in DB, replay (after fast-forwarding system date or via a test) → streak = 2. Skip a day → streak resets to 1.
9. `poetry run pytest` — all green. New tests cover:
   - `daily_seed` returns identical payload for same date across calls
   - `update_streak` for the three branches (consecutive / gap / same-day idempotent)
   - `GET /daily` redirects unauthenticated user to OAuth login
   - `POST /daily/{slug}` rejects second attempt same day
   - Adding a stub `ExerciseType` to the registry causes it to appear in `build_daily_questions` automatically (locks in extensibility contract)
10. Confirm `GET /healthz` still returns `{"status":"ok"}` after middleware/lifespan changes.

---

## Out of scope (intentionally deferred)

- Per-user timezone day boundaries
- Shareable result string and global leaderboard
- Facebook OAuth (rejected — niche site, painful review process)
- Frontend framework migration — staying on Jinja2 + HTMX
- Anti-cheat / rate-limit beyond the per-day unique constraint
