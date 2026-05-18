"""Cross-exercise tests for the no-repeat-question cookie behaviour.

Every exercise must:
- write its recent-questions cookie on each GET,
- avoid repeating a question while one slot still fits in the window,
- keep its history independent from the other exercises' histories.
"""

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.chords import CHORDS
from guitar_exercises.domain.find_note import MAX_FRET
from guitar_exercises.domain.notes import CHROMATIC
from guitar_exercises.domain.recent import RECENT_WINDOW
from guitar_exercises.domain.tuning import STANDARD_TUNING
from guitar_exercises.main import create_app
from guitar_exercises.routes.exercises import (
    RECENT_COOKIE_CHORD_NAME,
    RECENT_COOKIE_CHORD_NOTES,
    RECENT_COOKIE_FIND_NOTE,
    RECENT_COOKIE_NAME_NOTE,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# (path, cookie name, pool size) — each tuple drives the per-exercise checks.
EXERCISES = [
    ("/exercises/chord-notes", RECENT_COOKIE_CHORD_NOTES, len(CHORDS)),
    ("/exercises/chord-name", RECENT_COOKIE_CHORD_NAME, len(CHORDS)),
    ("/exercises/find-note", RECENT_COOKIE_FIND_NOTE, len(STANDARD_TUNING) * len(CHROMATIC)),
    ("/exercises/name-note", RECENT_COOKIE_NAME_NOTE, len(STANDARD_TUNING) * (MAX_FRET + 1)),
]


@pytest.mark.parametrize(("path", "cookie", "_pool"), EXERCISES)
def test_get_sets_recent_cookie(client: TestClient, path: str, cookie: str, _pool: int) -> None:
    response = client.get(path)
    assert response.status_code == 200
    value = response.cookies.get(cookie)
    assert value is not None and value != ""


@pytest.mark.parametrize(("path", "cookie", "pool"), EXERCISES)
def test_no_repeat_within_window(client: TestClient, path: str, cookie: str, pool: int) -> None:
    # Hit the endpoint up to ``min(pool, RECENT_WINDOW)`` times. While the
    # window can still hold every key, no question may repeat.
    rounds = min(pool, RECENT_WINDOW)
    seen: list[str] = []
    for _ in range(rounds):
        response = client.get(path)
        assert response.status_code == 200
        value = client.cookies.get(cookie, "")
        seen.append(value.split(",")[0])
    assert len(set(seen)) == rounds, f"{path} repeated a question: {seen}"


@pytest.mark.parametrize(("path", "cookie", "_pool"), EXERCISES)
def test_cookie_trims_to_window(client: TestClient, path: str, cookie: str, _pool: int) -> None:
    for _ in range(RECENT_WINDOW + 3):
        response = client.get(path)
        assert response.status_code == 200
    stored = client.cookies.get(cookie, "")
    assert 0 < len(stored.split(",")) <= RECENT_WINDOW


def test_each_exercise_uses_an_independent_cookie(client: TestClient) -> None:
    # Visiting one exercise must not populate another exercise's history.
    expected_cookies = {
        RECENT_COOKIE_CHORD_NOTES,
        RECENT_COOKIE_CHORD_NAME,
        RECENT_COOKIE_FIND_NOTE,
        RECENT_COOKIE_NAME_NOTE,
    }
    for path, cookie, _ in EXERCISES:
        client.cookies.clear()
        client.get(path)
        present = {c for c in expected_cookies if client.cookies.get(c) is not None}
        assert present == {cookie}, f"{path} should only set {cookie}, got {present}"
