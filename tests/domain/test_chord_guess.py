import pytest

from guitar_exercises.domain.chords import (
    CHORDS,
    Chord,
    StringSpec,
    StringState,
    get_chord_by_id,
    is_correct_chord_guess,
)


def _chord(chord_id: str) -> Chord:
    chord = get_chord_by_id(chord_id)
    assert chord is not None, f"fixture chord {chord_id!r} missing from CHORDS"
    return chord


@pytest.mark.parametrize(
    ("chord_id", "guess"),
    [
        # bare canonical
        ("a_major", "A major"),
        ("a_minor", "A minor"),
        ("a_7", "A7"),
        ("a_maj7", "A major 7"),
        ("a_min7", "A minor 7"),
        # case insensitive
        ("c_major", "c major"),
        ("c_major", "C MAJOR"),
        # whitespace & separator tolerant
        ("d_minor", "  D   minor  "),
        ("d_minor", "D-minor"),
        ("d_minor", "D_minor"),
        # major shorthand: bare root
        ("c_major", "C"),
        ("g_major", "g"),
        # minor shorthand: root + m
        ("a_minor", "Am"),
        ("e_minor", "Em"),
        ("d_minor", "Dm"),
        # min/maj token forms
        ("a_minor", "Amin"),
        ("a_minor", "Aminor"),
        ("a_minor", "A Min"),
        ("c_major", "Cmaj"),
        ("c_major", "Cmajor"),
        # seventh shorthands
        ("a_min7", "Am7"),
        ("a_min7", "Amin7"),
        ("a_min7", "A min 7"),
        ("a_maj7", "Amaj7"),
        ("a_maj7", "A maj 7"),
        ("d_min7", "Dm7"),
        ("d_maj7", "Dmaj7"),
        ("f_maj7", "Fmaj7"),
        # dominant 7
        ("g_7", "G7"),
        ("g_7", "G 7"),
        ("b_7", "B7"),
    ],
)
def test_is_correct_chord_guess_accepts_alias(chord_id: str, guess: str) -> None:
    assert is_correct_chord_guess(guess, _chord(chord_id))


@pytest.mark.parametrize(
    ("chord_id", "guess"),
    [
        # wrong root
        ("a_major", "B major"),
        ("a_major", "B"),
        ("a_minor", "Em"),
        # wrong quality
        ("a_major", "A minor"),
        ("a_minor", "A major"),
        ("a_minor", "A"),
        ("a_maj7", "A minor 7"),
        ("a_min7", "A major 7"),
        ("a_7", "A major 7"),
        ("a_7", "A major"),
        # A vs A7 — same root, quality differs
        ("a_major", "A7"),
        ("a_7", "A"),
        # nonsense
        ("a_major", ""),
        ("a_major", "   "),
        ("a_major", "not a chord"),
    ],
)
def test_is_correct_chord_guess_rejects_mismatch(chord_id: str, guess: str) -> None:
    assert not is_correct_chord_guess(guess, _chord(chord_id))


def test_every_canonical_name_matches_itself() -> None:
    for chord in CHORDS:
        assert is_correct_chord_guess(chord.name, chord), chord.name


def test_unicode_sharp_normalises_to_ascii_hash() -> None:
    # Even though we have no sharp roots in CHORDS today, the matcher must
    # treat ♯ and # as equivalent so future entries (e.g. F#m) work.
    # Exercised through the public API with a synthetic Chord — only `name`
    # participates in the comparison.
    fsharp_minor = Chord(
        id="f_sharp_minor_synth",
        name="F#m",
        strings=tuple(
            StringSpec(string_number=string_number, state=StringState.MUTED)
            for string_number in [6, 5, 4, 3, 2, 1]
        ),
    )
    assert is_correct_chord_guess("F♯m", fsharp_minor)
    assert is_correct_chord_guess("F#m", fsharp_minor)
    assert is_correct_chord_guess("F# minor", fsharp_minor)
    assert is_correct_chord_guess("F♯ minor", fsharp_minor)
    assert not is_correct_chord_guess("Fm", fsharp_minor)
