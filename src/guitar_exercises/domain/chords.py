import random
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from guitar_exercises.domain.notes import Note
from guitar_exercises.domain.tuning import note_for_string


class StringState(StrEnum):
    MUTED = "muted"
    OPEN = "open"
    FRETTED = "fretted"


class StringSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    string_number: Annotated[int, Field(ge=1, le=6)]
    state: StringState
    fret: Annotated[int | None, Field(ge=1, le=24, default=None)] = None
    finger: Annotated[int | None, Field(ge=1, le=4, default=None)] = None

    @model_validator(mode="after")
    def _validate_state_fields(self) -> Self:
        if self.state is StringState.FRETTED:
            if self.fret is None or self.finger is None:
                raise ValueError("fretted strings require both fret and finger")
        else:
            if self.fret is not None or self.finger is not None:
                raise ValueError(f"{self.state.value} strings must not specify fret or finger")
        return self

    @property
    def note(self) -> Note | None:
        if self.state is StringState.MUTED:
            return None
        return note_for_string(self.string_number, self.fret or 0)


class Chord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    strings: tuple[StringSpec, ...]

    @model_validator(mode="after")
    def _validate_strings(self) -> Self:
        if len(self.strings) != 6:
            raise ValueError(f"chord must have exactly 6 strings, got {len(self.strings)}")
        numbers = [s.string_number for s in self.strings]
        if numbers != [6, 5, 4, 3, 2, 1]:
            raise ValueError(f"strings must be ordered 6..1, got {numbers}")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def notes_by_string(self) -> dict[int, Note | None]:
        return {s.string_number: s.note for s in self.strings}


def _build_chord(
    chord_id: str,
    name: str,
    frets: list[int | None],
    fingers: list[int | None],
) -> Chord:
    """Compact builder. `frets` and `fingers` are indexed 0..5 where 0 = string 6 (low E).

    fret semantics:
        None -> MUTED
        0    -> OPEN
        >=1  -> FRETTED (finger required at same index)
    """
    if len(frets) != 6 or len(fingers) != 6:
        raise ValueError("frets and fingers must each have 6 entries")

    specs: list[StringSpec] = []
    for index in range(6):
        string_number = 6 - index
        fret = frets[index]
        finger = fingers[index]
        if fret is None:
            state = StringState.MUTED
            specs.append(StringSpec(string_number=string_number, state=state))
        elif fret == 0:
            state = StringState.OPEN
            specs.append(StringSpec(string_number=string_number, state=state))
        else:
            specs.append(
                StringSpec(
                    string_number=string_number,
                    state=StringState.FRETTED,
                    fret=fret,
                    finger=finger,
                )
            )
    return Chord(id=chord_id, name=name, strings=tuple(specs))


CHORDS: tuple[Chord, ...] = (
    _build_chord("a_major", "A major", [None, 0, 2, 2, 2, 0], [None, None, 1, 2, 3, None]),
    _build_chord("a_minor", "A minor", [None, 0, 2, 2, 1, 0], [None, None, 2, 3, 1, None]),
    _build_chord("a_7", "A7", [None, 0, 2, 0, 2, 0], [None, None, 1, None, 2, None]),
    _build_chord("a_maj7", "A major 7", [None, 0, 2, 1, 2, 0], [None, None, 2, 1, 3, None]),
    _build_chord("a_min7", "A minor 7", [None, 0, 2, 0, 1, 0], [None, None, 2, None, 1, None]),
    _build_chord("b_7", "B7", [None, 2, 1, 2, 0, 2], [None, 2, 1, 3, None, 4]),
    _build_chord("c_major", "C major", [None, 3, 2, 0, 1, 0], [None, 3, 2, None, 1, None]),
    _build_chord("c_7", "C7", [None, 3, 2, 3, 1, 0], [None, 3, 2, 4, 1, None]),
    _build_chord("c_maj7", "C major 7", [None, 3, 2, 0, 0, 0], [None, 3, 2, None, None, None]),
    _build_chord("d_major", "D major", [None, None, 0, 2, 3, 2], [None, None, None, 1, 3, 2]),
    _build_chord("d_minor", "D minor", [None, None, 0, 2, 3, 1], [None, None, None, 2, 3, 1]),
    _build_chord("d_7", "D7", [None, None, 0, 2, 1, 2], [None, None, None, 2, 1, 3]),
    _build_chord("d_maj7", "D major 7", [None, None, 0, 2, 2, 2], [None, None, None, 1, 1, 1]),
    _build_chord("d_min7", "D minor 7", [None, None, 0, 2, 1, 1], [None, None, None, 2, 1, 1]),
    _build_chord("e_major", "E major", [0, 2, 2, 1, 0, 0], [None, 2, 3, 1, None, None]),
    _build_chord("e_minor", "E minor", [0, 2, 2, 0, 0, 0], [None, 2, 3, None, None, None]),
    _build_chord("e_7", "E7", [0, 2, 0, 1, 0, 0], [None, 2, None, 1, None, None]),
    _build_chord("e_maj7", "E major 7", [0, 2, 1, 1, 0, 0], [None, 3, 1, 2, None, None]),
    _build_chord("e_min7", "E minor 7", [0, 2, 0, 0, 0, 0], [None, 2, None, None, None, None]),
    _build_chord("f_maj7", "F major 7", [None, None, 3, 2, 1, 0], [None, None, 3, 2, 1, None]),
    _build_chord("g_major", "G major", [3, 2, 0, 0, 0, 3], [2, 1, None, None, None, 3]),
    _build_chord("g_7", "G7", [3, 2, 0, 0, 0, 1], [3, 2, None, None, None, 1]),
    _build_chord("g_maj7", "G major 7", [3, 2, 0, 0, 0, 2], [3, 2, None, None, None, 1]),
)


_CHORDS_BY_ID: dict[str, Chord] = {chord.id: chord for chord in CHORDS}


def pick_chord(rng: random.Random) -> Chord:
    return rng.choice(CHORDS)


def get_chord_by_id(chord_id: str) -> Chord | None:
    return _CHORDS_BY_ID.get(chord_id)
