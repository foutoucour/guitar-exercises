import random
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from guitar_exercises.config import Settings, get_settings
from guitar_exercises.domain.chords import (
    chord_question_key,
    get_chord_by_id,
    is_correct_chord_guess,
    pick_chord,
)
from guitar_exercises.domain.find_note import (
    MAX_FRET,
    find_frets_for_note,
    find_note_question_key,
    pick_find_note_question,
)
from guitar_exercises.domain.name_note import (
    name_note_question_key,
    pick_name_note_question,
)
from guitar_exercises.domain.notes import CHROMATIC, Note, is_correct_guess
from guitar_exercises.domain.recent import (
    parse_recent,
    push_recent,
    serialize_recent,
)
from guitar_exercises.domain.tuning import STANDARD_TUNING, note_for_string
from guitar_exercises.rendering.chord_svg import render_chord_svg
from guitar_exercises.version import get_version

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Per-exercise cookie names — each game keeps its own recent-questions
# history so progress in one game does not lock questions out of another.
RECENT_COOKIE_CHORD_NOTES = "recent_chord_notes"
RECENT_COOKIE_CHORD_NAME = "recent_chord_name"
RECENT_COOKIE_FIND_NOTE = "recent_find_note"
RECENT_COOKIE_NAME_NOTE = "recent_name_note"

_RECENT_COOKIE_MAX_AGE = 60 * 60 * 24  # 1 day


def get_rng() -> random.Random:
    return random.Random()


def get_templates(settings: Annotated[Settings, Depends(get_settings)]) -> Jinja2Templates:
    templates = Jinja2Templates(directory=settings.templates_dir)
    templates.env.globals["app_version"] = get_version()
    return templates


def _set_recent_cookie(
    response: HTMLResponse,
    cookie_name: str,
    recent: list[str],
    new_key: str,
) -> None:
    """Prepend ``new_key`` to ``recent`` and write the cookie back on ``response``."""
    response.set_cookie(
        key=cookie_name,
        value=serialize_recent(push_recent(recent, new_key)),
        max_age=_RECENT_COOKIE_MAX_AGE,
        path="/exercises",
        httponly=True,
        samesite="lax",
    )


@router.get("/chord-notes", response_class=HTMLResponse)
async def chord_notes_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_chord_notes: Annotated[str | None, Cookie(alias=RECENT_COOKIE_CHORD_NOTES)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_chord_notes)
    chord = pick_chord(rng, exclude_keys=recent)
    svg = render_chord_svg(chord)
    response = templates.TemplateResponse(
        request,
        "exercises/chord_notes.html",
        {"chord": chord, "svg": svg, "notes": list(CHROMATIC)},
    )
    _set_recent_cookie(response, RECENT_COOKIE_CHORD_NOTES, recent, chord_question_key(chord))
    return response


@router.post("/chord-notes/check", response_class=HTMLResponse)
async def chord_notes_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    chord_id: Annotated[str, Form()],
    string_number: Annotated[int, Form(ge=1, le=6)],
    guess: Annotated[str, Form(min_length=1, max_length=4)],
) -> HTMLResponse:
    chord = get_chord_by_id(chord_id)
    if chord is None:
        raise HTTPException(status_code=404, detail="chord not found")

    expected = chord.notes_by_string.get(string_number)
    if expected is None:
        raise HTTPException(status_code=400, detail="that string is muted")

    correct = is_correct_guess(guess, expected)
    return templates.TemplateResponse(
        request,
        "exercises/_answer_feedback.html",
        {
            "string_number": string_number,
            "guess": guess,
            "expected_note": expected.value,
            "correct": correct,
        },
    )


@router.get("/chord-name", response_class=HTMLResponse)
async def chord_name_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_chord_name: Annotated[str | None, Cookie(alias=RECENT_COOKIE_CHORD_NAME)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_chord_name)
    chord = pick_chord(rng, exclude_keys=recent)
    svg = render_chord_svg(chord, reveal_name=False)
    response = templates.TemplateResponse(
        request,
        "exercises/chord_name.html",
        {"chord": chord, "svg": svg},
    )
    _set_recent_cookie(response, RECENT_COOKIE_CHORD_NAME, recent, chord_question_key(chord))
    return response


