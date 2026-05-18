from xml.sax.saxutils import escape

from guitar_exercises.domain.chords import Chord, StringSpec, StringState

_VIEWBOX_WIDTH = 180
_VIEWBOX_HEIGHT = 240
_GRID_LEFT = 20
_GRID_RIGHT = 160
_STRING_COUNT = 6
_FRET_ROWS = 5
_NUT_Y = 40
_FRET_SPACING = 30
_MARKER_Y = 22
_FINGER_Y = 215
_DOT_RADIUS = 7
_FRET_LABEL_X = _GRID_LEFT - 5

_STRING_SPACING = (_GRID_RIGHT - _GRID_LEFT) / (_STRING_COUNT - 1)
_GRID_BOTTOM = _NUT_Y + _FRET_SPACING * _FRET_ROWS


def _string_x(index: int) -> float:
    """`index` is 0..5 where 0 = string 6 (low E, leftmost)."""
    return _GRID_LEFT + index * _STRING_SPACING


def _fret_dot_y(fret: int, start_fret: int) -> float:
    relative = fret - start_fret + 1
    return _NUT_Y + _FRET_SPACING * relative - _FRET_SPACING / 2


def _compute_start_fret(chord: Chord) -> int:
    """Lowest visible fret in the diagram. Returns 1 when the shape fits in the open window.

    Open strings always anchor the diagram to fret 1 (the nut). For fully-fretted
    shapes the window slides to start at the lowest fretted note, showing an 'Nfr'
    label so the player knows where on the neck to position their hand.
    """
    has_open = any(spec.state is StringState.OPEN for spec in chord.strings)
    if has_open:
        return 1
    fretted = [
        spec.fret
        for spec in chord.strings
        if spec.state is StringState.FRETTED and spec.fret is not None
    ]
    if not fretted:
        return 1
    return min(fretted)


def _describe_chord(chord: Chord, *, reveal_name: bool) -> str:
    parts: list[str] = []
    for spec in chord.strings:
        label = f"{spec.string_number} string"
        match spec.state:
            case StringState.MUTED:
                parts.append(f"{label} muted")
            case StringState.OPEN:
                if reveal_name:
                    parts.append(f"{label} open {spec.note.value}")
                else:
                    parts.append(f"{label} open")
            case StringState.FRETTED:
                if reveal_name:
                    parts.append(f"{label} fret {spec.fret} {spec.note.value}")
                else:
                    parts.append(f"{label} fret {spec.fret}")
    prefix = f"Chord diagram for {chord.name}" if reveal_name else "Chord diagram"
    return f"{prefix}. " + ". ".join(parts) + "."


def _render_marker(spec: StringSpec, index: int, start_fret: int) -> str:
    x = _string_x(index)
    if spec.state is StringState.MUTED:
        return (
            f'<text x="{x:.1f}" y="{_MARKER_Y}" class="chord-marker chord-marker-muted" '
            f'text-anchor="middle">X</text>'
        )
    if spec.state is StringState.OPEN and start_fret == 1:
        return (
            f'<circle cx="{x:.1f}" cy="{_MARKER_Y - 4}" r="5" '
            f'class="chord-marker-open" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        )
    return ""


def _render_dot(spec: StringSpec, index: int, start_fret: int) -> str:
    if spec.state is not StringState.FRETTED or spec.fret is None:
        return ""
    x = _string_x(index)
    y = _fret_dot_y(spec.fret, start_fret)
    return (
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{_DOT_RADIUS}" '
        f'class="chord-dot" fill="currentColor"/>'
    )


def _render_finger(spec: StringSpec, index: int) -> str:
    if spec.state is not StringState.FRETTED or spec.finger is None:
        return ""
    x = _string_x(index)
    return (
        f'<text x="{x:.1f}" y="{_FINGER_Y}" class="chord-finger" '
        f'text-anchor="middle">{spec.finger}</text>'
    )


def _find_barres(chord: Chord) -> list[tuple[int, int, int]]:
    """Group fretted strings that share the same finger at the same fret.

    A barre is two-or-more strings pressed by the same finger at the same fret;
    we return one (fret, leftmost_string_index, rightmost_string_index) tuple per
    such group so the renderer can draw a single capsule that visually spans the
    contacted strings — even when intermediate strings are fretted higher up by
    other fingers, which is the normal case for E-shape and A-shape barres.
    """
    by_key: dict[tuple[int, int], list[int]] = {}
    for index, spec in enumerate(chord.strings):
        if (
            spec.state is StringState.FRETTED
            and spec.fret is not None
            and spec.finger is not None
        ):
            by_key.setdefault((spec.finger, spec.fret), []).append(index)
    return [
        (fret, min(indices), max(indices))
        for (_finger, fret), indices in by_key.items()
        if len(indices) >= 2
    ]


def _render_barre(fret: int, left_index: int, right_index: int, start_fret: int) -> str:
    x1 = _string_x(left_index)
    x2 = _string_x(right_index)
    y = _fret_dot_y(fret, start_fret)
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
        f'class="chord-barre" stroke="currentColor" '
        f'stroke-width="{2 * _DOT_RADIUS}" stroke-linecap="round"/>'
    )


