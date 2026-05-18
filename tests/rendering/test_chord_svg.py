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
            StringSpec(string_number=n, state=StringState.OPEN)
            if n in {6, 5, 4, 3, 2, 1}
            else StringSpec(string_number=n, state=StringState.MUTED)
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


def test_render_open_window_omits_fret_label() -> None:
    chord = get_chord_by_id("a_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-fret-label" not in svg


def test_render_open_chord_with_high_frets_omits_fret_label() -> None:
    """Open chords (e.g. G major, frets 2 and 3) must not get an 'Nfr' label even though
    their lowest fretted note is above fret 1 — the open strings anchor the diagram to fret 1."""
    chord = get_chord_by_id("g_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-fret-label" not in svg


def test_render_closed_shape_on_second_fret_shows_fret_label() -> None:
    """Fully-fretted shapes (no open strings) with lowest fret > 1 should display an 'Nfr'
    marker — e.g. B major barres from fret 2."""
    chord = get_chord_by_id("b_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-fret-label" in svg
    assert ">2fr<" in svg


def test_render_higher_position_shape_includes_fret_label() -> None:
    """Shapes whose lowest fret is above the open window should display an 'Nfr' marker
    so the player knows where on the neck to position their hand."""
    chord = get_chord_by_id("a_major_e_shape")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-fret-label" in svg
    assert ">5fr<" in svg


def test_render_barre_chord_includes_barre_line() -> None:
    """E-shape barre (F major) has finger 1 pressing strings 6, 2, 1 at fret 1 —
    the diagram should render one capsule-shaped bar across those strings."""
    chord = get_chord_by_id("f_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count('class="chord-barre"') == 1


def test_render_open_chord_without_shared_finger_has_no_barre() -> None:
    chord = get_chord_by_id("c_major")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-barre" not in svg


def test_render_open_dmaj7_renders_existing_partial_barre() -> None:
    """D maj7 (x,x,0,2,2,2 with fingers 1,1,1) is a 3-string partial barre with finger 1
    at fret 2 — already in the catalog before the CAGED additions, now visualised properly."""
    chord = get_chord_by_id("d_maj7")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert svg.count('class="chord-barre"') == 1


def test_render_higher_position_shape_hides_open_string_markers() -> None:
    """When the diagram is shifted up the neck, an unfretted string is muted, not 'open',
    so we must not render the open-string circle markers."""
    chord = get_chord_by_id("a_major_e_shape")
    assert chord is not None
    svg = render_chord_svg(chord)
    assert "chord-marker-open" not in svg