@router.post("/chord-name/check", response_class=HTMLResponse)
async def chord_name_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    chord_id: Annotated[str, Form()],
    guess: Annotated[str, Form(min_length=1, max_length=32)],
) -> HTMLResponse:
    chord = get_chord_by_id(chord_id)
    if chord is None:
        raise HTTPException(status_code=404, detail="chord not found")

    cleaned_guess = guess.strip()
    if not cleaned_guess:
        raise HTTPException(status_code=422, detail="guess must not be blank")

    correct = is_correct_chord_guess(cleaned_guess, chord)
    return templates.TemplateResponse(
        request,
        "exercises/_chord_name_feedback.html",
        {
            "chord_id": chord_id,
            "guess": cleaned_guess,
            "expected_name": chord.name,
            "correct": correct,
        },
    )


def _fretboard_context(string_number: int) -> dict[str, object]:
    """Shared layout context for any exercise that renders the fretboard partial."""
    return {
        "string_number": string_number,
        "max_fret": MAX_FRET,
        "fret_range": list(range(MAX_FRET + 1)),
        "string_order": [1, 2, 3, 4, 5, 6],
        "open_notes": {s: STANDARD_TUNING[s].value for s in STANDARD_TUNING},
    }


@router.get("/find-note", response_class=HTMLResponse)
async def find_note_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_find_note: Annotated[str | None, Cookie(alias=RECENT_COOKIE_FIND_NOTE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_find_note)
    question = pick_find_note_question(rng, exclude_keys=recent)
    context = _fretboard_context(question.string_number)
    response = templates.TemplateResponse(
        request,
        "exercises/find_note.html",
        {
            **context,
            "target_note": question.target_note,
        },
    )
    _set_recent_cookie(
        response, RECENT_COOKIE_FIND_NOTE, recent, find_note_question_key(question)
    )
    return response


@router.post("/find-note/check", response_class=HTMLResponse)
async def find_note_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    string_number: Annotated[int, Form(ge=1, le=6)],
    target_note: Annotated[str, Form(min_length=1, max_length=2)],
    fret: Annotated[int, Form(ge=0, le=MAX_FRET)],
) -> HTMLResponse:
    try:
        note = Note(target_note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid target note") from exc

    correct_frets = find_frets_for_note(string_number, note)
    correct = fret in correct_frets
    user_note = note_for_string(string_number, fret) if not correct else None

    context = _fretboard_context(string_number)
    return templates.TemplateResponse(
        request,
        "exercises/_find_note_feedback.html",
        {
            **context,
            "target_note": note,
            "correct_frets": list(correct_frets),
            "clicked_fret": fret,
            "user_note": user_note.value if user_note is not None else "",
            "correct": correct,
        },
    )


@router.get("/name-note", response_class=HTMLResponse)
async def name_note_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_name_note: Annotated[str | None, Cookie(alias=RECENT_COOKIE_NAME_NOTE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_name_note)
    question = pick_name_note_question(rng, exclude_keys=recent)
    context = _fretboard_context(question.string_number)
    response = templates.TemplateResponse(
        request,
        "exercises/name_note.html",
        {
            **context,
            "highlighted_fret": question.fret,
            "expected_note": question.expected_note,
            "notes": list(CHROMATIC),
        },
    )
    _set_recent_cookie(
        response, RECENT_COOKIE_NAME_NOTE, recent, name_note_question_key(question)
    )
    return response


@router.post("/name-note/check", response_class=HTMLResponse)
async def name_note_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    string_number: Annotated[int, Form(ge=1, le=6)],
    fret: Annotated[int, Form(ge=0, le=MAX_FRET)],
    guess: Annotated[str, Form(min_length=1, max_length=2)],
) -> HTMLResponse:
    expected = note_for_string(string_number, fret)
    correct = is_correct_guess(guess, expected)

    context = _fretboard_context(string_number)
    return templates.TemplateResponse(
        request,
        "exercises/_name_note_feedback.html",
        {
            **context,
            "highlighted_fret": fret,
            "expected_note": expected,
            "guess": guess,
            "correct": correct,
        },
    )
