import random

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.main import create_app
from guitar_exercises.routes.exercises import get_rng


@pytest.fixture
def seeded_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_rng] = lambda: random.Random(42)
    return TestClient(app)


def test_get_chord_notes_returns_html_page(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-notes")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<svg" in body
    assert "</svg>" in body
    for string_number in range(1, 7):
        assert f'id="string-{string_number}"' in body


def test_get_chord_notes_includes_chord_name(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-notes")
    assert response.status_code == 200
    body = response.text
    assert "<h1" in body
    assert "Name the notes" in body


def test_get_chord_notes_renders_answer_form_for_non_muted_strings(
    seeded_client: TestClient,
) -> None:
    response = seeded_client.get("/exercises/chord-notes")
    body = response.text
    assert 'hx-post="/exercises/chord-notes/check"' in body
    assert 'name="chord_id"' in body
    assert 'name="string_number"' in body
    assert 'name="guess"' in body


def test_post_check_correct_guess_returns_correct_feedback(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={"chord_id": "a_major", "string_number": 5, "guess": "A"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text
    assert 'id="string-5"' in response.text


def test_post_check_incorrect_guess_reveals_expected_note(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={"chord_id": "a_major", "string_number": 4, "guess": "C"},
    )
    assert response.status_code == 200
    assert "the note is E" in response.text


def test_post_check_unknown_chord_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={"chord_id": "unknown", "string_number": 1, "guess": "A"},
    )
    assert response.status_code == 404


def test_post_check_muted_string_returns_400(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={"chord_id": "a_major", "string_number": 6, "guess": "E"},
    )
    assert response.status_code == 400
