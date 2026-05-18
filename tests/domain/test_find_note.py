import random

import pytest

from guitar_exercises.domain.find_note import (
    MAX_FRET,
    FindNoteQuestion,
    find_frets_for_note,
    find_note_question_key,
    is_correct_fret,
    pick_find_note_question,
)
from guitar_exercises.domain.notes import CHROMATIC, Note
from guitar_exercises.domain.tuning import STANDARD_TUNING


@pytest.mark.parametrize(
    ("string_number", "target_note", "expected"),
    [
        (6, Note.E, (0, 12)),
        (6, Note.F, (1, 13)),
        (5, Note.A, (0, 12)),
        (5, Note.G, (10,)),
        (4, Note.D, (0, 12)),
        (4, Note.E, (2, 14)),
        (3, Note.G, (0, 12)),
        (3, Note.A, (2, 14)),
        (2, Note.B, (0, 12)),
        (2, Note.C, (1, 13)),
        (1, Note.E, (0, 12)),
        (1, Note.G, (3, 15)),
    ],
)
def test_find_frets_for_note_known_anchors(
    string_number: int, target_note: Note, expected: tuple[int, ...]
) -> None:
    assert find_frets_for_note(string_number, target_note) == expected


def test_find_frets_for_note_covers_every_chromatic_note_on_every_string() -> None:
    for string_number in range(1, 7):
        for note in CHROMATIC:
            frets = find_frets_for_note(string_number, note)
            assert len(frets) >= 1
            assert all(0 <= fret <= MAX_FRET for fret in frets)


def test_find_frets_for_note_rejects_invalid_string() -> None:
    with pytest.raises(ValueError):
        find_frets_for_note(0, Note.A)
    with pytest.raises(ValueError):
        find_frets_for_note(7, Note.A)


@pytest.mark.parametrize(
    ("string_number", "fret", "target_note", "expected"),
    [
        (6, 0, Note.E, True),
        (6, 12, Note.E, True),
        (6, 1, Note.E, False),
        (5, 10, Note.G, True),
        (5, 11, Note.G, False),
        (2, 1, Note.C, True),
        (2, 1, Note.D, False),
    ],
)
def test_is_correct_fret(string_number: int, fret: int, target_note: Note, expected: bool) -> None:
    assert is_correct_fret(string_number, fret, target_note) is expected


def test_pick_find_note_question_returns_valid_question_for_any_seed() -> None:
    for seed in range(20):
        rng = random.Random(seed)
        question = pick_find_note_question(rng)
        assert isinstance(question, FindNoteQuestion)
        assert 1 <= question.string_number <= 6
        assert question.target_note in CHROMATIC
        assert len(find_frets_for_note(question.string_number, question.target_note)) >= 1


def test_pick_find_note_question_is_deterministic_for_same_seed() -> None:
    first = pick_find_note_question(random.Random(1234))
    second = pick_find_note_question(random.Random(1234))
    assert first == second


def test_pick_find_note_question_excludes_given_keys() -> None:
    # Build an exclude set covering every (string, note) except one — the
    # picker must return that one survivor.
    target = FindNoteQuestion(string_number=3, target_note=Note.E)
    survivor_key = find_note_question_key(target)
    exclude = {
        f"{s}:{n.value}"
        for s in sorted(STANDARD_TUNING)
        for n in CHROMATIC
        if f"{s}:{n.value}" != survivor_key
    }
    picked = pick_find_note_question(random.Random(0), exclude_keys=exclude)
    assert picked == target


def test_pick_find_note_question_falls_back_when_all_excluded() -> None:
    exclude = {f"{s}:{n.value}" for s in sorted(STANDARD_TUNING) for n in CHROMATIC}
    picked = pick_find_note_question(random.Random(0), exclude_keys=exclude)
    assert find_note_question_key(picked) in exclude
