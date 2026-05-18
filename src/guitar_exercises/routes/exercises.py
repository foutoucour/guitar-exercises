import random
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from guitar_exercises.config import Settings, get_settings
from guitar_exercises.domain.chords import (
    get_chord_by_id,
    is_correct_chord_guess,
    pick_chord,
)
from guitar_exercises.domain.find_note import (
    MAX_FRET,
    find_frets_for_note,
    pick_find_note_question,
)
from guitar_exercises.domain.name_note import pick_name_note_question
from guitar_exercises.domain.notes import CHROMATIC, Note, is_correct_guess
from guitar_exercises.domain.tuning import STANDARD_TUNING, note_for_string
from guitar_exercises.rendering.chord_svg import render_chord_svg
from guitar_exercises.version import get_version

router = APIRouter(prefix="/exercises", tags=["exercises"])


def get_rng() -> random.Random:
    return random.Random()


def get_templates(settings: Annotated[Settings, Depends(get_settings)]) -> Jinja2Templates:
    templates = Jinja2Templates(directory=settings.templates_dir)
    templates.env.globals["app_version"] = get_version()
    return templates


@router.get("/chord-notes", response_class=HTMLResponse)
async def chord_notes_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
) -> HTMLResponse:
    chord = pick_chord(rng)
    svg = render_chord_svg(chord)
    return templates.TemplateResponse(
        request,
        "exercises/chord_notes.html",
        {"chord": chord, "svg": svg, "notes": list(CHROMATIC)},
    )


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
) -> HTMLResponse:
    chord = pick_chord(rng)
    svg = render_chord_svg(chord, reveal_name=False)
    return templates.TemplateResponse(
        request,
        "exercises/chord_name.html",
        {"chord": chord, "svg": svg},
    )


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
) -> HTMLResponse:
    question = pick_find_note_question(rng)
    context = _fretboard_context(question.string_number)
    return templates.TemplateResponse(
        request,
        "exercises/find_note.html",
        {
            **context,
            "target_note": question.target_note,
            "correct_frets": list(question.correct_frets),
        },
    )


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
    user_note = note_for_string(string_number, fret)

    context = _fretboard_context(string_number)
    return templates.TemplateResponse(
        request,
        "exercises/_find_note_feedback.html",
        {
            **context,
            "target_note": note,
            "correct_frets": list(correct_frets),
            "clicked_fret": fret,
            "user_note": user_note.value,
            "correct": correct,
        },
    )


@router.get("/name-note", response_class=HTMLResponse)
async def name_note_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
) -> HTMLResponse:
    question = pick_name_note_question(rng)
    context = _fretboard_context(question.string_number)
    return templates.TemplateResponse(
        request,
        "exercises/name_note.html",
        {
            **context,
            "highlighted_fret": question.fret,
            "expected_note": question.expected_note,
            "notes": list(CHROMATIC),
        },
    )


@router.post("/name-note/check", response_class=HTMLResponse)
async def name_note_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    string_number: Annotated[int, Form(ge=1, le=6)],
    fret: Annotated[int, Form(ge=0, le=MAX_FRET)],
    guess: Annotated[str, Form(min_length=1, max_length=4)],
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
