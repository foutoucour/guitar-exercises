import random
from collections.abc import Collection
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from guitar_exercises.domain.notes import CHROMATIC, Note
from guitar_exercises.domain.tuning import STANDARD_TUNING, note_for_string

MAX_FRET = 12


class FindNoteQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    string_number: Annotated[int, Field(ge=1, le=6)]
    target_note: Note


def find_frets_for_note(string_number: int, target_note: Note) -> tuple[int, ...]:
    if string_number not in STANDARD_TUNING:
        raise ValueError(f"string_number must be 1..6, got {string_number}")
    return tuple(
        fret for fret in range(MAX_FRET + 1) if note_for_string(string_number, fret) == target_note
    )


def find_note_question_key(question: FindNoteQuestion) -> str:
    return f"{question.string_number}:{question.target_note.value}"


def _all_find_note_questions() -> tuple[FindNoteQuestion, ...]:
    return tuple(
        FindNoteQuestion(string_number=string_number, target_note=note)
        for string_number in sorted(STANDARD_TUNING)
        for note in CHROMATIC
    )


_FIND_NOTE_POOL: tuple[FindNoteQuestion, ...] = _all_find_note_questions()


def pick_find_note_question(
    rng: random.Random,
    exclude_keys: Collection[str] = (),
) -> FindNoteQuestion:
    """Pick a (string, target-note) question, avoiding ``exclude_keys``.

    Falls back to the full pool if every question is excluded.
    """
    if not exclude_keys:
        return rng.choice(_FIND_NOTE_POOL)
    excluded = set(exclude_keys)
    available = [q for q in _FIND_NOTE_POOL if find_note_question_key(q) not in excluded]
    if not available:
        available = list(_FIND_NOTE_POOL)
    return rng.choice(available)


def is_correct_fret(string_number: int, fret: int, target_note: Note) -> bool:
    return fret in find_frets_for_note(string_number, target_note)
