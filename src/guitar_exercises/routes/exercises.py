import random
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from guitar_exercises.config import Settings, get_settings
from guitar_exercises.domain.chords import get_chord_by_id, pick_chord
from guitar_exercises.domain.notes import CHROMATIC, Note, is_correct_guess
from guitar_exercises.rendering.chord_svg import render_chord_svg

router = APIRouter(prefix="/exercises", tags=["exercises"])


def get_rng() -> random.Random:
    return random.Random()


def get_templates(settings: Annotated[Settings, Depends(get_settings)]) -> Jinja2Templates:
    return Jinja2Templates(directory=settings.templates_dir)


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