def _render_fret_label(start_fret: int) -> str:
    if start_fret == 1:
        return ""
    y = _NUT_Y + _FRET_SPACING / 2 + 4
    return (
        f'<text x="{_FRET_LABEL_X}" y="{y:.1f}" class="chord-fret-label" '
        f'text-anchor="end">{start_fret}fr</text>'
    )


def render_chord_svg(chord: Chord, *, reveal_name: bool = True) -> str:
    title = escape(chord.name) if reveal_name else "Chord diagram"
    desc = escape(_describe_chord(chord, reveal_name=reveal_name))
    start_fret = _compute_start_fret(chord)

    string_lines = [
        f'<line x1="{_string_x(i):.1f}" y1="{_NUT_Y}" '
        f'x2="{_string_x(i):.1f}" y2="{_GRID_BOTTOM}" '
        f'stroke="currentColor" stroke-width="1.2"/>'
        for i in range(_STRING_COUNT)
    ]
    fret_lines = [
        f'<line x1="{_GRID_LEFT}" y1="{_NUT_Y + _FRET_SPACING * (row + 1):.1f}" '
        f'x2="{_GRID_RIGHT}" y2="{_NUT_Y + _FRET_SPACING * (row + 1):.1f}" '
        f'stroke="currentColor" stroke-width="1.2"/>'
        for row in range(_FRET_ROWS)
    ]
    nut_stroke_width = 4 if start_fret == 1 else 1.2
    nut = (
        f'<line x1="{_GRID_LEFT - 1}" y1="{_NUT_Y}" '
        f'x2="{_GRID_RIGHT + 1}" y2="{_NUT_Y}" '
        f'stroke="currentColor" stroke-width="{nut_stroke_width}"/>'
    )

    markers = [_render_marker(spec, i, start_fret) for i, spec in enumerate(chord.strings)]
    barres = [
        _render_barre(fret, left, right, start_fret)
        for fret, left, right in _find_barres(chord)
    ]
    dots = [_render_dot(spec, i, start_fret) for i, spec in enumerate(chord.strings)]
    fingers = [_render_finger(spec, i) for i, spec in enumerate(chord.strings)]
    fret_label = _render_fret_label(start_fret)

    body = "\n  ".join(
        line
        for line in (
            *string_lines,
            *fret_lines,
            nut,
            *markers,
            *barres,
            *dots,
            *fingers,
            fret_label,
        )
        if line
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_VIEWBOX_WIDTH} {_VIEWBOX_HEIGHT}" '
        f'class="chord-diagram" role="img" aria-labelledby="chord-title chord-desc">\n'
        f"  <title id=\"chord-title\">{title}</title>\n"
        f"  <desc id=\"chord-desc\">{desc}</desc>\n"
        f"  {body}\n"
        f"</svg>"
    )
