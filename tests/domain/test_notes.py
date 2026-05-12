import pytest

from guitar_exercises.domain.notes import CHROMATIC, Note, is_correct_guess, note_at
from guitar_exercises.domain.tuning import note_for_string


@pytest.mark.parametrize("open_note", list(Note))
def test_note_at_open_string_returns_root(open_note: Note) -> None:
    assert note_at(open_note, 0) == open_note


@pytest.mark.parametrize("open_note", list(Note))
def test_note_at_fret_twelve_returns_root_octave(open_note: Note) -> None:
    assert note_at(open_note, 12) == open_note


def test_note_at_wraps_chromatic_scale() -> None:
    assert note_at(Note.A, 1) == Note.A_SHARP
    assert note_at(Note.A, 2) == Note.B
    assert note_at(Note.A, 3) == Note.C


def test_note_at_rejects_negative_fret() -> None:
    with pytest.raises(ValueError):
        note_at(Note.E, -1)


@pytest.mark.parametrize(
    ("string_number", "fret", "expected"),
    [
        (6, 0, Note.E),
        (6, 5, Note.A),
        (5, 0, Note.A),
        (5, 2, Note.B),
        (4, 0, Note.D),
        (4, 2, Note.E),
        (3, 0, Note.G),
        (3, 2, Note.A),
        (2, 0, Note.B),
        (2, 1, Note.C),
        (2, 2, Note.C_SHARP),
        (1, 0, Note.E),
    ],
)
def test_note_for_string_known_anchors(string_number: int, fret: int, expected: Note) -> None:
    assert note_for_string(string_number, fret) == expected


def test_note_for_string_rejects_invalid_string() -> None:
    with pytest.raises(ValueError):
        note_for_string(7, 0)


def test_chromatic_scale_has_twelve_notes() -> None:
    assert len(CHROMATIC) == 12
    assert len(set(CHROMATIC)) == 12


@pytest.mark.parametrize(
    ("guess", "expected", "result"),
    [
        ("C", Note.C, True),
        ("c", Note.C, True),
        (" C# ", Note.C_SHARP, True),
        ("C♯", Note.C_SHARP, True),
        ("Db", Note.C_SHARP, False),
        ("D", Note.C, False),
    ],
)
def test_is_correct_guess(guess: str, expected: Note, result: bool) -> None:
    assert is_correct_guess(guess, expected) is result
