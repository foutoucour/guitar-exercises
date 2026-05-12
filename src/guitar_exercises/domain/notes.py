from enum import StrEnum


class Note(StrEnum):
    C = "C"
    C_SHARP = "C#"
    D = "D"
    D_SHARP = "D#"
    E = "E"
    F = "F"
    F_SHARP = "F#"
    G = "G"
    G_SHARP = "G#"
    A = "A"
    A_SHARP = "A#"
    B = "B"


CHROMATIC: tuple[Note, ...] = (
    Note.C,
    Note.C_SHARP,
    Note.D,
    Note.D_SHARP,
    Note.E,
    Note.F,
    Note.F_SHARP,
    Note.G,
    Note.G_SHARP,
    Note.A,
    Note.A_SHARP,
    Note.B,
)


def note_at(open_note: Note, fret: int) -> Note:
    if fret < 0:
        raise ValueError(f"fret must be non-negative, got {fret}")

    start = CHROMATIC.index(open_note)
    return CHROMATIC[(start + fret) % len(CHROMATIC)]


def is_correct_guess(guess: str, expected: Note) -> bool:
    normalised = guess.strip().upper().replace("♯", "#")
    return normalised == expected.value
