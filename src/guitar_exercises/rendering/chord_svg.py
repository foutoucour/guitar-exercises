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

_STRING_SPACING = (_GRID_RIGHT - _GRID_LEFT) / (_STRING_COUNT - 1)
_GRID_BOTTOM = _NUT_Y + _FRET_SPACING * _FRET_ROWS


def _string_x(index: int) -> float:
    """`index` is 0..5 where 0 = string 6 (low E, leftmost)."""
    return _GRID_LEFT + index * _STRING_SPACING


def _fret_dot_y(fret: int) -> float:
    return _NUT_Y + _FRET_SPACING * fret - _FRET_SPACING / 2


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


def _render_marker(spec: StringSpec, index: int) -> str:
    x = _string_x(index)
    if spec.state is StringState.MUTED:
        return (
            f'<text x="{x:.1f}" y="{_MARKER_Y}" class="chord-marker chord-marker-muted" '
            f'text-anchor="middle">X</text>'
        )
    if spec.state is StringState.OPEN:
        return (
            f'<circle cx="{x:.1f}" cy="{_MARKER_Y - 4}" r="5" '
            f'class="chord-marker-open" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        )
    return ""


def _render_dot(spec: StringSpec, index: int) -> str:
    if spec.state is not StringState.FRETTED or spec.fret is None:
        return ""
    x = _string_x(index)
    y = _fret_dot_y(spec.fret)
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


def render_chord_svg(chord: Chord, *, reveal_name: bool = True) -> str:
    title = escape(chord.name) if reveal_name else "Chord diagram"
    desc = escape(_describe_chord(chord, reveal_name=reveal_name))

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
    nut = (
        f'<line x1="{_GRID_LEFT - 1}" y1="{_NUT_Y}" '
        f'x2="{_GRID_RIGHT + 1}" y2="{_NUT_Y}" '
        f'stroke="currentColor" stroke-width="4"/>'
    )

    markers = [_render_marker(spec, i) for i, spec in enumerate(chord.strings)]
    dots = [_render_dot(spec, i) for i, spec in enumerate(chord.strings)]
    fingers = [_render_finger(spec, i) for i, spec in enumerate(chord.strings)]

    body = "\n  ".join(
        line for line in (*string_lines, *fret_lines, nut, *markers, *dots, *fingers) if line
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
