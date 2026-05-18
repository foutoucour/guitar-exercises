"""Integration tests for the per-answer timer + history-cookie flow."""

import random
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from guitar_exercises.domain.chords import CHORDS, get_chord_by_id
from guitar_exercises.domain.find_note import MAX_FRET
from guitar_exercises.domain.name_note import NameNoteQuestion
from guitar_exercises.domain.notes import Note
from guitar_exercises.domain.timings import (
    TIMINGS_WINDOW,
    parse_timings,
)
from guitar_exercises.main import create_app
from guitar_exercises.routes import exercises as exercises_module
from guitar_exercises.routes.exercises import (
    BEST_STREAK_COOKIE_CHORD_NAME,
    BEST_STREAK_COOKIE_CHORD_NOTES,
    BEST_STREAK_COOKIE_FIND_NOTE,
    BEST_STREAK_COOKIE_NAME_NOTE,
    TIMINGS_COOKIE_CHORD_NAME,
    TIMINGS_COOKIE_CHORD_NOTES,
    TIMINGS_COOKIE_FIND_NOTE,
    TIMINGS_COOKIE_NAME_NOTE,
    get_rng,
)


@pytest.fixture
def pinned_name_note_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    pinned = NameNoteQuestion(string_number=6, fret=5, expected_note=Note.A)
    monkeypatch.setattr(exercises_module, "pick_name_note_question", lambda *_a, **_kw: pinned)
    with TestClient(create_app()) as client:
        yield client


@pytest.fixture
def seeded_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_rng] = lambda: random.Random(42)
    with TestClient(app) as client:
        yield client


# --- name-note (the simplest single-answer exercise) ---


def test_name_note_correct_with_elapsed_records_timing_cookie(
    pinned_name_note_client: TestClient,
) -> None:
    response = pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 2500},
    )
    assert response.status_code == 200
    raw = pinned_name_note_client.cookies.get(TIMINGS_COOKIE_NAME_NOTE)
    assert raw is not None
    entries = parse_timings(raw)
    assert len(entries) == 1
    assert entries[0].correct is True
    assert entries[0].elapsed_ms == 2500


def test_name_note_incorrect_with_elapsed_records_incorrect_entry(
    pinned_name_note_client: TestClient,
) -> None:
    response = pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "C", "elapsed_ms": 7100},
    )
    assert response.status_code == 200
    entries = parse_timings(pinned_name_note_client.cookies.get(TIMINGS_COOKIE_NAME_NOTE))
    assert entries[0].correct is False
    assert entries[0].elapsed_ms == 7100


def test_name_note_without_elapsed_does_not_record_timing(
    pinned_name_note_client: TestClient,
) -> None:
    # An old/JS-disabled client may not send elapsed_ms — the exercise must
    # still work, just without recording a timing.
    response = pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A"},
    )
    assert response.status_code == 200
    assert pinned_name_note_client.cookies.get(TIMINGS_COOKIE_NAME_NOTE) is None


def test_name_note_feedback_includes_elapsed_seconds(
    pinned_name_note_client: TestClient,
) -> None:
    response = pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 2500},
    )
    assert "in 2.5s" in response.text


def test_name_note_history_widget_appears_after_first_answer(
    pinned_name_note_client: TestClient,
) -> None:
    # Page starts with no widget content beyond the live timer.
    page = pinned_name_note_client.get("/exercises/name-note").text
    assert "exercise-timer-live" in page
    assert "exercise-timer-chip" not in page

    pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 1800},
    )
    page = pinned_name_note_client.get("/exercises/name-note").text
    assert "exercise-timer-chip" in page
    assert "1.8s" in page  # the chip's seconds label


def test_name_note_streak_increments_then_resets(
    pinned_name_note_client: TestClient,
) -> None:
    # Three correct answers in a row.
    for _ in range(3):
        pinned_name_note_client.post(
            "/exercises/name-note/check",
            data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 1000},
        )
    page = pinned_name_note_client.get("/exercises/name-note").text
    assert "exercise-timer-streak-value" in page
    # The streak value is rendered in its own span — use a marker to grab it.
    assert ">3<" in page

    # A wrong answer must drop the current streak to 0 while keeping best at 3.
    pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "C", "elapsed_ms": 1000},
    )
    page = pinned_name_note_client.get("/exercises/name-note").text
    assert ">0<" in page
    assert "best 3" in page


