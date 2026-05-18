import random
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
        fret
        for fret in range(MAX_FRET + 1)
        if note_for_string(string_number, fret) == target_note
    )


def pick_find_note_question(rng: random.Random) -> FindNoteQuestion:
    string_number = rng.choice(sorted(STANDARD_TUNING))
    target_note = rng.choice(CHROMATIC)
    return FindNoteQuestion(
        string_number=string_number,
        target_note=target_note,
    )


def is_correct_fret(string_number: int, fret: int, target_note: Note) -> bool:
    return fret in find_frets_for_note(string_number, target_note)
