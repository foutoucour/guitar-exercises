import random

import pytest

from guitar_exercises.domain.find_note import MAX_FRET
from guitar_exercises.domain.name_note import (
    NameNoteQuestion,
    name_note_question_key,
    pick_name_note_question,
)
from guitar_exercises.domain.notes import CHROMATIC
from guitar_exercises.domain.tuning import STANDARD_TUNING, note_for_string


def test_pick_name_note_question_returns_valid_question_for_any_seed() -> None:
    for seed in range(20):
        rng = random.Random(seed)
        question = pick_name_note_question(rng)
        assert isinstance(question, NameNoteQuestion)
        assert 1 <= question.string_number <= 6
        assert 0 <= question.fret <= MAX_FRET
        assert question.expected_note in CHROMATIC
        # The expected note must match the actual note at that fret —
        # otherwise the exercise would mark correct answers as wrong.
        assert question.expected_note == note_for_string(question.string_number, question.fret)


def test_pick_name_note_question_is_deterministic_for_same_seed() -> None:
    first = pick_name_note_question(random.Random(7))
    second = pick_name_note_question(random.Random(7))
    assert first == second


def test_pick_name_note_question_excludes_given_keys() -> None:
    # Build an exclude set covering every (string, fret) except one — the
    # picker must return that one survivor.
    target_string, target_fret = 2, 7
    survivor_key = f"{target_string}:{target_fret}"
    exclude = {
        f"{s}:{f}"
        for s in sorted(STANDARD_TUNING)
        for f in range(MAX_FRET + 1)
        if f"{s}:{f}" != survivor_key
    }
    picked = pick_name_note_question(random.Random(0), exclude_keys=exclude)
    assert picked.string_number == target_string
    assert picked.fret == target_fret


def test_pick_name_note_question_falls_back_when_all_excluded() -> None:
    exclude = {f"{s}:{f}" for s in sorted(STANDARD_TUNING) for f in range(MAX_FRET + 1)}
    picked = pick_name_note_question(random.Random(0), exclude_keys=exclude)
    assert name_note_question_key(picked) in exclude


@pytest.mark.parametrize("max_seed", [200])
def test_pick_name_note_question_explores_full_range(max_seed: int) -> None:
    # A reasonable sample should hit every string and a variety of frets.
    strings_seen: set[int] = set()
    frets_seen: set[int] = set()
    for seed in range(max_seed):
        q = pick_name_note_question(random.Random(seed))
        strings_seen.add(q.string_number)
        frets_seen.add(q.fret)
    assert strings_seen == {1, 2, 3, 4, 5, 6}
    assert len(frets_seen) >= 10
