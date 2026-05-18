import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.chords import Chord, get_chord_by_id
from guitar_exercises.main import create_app
from guitar_exercises.routes import exercises as exercises_module

# Chord pinned for the GET-page tests. Stubbing pick_chord (rather than seeding
# the RNG) decouples these assertions from the order of chords.yaml — adding
# a new chord to the catalog cannot silently change which chord gets picked.
PINNED_CHORD_ID = "g_major"
PINNED_CHORD_NAME = "G major"


@pytest.fixture
def pinned_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    pinned: Chord = get_chord_by_id(PINNED_CHORD_ID)  # type: ignore[assignment]
    assert pinned is not None, f"fixture chord {PINNED_CHORD_ID!r} missing from catalog"
    monkeypatch.setattr(exercises_module, "pick_chord", lambda *_a, **_kw: pinned)
    return TestClient(create_app())


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_get_chord_name_returns_html_page(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/chord-name")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<svg" in body
    assert "</svg>" in body


def test_get_chord_name_does_not_leak_chord_display_name(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/chord-name")
    body = response.text

    # The display name must not appear anywhere on the page — not in the
    # heading, not in the SVG <title>/<desc>, not in alt text.
    assert PINNED_CHORD_NAME not in body
    # The hidden form field still carries the slug id so /check can find it.
    assert f'value="{PINNED_CHORD_ID}"' in body


def test_get_chord_name_renders_guess_form(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/chord-name")
    body = response.text
    assert 'hx-post="/exercises/chord-name/check"' in body
    assert 'name="chord_id"' in body
    assert 'name="guess"' in body
    assert 'type="text"' in body


def test_get_chord_name_prompts_user_to_name_the_chord(pinned_client: TestClient) -> None:
    response = pinned_client.get("/exercises/chord-name")
    body = response.text
    assert "Name this chord" in body or "What chord is this" in body


def test_post_check_correct_canonical_guess(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "A major"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text
    assert "A major" in response.text


def test_post_check_correct_auto_advances_to_next_chord(client: TestClient) -> None:
    # A correct guess should auto-advance without a click — the user shouldn't
    # have to hit "New chord" after every right answer. The navigation goes
    # through the shared helper so the delay can be tuned site-wide.
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "A major"},
    )
    body = response.text
    assert 'data-auto-advance="1"' in body
    assert "window.GuitarExercises.advanceTo('/exercises/chord-name')" in body
    # Keep a manual fallback if inline auto-advance is unavailable.
    assert 'href="/exercises/chord-name"' in body


def test_post_check_incorrect_keeps_manual_new_chord_link(client: TestClient) -> None:
    # Incorrect feedback must NOT auto-advance — the user needs time to read
    # the expected answer before moving on.
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "Bm"},
    )
    body = response.text
    assert 'data-auto-advance="0"' in body
    assert "advanceTo" not in body
    assert 'href="/exercises/chord-name"' in body


def test_post_check_incorrect_arms_key_advance(client: TestClient) -> None:
    # Keyboard players must be able to move on with Enter/Space without
    # reaching for the mouse — the failure feedback arms a key listener.
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "Bm"},
    )
    body = response.text
    assert "window.GuitarExercises.armKeyAdvance('/exercises/chord-name')" in body


def test_post_check_correct_alias_am(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_minor", "guess": "Am"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text
    assert "A minor" in response.text


def test_post_check_correct_alias_amaj7(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_maj7", "guess": "Amaj7"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_check_correct_alias_am7(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_min7", "guess": "Am7"},
    )
    assert response.status_code == 200
    assert "Correct" in response.text


def test_post_check_incorrect_reveals_expected_name(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "Bm"},
    )
    assert response.status_code == 200
    assert "the chord is A major" in response.text
    assert "Bm" in response.text


def test_post_check_unknown_chord_returns_404(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "unknown", "guess": "A"},
    )
    assert response.status_code == 404


def test_post_check_rejects_empty_guess(client: TestClient) -> None:
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": ""},
    )
    # FastAPI's Form(min_length=1) returns 422 for validation failure.
    assert response.status_code == 422


def test_post_check_rejects_whitespace_only_guess(client: TestClient) -> None:
    # `Form(min_length=1)` accepts whitespace; the handler must strip and
    # reject so the user never sees feedback like "You said    — the chord is …".
    response = client.post(
        "/exercises/chord-name/check",
        data={"chord_id": "a_major", "guess": "   "},
    )
    assert response.status_code == 422
