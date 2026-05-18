import random

import pytest

from guitar_exercises.domain.find_note import MAX_FRET
from guitar_exercises.domain.name_note import NameNoteQuestion, pick_name_note_question
from guitar_exercises.domain.notes import CHROMATIC
from guitar_exercises.domain.tuning import note_for_string


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
        assert question.expected_note == note_for_string(
            question.string_number, question.fret
        )


def test_pick_name_note_question_is_deterministic_for_same_seed() -> None:
    first = pick_name_note_question(random.Random(7))
    second = pick_name_note_question(random.Random(7))
    assert first == second


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
