import random
import re

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.chords import Chord, get_chord_by_id
from guitar_exercises.main import create_app
from guitar_exercises.routes import exercises as exercises_module
from guitar_exercises.routes.exercises import get_rng


@pytest.fixture
def seeded_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_rng] = lambda: random.Random(42)
    return TestClient(app)


# A major is muted on string 6 only — first playable string is 5. Pinning the
# chord (rather than seeding the RNG) decouples the tabindex assertions from
# the order of chords.yaml.
PINNED_CHORD_ID = "a_major"
PINNED_FIRST_PLAYABLE_STRING = 5
PINNED_MUTED_STRINGS = {6}


@pytest.fixture
def pinned_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    pinned: Chord = get_chord_by_id(PINNED_CHORD_ID)  # type: ignore[assignment]
    assert pinned is not None, f"fixture chord {PINNED_CHORD_ID!r} missing from catalog"
    monkeypatch.setattr(exercises_module, "pick_chord", lambda *_a, **_kw: pinned)
    return TestClient(create_app())


def _chip_tabindex_by_string(body: str, string_number: int) -> set[str]:
    """Return the set of tabindex values found on chips inside a given string row."""
    row_match = re.search(
        rf'<li id="string-{string_number}".*?</li>',
        body,
        re.DOTALL,
    )
    assert row_match is not None, f"string-{string_number} row not found"
    return set(re.findall(r'class="note-chip"\s+tabindex="(-?\d+)"', row_match.group(0)))


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


def test_first_playable_string_chips_are_in_tab_order(pinned_client: TestClient) -> None:
    # Tab should land inside the first playable string's chip group, so only
    # those chips are tabbable on initial render.
    response = pinned_client.get("/exercises/chord-notes")
    body = response.text
    assert _chip_tabindex_by_string(body, PINNED_FIRST_PLAYABLE_STRING) == {"0"}


def test_other_playable_string_chips_are_removed_from_tab_order(
    pinned_client: TestClient,
) -> None:
    # All other playable strings must be unreachable via Tab until the user
    # answers the active string — JS unlocks them after the swap.
    response = pinned_client.get("/exercises/chord-notes")
    body = response.text
    for string_number in range(1, 7):
        if string_number in PINNED_MUTED_STRINGS:
            continue
        if string_number == PINNED_FIRST_PLAYABLE_STRING:
            continue
        assert _chip_tabindex_by_string(body, string_number) == {"-1"}, (
            f"string {string_number} chips should be tabindex=-1"
        )


def test_chord_notes_page_includes_keyboard_navigation_script(
    pinned_client: TestClient,
) -> None:
    # The Tab-cycle and post-swap focus logic lives in chord-notes.js; if the
    # script tag is dropped the keyboard UX silently regresses.
    response = pinned_client.get("/exercises/chord-notes")
    assert "/static/js/chord-notes.js" in response.text


def test_answer_feedback_row_has_no_chips(seeded_client: TestClient) -> None:
    # Once a string is answered the row must not contain any note chips —
    # this is what tells the JS the row is no longer playable.
    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={"chord_id": "a_major", "string_number": 5, "guess": "A"},
    )
    assert "note-chip" not in response.text
    assert "string-row-answered" in response.text
