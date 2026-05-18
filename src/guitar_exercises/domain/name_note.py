import random
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


def pick_name_note_question(rng: random.Random) -> NameNoteQuestion:
    string_number = rng.choice(sorted(STANDARD_TUNING))
    fret = rng.randint(0, MAX_FRET)
    return NameNoteQuestion(
        string_number=string_number,
        fret=fret,
        expected_note=note_for_string(string_number, fret),
    )
