import random
import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Self

import yaml
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


def _find_repo_root(start: Path) -> Path:
    """Walk upward from ``start`` until a directory containing ``pyproject.toml`` is found.

    Used instead of a hard-coded ``parents[N]`` index so the chord catalog path stays
    correct if the package is moved or re-nested. Raises ``FileNotFoundError`` if no
    ancestor contains a ``pyproject.toml`` — surfaces misconfiguration loudly at
    import time rather than silently resolving to the wrong location.
    """
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(
        f"could not locate a pyproject.toml ancestor starting from {start}; "
        "the chords.yaml location cannot be resolved"
    )


_CHORDS_FILE = _find_repo_root(Path(__file__).resolve()) / "config" / "chords.yaml"


def _load_chords_from_yaml(path: Path) -> tuple[Chord, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "chords" not in raw:
        raise ValueError(f"{path}: expected a top-level 'chords' list")
    return tuple(
        _build_chord(
            chord_id=entry["id"],
            name=entry["name"],
            frets=entry["frets"],
            fingers=entry["fingers"],
        )
        for entry in raw["chords"]
    )


CHORDS: tuple[Chord, ...] = _load_chords_from_yaml(_CHORDS_FILE)

_CHORDS_BY_ID: dict[str, Chord] = {chord.id: chord for chord in CHORDS}


def pick_chord(rng: random.Random) -> Chord:
    return rng.choice(CHORDS)


def get_chord_by_id(chord_id: str) -> Chord | None:
    return _CHORDS_BY_ID.get(chord_id)


_SEPARATORS_RE = re.compile(r"[\s\-_]+")
_BARE_ROOT_RE = re.compile(r"^([a-g]#?)$")
_ROOT_PLUS_M_RE = re.compile(r"^([a-g]#?)m$")

# Single-pass token expansion. Order matters — Python regex alternation takes the
# first alternative that matches at each position, so longer tokens must come
# first to prevent e.g. "minor" being re-matched as "min" → "minoror".
_QUALITY_RE = re.compile(r"major7|minor7|maj7|min7|m7|major|minor|maj|min")
_QUALITY_MAP = {
    "major7": "major7",
    "minor7": "minor7",
    "maj7": "major7",
    "min7": "minor7",
    "m7": "minor7",
    "major": "major",
    "minor": "minor",
    "maj": "major",
    "min": "minor",
}


def _normalize_chord_name(s: str) -> str:
    """Canonicalise a chord name so common spellings collapse to a single form.

    Examples (input → canonical):
        "A major"     → "amajor"
        "A"           → "amajor"   (bare root assumed major)
        "Am"          → "aminor"   (trailing m shorthand)
        "Amin"        → "aminor"
        "A minor"     → "aminor"
        "Am7"         → "aminor7"
        "Amaj7"       → "amajor7"
        "A minor 7"   → "aminor7"
    """
    s = s.strip().lower().replace("♯", "#")
    s = _SEPARATORS_RE.sub("", s)

    s = _QUALITY_RE.sub(lambda m: _QUALITY_MAP[m.group(0)], s)

    s = _ROOT_PLUS_M_RE.sub(r"\1minor", s)
    s = _BARE_ROOT_RE.sub(r"\1major", s)

    return s


def is_correct_chord_guess(guess: str, chord: Chord) -> bool:
    return _normalize_chord_name(guess) == _normalize_chord_name(chord.name)
