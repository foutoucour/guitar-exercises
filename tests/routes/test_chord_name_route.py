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


# With seed 42, pick_chord returns g_major / "G major" — locked-in fixture.
SEEDED_CHORD_ID = "g_major"
SEEDED_CHORD_NAME = "G major"


def test_get_chord_name_returns_html_page(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-name")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<svg" in body
    assert "</svg>" in body


def test_get_chord_name_does_not_leak_chord_display_name(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-name")
    body = response.text

    # The display name "G major" must not appear anywhere on the page —
    # not in the heading, not in the SVG <title>/<desc>, not in alt text.
    assert SEEDED_CHORD_NAME not in body
    # The hidden form field still carries the slug id so /check can find it.
    assert f'value="{SEEDED_CHORD_ID}"' in body


def test_get_chord_name_renders_guess_form(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-name")
    body = response.text
    assert 'hx-post="/exercises/chord-name/check"' in body
    assert 'name="chord_id"' in body
    assert 'name="guess"' in body
    assert 'type="text"' in body


def test_get_chord_name_prompts_user_to_name_the_chord(seeded_client: TestClient) -> None:
    response = seeded_client.get("/exercises/chord-name")
    body = response.text
    assert "Name this chord" in body or "What chord is this" in body


def test_post_check_correct_canonical_guess(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "A major"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text
    assert "A major" in response.text


def test_post_check_correct_alias_am(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_minor", "guess": "Am"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text
    assert "A minor" in response.text


def test_post_check_correct_alias_amaj7(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_maj7", "guess": "Amaj7"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_check_correct_alias_am7(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_min7", "guess": "Am7"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_check_incorrect_reveals_expected_name(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "Bm"},
    )
    assert response.status_code == 200
    assert "the chord is A major" in response.text
    assert "Bm" in response.text


def test_post_check_unknown_chord_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "unknown", "guess": "A"},
    )
    assert response.status_code == 404


def test_post_check_rejects_empty_guess(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": ""},
    )
    # FastAPI's Form(min_length=1) returns 422 for validation failure.
    assert response.status_code == 422
