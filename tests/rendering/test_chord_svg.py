from guitar_exercises.domain.chords import CHORDS, Chord, StringSpec, StringState, get_chord_by_id
from guitar_exercises.rendering.chord_svg import render_chord_svg


def _count_fretted(chord: Chord) -> int:
    return sum(1 for s in chord.strings if s.state is StringState.FRETTED)


def _count_muted(chord: Chord) -> int:
    return sum(1 for s in chord.strings if s.state is StringState.MUTED)


def _count_open(chord: Chord) -> int:
    return sum(1 for s in chord.strings if s.state is StringState.OPEN)


def test_render_starts_with_svg_tag() -> None:
    chord = get_chord_by_id("a_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")


def test_render_includes_chord_name_in_title() -> None:
    chord = get_chord_by_id("c_maj7")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "<title" in svg
    assert "C major 7" in svg


def test_render_marks_muted_strings_with_X() -> None:
    chord = get_chord_by_id("a_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count(">X<") == _count_muted(chord)


def test_render_marks_open_strings_with_circle() -> None:
    chord = get_chord_by_id("e_minor")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count("chord-marker-open") == _count_open(chord)


def test_render_draws_one_dot_per_fretted_string() -> None:
    chord = get_chord_by_id("b_7")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count('class="chord-dot"') == _count_fretted(chord)


def test_render_includes_finger_numbers() -> None:
    chord = get_chord_by_id("a_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count('class="chord-finger"') == _count_fretted(chord)


def test_render_escapes_chord_name() -> None:
    chord = Chord(
        id="weird",
        name="<script>alert(1)</script>",
        strings=tuple(
            StringSpec(string_number=n, state=StringState.OPEN) if n in {6, 5, 4, 3, 2, 1} else StringSpec(string_number=n, state=StringState.MUTED)
            for n in (6, 5, 4, 3, 2, 1)
        ),
    )
    svg = render_chord_svg(chord)
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_render_every_chord_in_catalog() -> None:
    for chord in CHORDS:
        svg = render_chord_svg(chord)
        assert svg.startswith("<svg")
        assert chord.name in svg