def test_name_note_timing_cookie_caps_at_window(
    pinned_name_note_client: TestClient,
) -> None:
    for _ in range(TIMINGS_WINDOW + 4):
        pinned_name_note_client.post(
            "/exercises/name-note/check",
            data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 500},
        )
    entries = parse_timings(pinned_name_note_client.cookies.get(TIMINGS_COOKIE_NAME_NOTE))
    assert len(entries) == TIMINGS_WINDOW


# --- chord-name ---


def test_chord_name_records_timing_with_elapsed(seeded_client: TestClient) -> None:
    page = seeded_client.get("/exercises/chord-name").text
    chord_id = next(c.id for c in CHORDS if c.id in page)
    chord = get_chord_by_id(chord_id)
    assert chord is not None

    response = seeded_client.post(
        "/exercises/chord-name/check",
        data={"chord_id": chord_id, "guess": chord.name, "elapsed_ms": 3200},
    )
    assert response.status_code == 200
    assert "in 3.2s" in response.text
    entries = parse_timings(seeded_client.cookies.get(TIMINGS_COOKIE_CHORD_NAME))
    assert len(entries) == 1
    assert entries[0].correct is True
    assert entries[0].elapsed_ms == 3200


# --- find-note ---


def test_find_note_records_timing_with_elapsed(seeded_client: TestClient) -> None:
    # E on string 6 is at fret 0. Any other fret is wrong — use 0 for correct.
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={
            "string_number": 6,
            "target_note": "E",
            "fret": 0,
            "elapsed_ms": 4400,
        },
    )
    assert response.status_code == 200
    assert "in 4.4s" in response.text
    entries = parse_timings(seeded_client.cookies.get(TIMINGS_COOKIE_FIND_NOTE))
    assert len(entries) == 1
    assert entries[0].correct is True
    assert entries[0].elapsed_ms == 4400


def test_find_note_rejects_out_of_range_elapsed(seeded_client: TestClient) -> None:
    # Anything past the form's `le=600_000` ceiling must be rejected at the
    # boundary — guards against a clock-skew client submitting a huge value.
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={
            "string_number": 6,
            "target_note": "E",
            "fret": 0,
            "elapsed_ms": 600_001,
        },
    )
    assert response.status_code == 422


# --- chord-notes (special case: one entry per chord, on final string) ---


def _chord_notes_chord_from_page(html: str) -> tuple[str, list[int]]:
    """Pull the chord id and the playable (non-muted) string numbers."""
    import re

    chord_match = re.search(r'name="chord_id" value="([^"]+)"', html)
    assert chord_match is not None, "no chord_id input found"
    chord_id = chord_match.group(1)
    chord = get_chord_by_id(chord_id)
    assert chord is not None
    playable = sorted(s for s, note in chord.notes_by_string.items() if note is not None)
    return chord_id, playable


def test_chord_notes_non_final_string_does_not_record(seeded_client: TestClient) -> None:
    page = seeded_client.get("/exercises/chord-notes").text
    chord_id, playable = _chord_notes_chord_from_page(page)
    assert len(playable) >= 2, "this test needs a multi-string chord"

    chord = get_chord_by_id(chord_id)
    assert chord is not None
    first_string = playable[0]
    expected = chord.notes_by_string[first_string].value

    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={
            "chord_id": chord_id,
            "string_number": first_string,
            "guess": expected,
            "elapsed_ms": 1500,
            # final_string omitted (defaults to 0)
        },
    )
    assert response.status_code == 200
    # Per-string feedback still shows the inline elapsed for the user.
    assert "in 1.5s" in response.text
    # But the per-chord history cookie must NOT have been written yet.
    assert seeded_client.cookies.get(TIMINGS_COOKIE_CHORD_NOTES) is None


