from guitar_exercises.domain.notes import Note, note_at

STANDARD_TUNING: dict[int, Note] = {
    6: Note.E,
    5: Note.A,
    4: Note.D,
    3: Note.G,
    2: Note.B,
    1: Note.E,
}


def note_for_string(string_number: int, fret: int) -> Note:
    if string_number not in STANDARD_TUNING:
        raise ValueError(f"string_number must be 1..6, got {string_number}")
    return note_at(STANDARD_TUNING[string_number], fret)
