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
    assert len(CHORDS) == 57
    ids = [c.id for c in CHORDS]
    assert len(set(ids)) == 57


def test_catalog_includes_movable_shapes_above_open_window() -> None:
    """The catalog must contain shapes whose lowest fret is above the open-window (>1)
    so users practise positions across the neck, not just open chords."""
    fretted_minimums = []
    for chord in CHORDS:
        frets = [s.fret for s in chord.strings if s.fret is not None]
        if frets:
            fretted_minimums.append(min(frets))
    assert max(fretted_minimums) >= 7, (
        "expected at least one chord with a minimum fretted note at fret 7 or higher"
    )


def test_multiple_shapes_share_a_canonical_name() -> None:
    """Movable shapes are intentionally added under the same canonical name as their
    open counterparts so chord-name guesses still match."""
    names = [c.name for c in CHORDS]
    assert names.count("A major") >= 2
    assert names.count("E minor") >= 2


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
