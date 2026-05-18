import random
import re

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.find_note import FindNoteQuestion
from guitar_exercises.domain.notes import Note
from guitar_exercises.main import create_app
from guitar_exercises.routes import exercises as exercises_module
from guitar_exercises.routes.exercises import get_rng


@pytest.fixture
def seeded_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_rng] = lambda: random.Random(42)
    return TestClient(app)


@pytest.fixture
def pinned_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Pin to "Find G on string 5" so prompt assertions stay stable regardless
    # of RNG drift across Python versions.
    pinned = FindNoteQuestion(
        string_number=5,
        target_note=Note.G,
    )
    monkeypatch.setattr(
        exercises_module, "pick_find_note_question", lambda *_a, **_kw: pinned
    )
    return TestClient(create_app())


def test_get_find_note_returns_html_page(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/find-note")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "Find the note" in body
    assert "fretboard" in body
    assert 'id="find-note-board"' in body


def test_get_find_note_renders_prompt_and_form(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/find-note")
    body = response.text
    assert ">G<" in body
    assert ">5<" in body
    assert 'hx-post="/exercises/find-note/check"' in body
    assert 'name="string_number" value="5"' in body
    assert 'name="target_note" value="G"' in body


def test_get_find_note_renders_clickable_buttons_only_on_target_string(
    pinned_client: TestClient,
) -> None:
    response = pinned_client.get("/exercises/find-note")
    body = response.text
    # 13 fret cells (0..12) on the target string should be submit buttons.
    fret_values = re.findall(
        r'name="fret"\s+value="(\d+)"', body, flags=re.DOTALL
    )
    assert sorted(int(v) for v in fret_values) == list(range(13))


def test_post_correct_fret_returns_correct_feedback(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "G", "fret": 10},
    )
    assert response.status_code == 200
    body = response.text
    assert "Correct" in body
    assert "at fret 10" in body


def test_post_incorrect_fret_reveals_correct_frets(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "G", "fret": 3},
    )
    assert response.status_code == 200
    body = response.text
    assert "fret 3" in body
    # String 5 = A; fret 3 = C. The feedback must surface the wrong note name.
    assert "C" in body
    assert "is at fret 10" in body


def test_post_correct_fret_for_open_string_accepted(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 6, "target_note": "E", "fret": 0},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_octave_fret_accepted(seeded_client: TestClient) -> None:
    # E appears on string 6 at fret 0 AND fret 12 — both must count as correct.
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 6, "target_note": "E", "fret": 12},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_invalid_note_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "Z", "fret": 0},
    )
    assert response.status_code == 422


def test_post_out_of_range_fret_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "G", "fret": 13},
    )
    assert response.status_code == 422


def test_post_invalid_string_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 7, "target_note": "G", "fret": 3},
    )
    assert response.status_code == 422


def test_correct_feedback_includes_auto_advance_script(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "G", "fret": 10},
    )
    assert "GuitarExercises.advanceTo" in response.text


def test_correct_feedback_includes_manual_next_link_fallback(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 5, "target_note": "G", "fret": 10},
    )
    assert 'href="/exercises/find-note"' in response.text


def test_home_lists_find_note_exercise() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "/exercises/find-note" in response.text
    assert "Find the Note" in response.text
