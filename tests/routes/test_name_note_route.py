import random
import re

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.name_note import NameNoteQuestion
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
    # Pin to "fret 5 on string 6" → A. Stable across RNG changes.
    pinned = NameNoteQuestion(
        string_number=6,
        fret=5,
        expected_note=Note.A,
    )
    monkeypatch.setattr(exercises_module, "pick_name_note_question", lambda *_a, **_kw: pinned)
    return TestClient(create_app())


def test_get_name_note_returns_html_page(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/name-note")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "Name the note" in body
    assert "fretboard" in body
    assert 'id="name-note-board"' in body


def test_get_name_note_renders_prompt_with_pinned_values(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/name-note")
    body = response.text
    # Prompt mentions string 6 and fret 5.
    assert ">5<" in body
    assert ">6<" in body
    # Hidden form inputs encode the question.
    assert 'name="string_number" value="6"' in body
    assert 'name="fret" value="5"' in body


def test_get_name_note_renders_full_chromatic_chip_group(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/name-note")
    body = response.text
    chip_values = re.findall(r'name="guess"\s+value="([^"]+)"', body, flags=re.DOTALL)
    # The chip widget must offer all 12 chromatic notes exactly once.
    assert sorted(chip_values) == sorted(n.value for n in Note)


def test_get_name_note_highlights_target_fret_only(pinned_client: TestClient) -> None:
    # Only the highlighted (6, 5) cell carries the fretboard-cell-highlight
    # class — otherwise the visual cue is meaningless.
    response = pinned_client.get("/exercises/name-note")
    body = response.text
    assert body.count("fretboard-cell-highlight") == 1


def test_post_correct_guess_returns_correct_feedback(pinned_client: TestClient) -> None:
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A"},
    )
    assert response.status_code == 200
    body = response.text
    assert "Correct" in body
    assert "A" in body


def test_post_correct_guess_includes_auto_advance(pinned_client: TestClient) -> None:
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A"},
    )
    assert "GuitarExercises.advanceTo" in response.text


def test_post_correct_guess_includes_manual_next_link_fallback(
    pinned_client: TestClient,
) -> None:
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A"},
    )
    assert 'href="/exercises/name-note"' in response.text


def test_post_incorrect_guess_reveals_expected_note(pinned_client: TestClient) -> None:
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "C"},
    )
    assert response.status_code == 200
    body = response.text
    assert "the note is A" in body


def test_post_incorrect_guess_arms_key_advance(pinned_client: TestClient) -> None:
    # Keyboard players must be able to move on with Enter/Space without a
    # mouse click — the failure feedback carries a data attribute that the
    # shared auto-advance.js picks up after the htmx swap.
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "C"},
    )
    body = response.text
    assert 'data-key-advance="/exercises/name-note"' in body


def test_post_check_normalizes_sharp_input(pinned_client: TestClient) -> None:
    # Fret 6 on string 6 is A# — accept the unicode sharp glyph.
    response = pinned_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 6, "guess": "A♯"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_check_out_of_range_fret_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/name-note/check",
        data={"string_number": 5, "fret": 13, "guess": "A"},
    )
    assert response.status_code == 422


def test_post_check_invalid_string_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/name-note/check",
        data={"string_number": 0, "fret": 5, "guess": "A"},
    )
    assert response.status_code == 422


def test_post_check_guess_longer_than_two_characters_returns_422(
    seeded_client: TestClient,
) -> None:
    response = seeded_client.post(
        "/exercises/name-note/check",
        data={"string_number": 5, "fret": 2, "guess": "AAAA"},
    )
    assert response.status_code == 422


def test_home_lists_name_note_exercise() -> None:
    response = TestClient(create_app()).get("/")
    assert response.status_code == 200
    assert "/exercises/name-note" in response.text
    assert "Name the Note" in response.text