def test_chord_notes_final_string_records_one_entry(seeded_client: TestClient) -> None:
    page = seeded_client.get("/exercises/chord-notes").text
    chord_id, playable = _chord_notes_chord_from_page(page)
    chord = get_chord_by_id(chord_id)
    assert chord is not None
    last_string = playable[-1]
    expected = chord.notes_by_string[last_string].value

    response = seeded_client.post(
        "/exercises/chord-notes/check",
        data={
            "chord_id": chord_id,
            "string_number": last_string,
            "guess": expected,
            "elapsed_ms": 6800,
            "final_string": 1,
            "chord_correct": 1,
        },
    )
    assert response.status_code == 200
    entries = parse_timings(seeded_client.cookies.get(TIMINGS_COOKIE_CHORD_NOTES))
    assert len(entries) == 1
    assert entries[0].correct is True
    assert entries[0].elapsed_ms == 6800


def test_chord_notes_final_string_wrong_records_incorrect_chord(
    seeded_client: TestClient,
) -> None:
    # If the client reports "all priors were correct" but the final string is
    # itself wrong, the chord verdict is wrong — the server ANDs the two.
    page = seeded_client.get("/exercises/chord-notes").text
    chord_id, playable = _chord_notes_chord_from_page(page)
    chord = get_chord_by_id(chord_id)
    assert chord is not None
    last_string = playable[-1]
    expected = chord.notes_by_string[last_string].value
    wrong_guess = "C" if expected != "C" else "D"

    seeded_client.post(
        "/exercises/chord-notes/check",
        data={
            "chord_id": chord_id,
            "string_number": last_string,
            "guess": wrong_guess,
            "elapsed_ms": 5500,
            "final_string": 1,
            "chord_correct": 1,
        },
    )
    entries = parse_timings(seeded_client.cookies.get(TIMINGS_COOKIE_CHORD_NOTES))
    assert len(entries) == 1
    assert entries[0].correct is False


def test_chord_notes_history_cookie_is_independent_of_other_exercises(
    pinned_name_note_client: TestClient,
) -> None:
    # Posting to name-note must not populate any other exercise's history
    # cookie — each game's stats are scoped to that game.
    pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 1000},
    )
    assert pinned_name_note_client.cookies.get(TIMINGS_COOKIE_NAME_NOTE) is not None
    for cookie in (
        TIMINGS_COOKIE_CHORD_NAME,
        TIMINGS_COOKIE_CHORD_NOTES,
        TIMINGS_COOKIE_FIND_NOTE,
        BEST_STREAK_COOKIE_CHORD_NAME,
        BEST_STREAK_COOKIE_CHORD_NOTES,
        BEST_STREAK_COOKIE_FIND_NOTE,
    ):
        assert pinned_name_note_client.cookies.get(cookie) is None


def test_best_streak_survives_a_reset(pinned_name_note_client: TestClient) -> None:
    for _ in range(5):
        pinned_name_note_client.post(
            "/exercises/name-note/check",
            data={"string_number": 6, "fret": 5, "guess": "A", "elapsed_ms": 1200},
        )
    assert pinned_name_note_client.cookies.get(BEST_STREAK_COOKIE_NAME_NOTE) == "5"

    # A wrong answer drops the current streak but must NOT lower best_streak.
    pinned_name_note_client.post(
        "/exercises/name-note/check",
        data={"string_number": 6, "fret": 5, "guess": "C", "elapsed_ms": 1200},
    )
    assert pinned_name_note_client.cookies.get(BEST_STREAK_COOKIE_NAME_NOTE) == "5"


def test_max_fret_route_constant_is_used_for_form_validation(
    seeded_client: TestClient,
) -> None:
    # Defensive: ensure MAX_FRET stays a meaningful upper bound on `fret`.
    response = seeded_client.post(
        "/exercises/find-note/check",
        data={"string_number": 6, "target_note": "E", "fret": MAX_FRET + 1},
    )
    assert response.status_code == 422
