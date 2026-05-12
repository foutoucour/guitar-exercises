import random

import pytest
from pydantic import ValidationError

from guitar_exercises.domain.chords import (
    CHORDS,
    Chord,
    StringSpec,
    StringState,
    get_chord_by_id,
    pick_chord,
)
from guitar_exercises.domain.notes import Note


def test_fretted_string_requires_fret_and_finger() -> None:
    with pytest.raises(ValidationError):
        StringSpec(string_number=5, state=StringState.FRETTED)


def test_fretted_string_accepts_fret_and_finger() -> None:
    spec = StringSpec(string_number=5, state=StringState.FRETTED, fret=2, finger=1)
    assert spec.note == Note.B


def test_open_string_rejects_fret() -> None:
    with pytest.raises(ValidationError):
        StringSpec(string_number=5, state=StringState.OPEN, fret=2)


def test_muted_string_rejects_finger() -> None:
    with pytest.raises(ValidationError):
        StringSpec(string_number=5, state=StringState.MUTED, finger=1)


def test_open_string_has_open_note() -> None:
    spec = StringSpec(string_number=5, state=StringState.OPEN)
    assert spec.note == Note.A


def test_muted_string_has_no_note() -> None:
    spec = StringSpec(string_number=6, state=StringState.MUTED)
    assert spec.note is None


def test_chord_requires_six_strings() -> None:
    fixture = next(c for c in CHORDS if c.id == "a_major")
    with pytest.raises(ValidationError):
        Chord(id="x", name="x", strings=fixture.strings[:5])


def test_a_major_notes_by_string() -> None:
    chord = next(c for c in CHORDS if c.id == "a_major")
    assert chord.notes_by_string == {
        6: None,
        5: Note.A,
        4: Note.E,
        3: Note.A,
        2: Note.C_SHARP,
        1: Note.E,
    }


def test_e_minor_7_notes_by_string() -> None:
    chord = next(c for c in CHORDS if c.id == "e_min7")
    assert chord.notes_by_string == {
        6: Note.E,
        5: Note.B,
        4: Note.D,
        3: Note.G,
        2: Note.B,
        1: Note.E,
    }


def test_g_major_notes_by_string() -> None:
    chord = next(c for c in CHORDS if c.id == "g_major")
    assert chord.notes_by_string == {
        6: Note.G,
        5: Note.B,
        4: Note.D,
        3: Note.G,
        2: Note.B,
        1: Note.G,
    }


def test_d_7_notes_by_string() -> None:
    chord = next(c for c in CHORDS if c.id == "d_7")
    assert chord.notes_by_string == {
        6: None,
        5: None,
        4: Note.D,
        3: Note.A,
        2: Note.C,
        1: Note.F_SHARP,
    }


def test_catalog_size_and_unique_ids() -> None:
    assert len(CHORDS) == 23
    ids = [c.id for c in CHORDS]
    assert len(set(ids)) == 23


def test_pick_chord_is_deterministic_with_seed() -> None:
    rng_a = random.Random(42)
    rng_b = random.Random(42)
    assert pick_chord(rng_a).id == pick_chord(rng_b).id


def test_get_chord_by_id_returns_known_chord() -> None:
    chord = get_chord_by_id("a_major")
    assert chord is not None
    assert chord.name == "A major"


def test_get_chord_by_id_returns_none_for_unknown() -> None:
    assert get_chord_by_id("unknown_chord") is None
