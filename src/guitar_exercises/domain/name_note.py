import random
from collections.abc import Collection
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from guitar_exercises.domain.find_note import MAX_FRET
from guitar_exercises.domain.notes import Note
from guitar_exercises.domain.tuning import STANDARD_TUNING, note_for_string


class NameNoteQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    string_number: Annotated[int, Field(ge=1, le=6)]
    fret: Annotated[int, Field(ge=0, le=MAX_FRET)]
    expected_note: Note


def name_note_question_key(question: NameNoteQuestion) -> str:
    return f"{question.string_number}:{question.fret}"


def _all_name_note_questions() -> tuple[NameNoteQuestion, ...]:
    return tuple(
        NameNoteQuestion(
            string_number=string_number,
            fret=fret,
            expected_note=note_for_string(string_number, fret),
        )
        for string_number in sorted(STANDARD_TUNING)
        for fret in range(MAX_FRET + 1)
    )


_NAME_NOTE_POOL: tuple[NameNoteQuestion, ...] = _all_name_note_questions()


def pick_name_note_question(
    rng: random.Random,
    exclude_keys: Collection[str] = (),
) -> NameNoteQuestion:
    """Pick a (string, fret) question, avoiding ``exclude_keys``.

    Falls back to the full pool if every question is excluded.
    """
    if not exclude_keys:
        return rng.choice(_NAME_NOTE_POOL)
    excluded = set(exclude_keys)
    available = [q for q in _NAME_NOTE_POOL if name_note_question_key(q) not in excluded]
    if not available:
        available = list(_NAME_NOTE_POOL)
    return rng.choice(available)
