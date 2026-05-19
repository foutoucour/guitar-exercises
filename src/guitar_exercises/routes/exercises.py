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
from guitar_exercises.domain.timings import (
    Timing,
    average_correct_ms,
    current_streak,
    parse_auto_advance,
    parse_best_streak,
    parse_timings,
    push_timing,
    serialize_timings,
    update_best_streak,
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

# Per-exercise cookies for the answer-timer history widget.
TIMINGS_COOKIE_CHORD_NOTES = "times_chord_notes"
TIMINGS_COOKIE_CHORD_NAME = "times_chord_name"
TIMINGS_COOKIE_FIND_NOTE = "times_find_note"
TIMINGS_COOKIE_NAME_NOTE = "times_name_note"

# Best-streak cookies — kept separately so the longest run survives even
# after the offending wrong answer rolls out of the timings window.
BEST_STREAK_COOKIE_CHORD_NOTES = "best_streak_chord_notes"
BEST_STREAK_COOKIE_CHORD_NAME = "best_streak_chord_name"
BEST_STREAK_COOKIE_FIND_NOTE = "best_streak_find_note"
BEST_STREAK_COOKIE_NAME_NOTE = "best_streak_name_note"

# Toggle for the 1.2s auto-advance after a correct answer. Shared across
# all exercises (one cookie, one preference). Written client-side by
# timer.js when the player ticks the checkbox.
AUTO_ADVANCE_COOKIE = "auto_advance"

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


def _set_timings_cookie(
    response: HTMLResponse,
    timings_cookie: str,
    best_streak_cookie: str,
    timings: list[Timing],
    best_streak: int,
    *,
    correct: bool,
    elapsed_ms: int,
) -> None:
    """Push one timing onto the history cookie and update best-streak.

    Writes both cookies back on ``response`` so the next page-load shows the
    refreshed history widget.
    """
    updated = push_timing(timings, correct=correct, elapsed_ms=elapsed_ms)
    response.set_cookie(
        key=timings_cookie,
        value=serialize_timings(updated),
        path="/exercises",
        httponly=True,
        samesite="lax",
    )
    new_best = update_best_streak(best_streak, current_streak(updated))
    if new_best != best_streak:
        response.set_cookie(
            key=best_streak_cookie,
            value=str(new_best),
            path="/exercises",
            httponly=True,
            samesite="lax",
        )


def _timer_context(
    timings: list[Timing],
    best_streak: int,
    *,
    exercise_path: str,
    auto_advance: bool,
) -> dict[str, object]:
    """Build the template context block the ``_timer.html`` partial consumes."""
    return {
        "timer": {
            "exercise_path": exercise_path,
            "timings": timings,
            "current_streak": current_streak(timings),
            "best_streak": best_streak,
            "average_ms": average_correct_ms(timings),
            "auto_advance": auto_advance,
        },
    }


@router.get("/chord-notes", response_class=HTMLResponse)
async def chord_notes_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_chord_notes: Annotated[str | None, Cookie(alias=RECENT_COOKIE_CHORD_NOTES)] = None,
    times_chord_notes: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_CHORD_NOTES)] = None,
    best_streak_chord_notes: Annotated[
        str | None, Cookie(alias=BEST_STREAK_COOKIE_CHORD_NOTES)
    ] = None,
    auto_advance: Annotated[str | None, Cookie(alias=AUTO_ADVANCE_COOKIE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_chord_notes)
    timings = parse_timings(times_chord_notes)
    best_streak = parse_best_streak(best_streak_chord_notes)
    chord = pick_chord(rng, exclude_keys=recent)
    svg = render_chord_svg(chord)
    response = templates.TemplateResponse(
        request,
        "exercises/chord_notes.html",
        {
            "chord": chord,
            "svg": svg,
            "notes": list(CHROMATIC),
            **_timer_context(
                timings,
                best_streak,
                exercise_path="/exercises/chord-notes",
                auto_advance=parse_auto_advance(auto_advance),
            ),
        },
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
    elapsed_ms: Annotated[int | None, Form(ge=0, le=600_000)] = None,
    final_string: Annotated[int, Form(ge=0, le=1)] = 0,
    chord_correct: Annotated[int, Form(ge=0, le=1)] = 0,
    times_chord_notes: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_CHORD_NOTES)] = None,
    best_streak_chord_notes: Annotated[
        str | None, Cookie(alias=BEST_STREAK_COOKIE_CHORD_NOTES)
    ] = None,
) -> HTMLResponse:
    chord = get_chord_by_id(chord_id)
    if chord is None:
        raise HTTPException(status_code=404, detail="chord not found")

    expected = chord.notes_by_string.get(string_number)
    if expected is None:
        raise HTTPException(status_code=400, detail="that string is muted")

    correct = is_correct_guess(guess, expected)
    response = templates.TemplateResponse(
        request,
        "exercises/_answer_feedback.html",
        {
            "string_number": string_number,
            "guess": guess,
            "expected_note": expected.value,
            "correct": correct,
            "elapsed_ms": elapsed_ms,
        },
    )
    # Chord-notes records ONE history entry per chord — only on the final
    # string. ``chord_correct`` from the client reports whether the
    # already-answered strings on this page were all correct; AND it with the
    # server-known correctness of this final string to get the chord verdict.
    if final_string == 1 and elapsed_ms is not None:
        chord_overall_correct = chord_correct == 1 and correct
        _set_timings_cookie(
            response,
            TIMINGS_COOKIE_CHORD_NOTES,
            BEST_STREAK_COOKIE_CHORD_NOTES,
            parse_timings(times_chord_notes),
            parse_best_streak(best_streak_chord_notes),
            correct=chord_overall_correct,
            elapsed_ms=elapsed_ms,
        )
    return response


@router.get("/chord-name", response_class=HTMLResponse)
async def chord_name_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_chord_name: Annotated[str | None, Cookie(alias=RECENT_COOKIE_CHORD_NAME)] = None,
    times_chord_name: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_CHORD_NAME)] = None,
    best_streak_chord_name: Annotated[
        str | None, Cookie(alias=BEST_STREAK_COOKIE_CHORD_NAME)
    ] = None,
    auto_advance: Annotated[str | None, Cookie(alias=AUTO_ADVANCE_COOKIE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_chord_name)
    timings = parse_timings(times_chord_name)
    best_streak = parse_best_streak(best_streak_chord_name)
    chord = pick_chord(rng, exclude_keys=recent)
    svg = render_chord_svg(chord, reveal_name=False)
    response = templates.TemplateResponse(
        request,
        "exercises/chord_name.html",
        {
            "chord": chord,
            "svg": svg,
            **_timer_context(
                timings,
                best_streak,
                exercise_path="/exercises/chord-name",
                auto_advance=parse_auto_advance(auto_advance),
            ),
        },
    )
    _set_recent_cookie(response, RECENT_COOKIE_CHORD_NAME, recent, chord_question_key(chord))
    return response


@router.post("/chord-name/check", response_class=HTMLResponse)
async def chord_name_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    chord_id: Annotated[str, Form()],
    guess: Annotated[str, Form(min_length=1, max_length=32)],
    elapsed_ms: Annotated[int | None, Form(ge=0, le=600_000)] = None,
    times_chord_name: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_CHORD_NAME)] = None,
    best_streak_chord_name: Annotated[
        str | None, Cookie(alias=BEST_STREAK_COOKIE_CHORD_NAME)
    ] = None,
) -> HTMLResponse:
    chord = get_chord_by_id(chord_id)
    if chord is None:
        raise HTTPException(status_code=404, detail="chord not found")

    cleaned_guess = guess.strip()
    if not cleaned_guess:
        raise HTTPException(status_code=422, detail="guess must not be blank")

    correct = is_correct_chord_guess(cleaned_guess, chord)
    response = templates.TemplateResponse(
        request,
        "exercises/_chord_name_feedback.html",
        {
            "chord_id": chord_id,
            "guess": cleaned_guess,
            "expected_name": chord.name,
            "correct": correct,
            "elapsed_ms": elapsed_ms,
        },
    )
    if elapsed_ms is not None:
        _set_timings_cookie(
            response,
            TIMINGS_COOKIE_CHORD_NAME,
            BEST_STREAK_COOKIE_CHORD_NAME,
            parse_timings(times_chord_name),
            parse_best_streak(best_streak_chord_name),
            correct=correct,
            elapsed_ms=elapsed_ms,
        )
    return response


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
    times_find_note: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_FIND_NOTE)] = None,
    best_streak_find_note: Annotated[str | None, Cookie(alias=BEST_STREAK_COOKIE_FIND_NOTE)] = None,
    auto_advance: Annotated[str | None, Cookie(alias=AUTO_ADVANCE_COOKIE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_find_note)
    timings = parse_timings(times_find_note)
    best_streak = parse_best_streak(best_streak_find_note)
    question = pick_find_note_question(rng, exclude_keys=recent)
    context = _fretboard_context(question.string_number)
    response = templates.TemplateResponse(
        request,
        "exercises/find_note.html",
        {
            **context,
            "target_note": question.target_note,
            **_timer_context(
                timings,
                best_streak,
                exercise_path="/exercises/find-note",
                auto_advance=parse_auto_advance(auto_advance),
            ),
        },
    )
    _set_recent_cookie(response, RECENT_COOKIE_FIND_NOTE, recent, find_note_question_key(question))
    return response


@router.post("/find-note/check", response_class=HTMLResponse)
async def find_note_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    string_number: Annotated[int, Form(ge=1, le=6)],
    target_note: Annotated[str, Form(min_length=1, max_length=2)],
    fret: Annotated[int, Form(ge=0, le=MAX_FRET)],
    elapsed_ms: Annotated[int | None, Form(ge=0, le=600_000)] = None,
    times_find_note: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_FIND_NOTE)] = None,
    best_streak_find_note: Annotated[str | None, Cookie(alias=BEST_STREAK_COOKIE_FIND_NOTE)] = None,
) -> HTMLResponse:
    try:
        note = Note(target_note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid target note") from exc

    correct_frets = find_frets_for_note(string_number, note)
    correct = fret in correct_frets
    user_note = note_for_string(string_number, fret) if not correct else None

    context = _fretboard_context(string_number)
    response = templates.TemplateResponse(
        request,
        "exercises/_find_note_feedback.html",
        {
            **context,
            "target_note": note,
            "correct_frets": list(correct_frets),
            "clicked_fret": fret,
            "user_note": user_note.value if user_note is not None else "",
            "correct": correct,
            "elapsed_ms": elapsed_ms,
        },
    )
    if elapsed_ms is not None:
        _set_timings_cookie(
            response,
            TIMINGS_COOKIE_FIND_NOTE,
            BEST_STREAK_COOKIE_FIND_NOTE,
            parse_timings(times_find_note),
            parse_best_streak(best_streak_find_note),
            correct=correct,
            elapsed_ms=elapsed_ms,
        )
    return response


@router.get("/name-note", response_class=HTMLResponse)
async def name_note_page(
    request: Request,
    rng: Annotated[random.Random, Depends(get_rng)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    recent_name_note: Annotated[str | None, Cookie(alias=RECENT_COOKIE_NAME_NOTE)] = None,
    times_name_note: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_NAME_NOTE)] = None,
    best_streak_name_note: Annotated[str | None, Cookie(alias=BEST_STREAK_COOKIE_NAME_NOTE)] = None,
    auto_advance: Annotated[str | None, Cookie(alias=AUTO_ADVANCE_COOKIE)] = None,
) -> HTMLResponse:
    recent = parse_recent(recent_name_note)
    timings = parse_timings(times_name_note)
    best_streak = parse_best_streak(best_streak_name_note)
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
            **_timer_context(
                timings,
                best_streak,
                exercise_path="/exercises/name-note",
                auto_advance=parse_auto_advance(auto_advance),
            ),
        },
    )
    _set_recent_cookie(response, RECENT_COOKIE_NAME_NOTE, recent, name_note_question_key(question))
    return response


@router.post("/name-note/check", response_class=HTMLResponse)
async def name_note_check(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    string_number: Annotated[int, Form(ge=1, le=6)],
    fret: Annotated[int, Form(ge=0, le=MAX_FRET)],
    guess: Annotated[str, Form(min_length=1, max_length=2)],
    elapsed_ms: Annotated[int | None, Form(ge=0, le=600_000)] = None,
    times_name_note: Annotated[str | None, Cookie(alias=TIMINGS_COOKIE_NAME_NOTE)] = None,
    best_streak_name_note: Annotated[str | None, Cookie(alias=BEST_STREAK_COOKIE_NAME_NOTE)] = None,
) -> HTMLResponse:
    expected = note_for_string(string_number, fret)
    correct = is_correct_guess(guess, expected)

    context = _fretboard_context(string_number)
    response = templates.TemplateResponse(
        request,
        "exercises/_name_note_feedback.html",
        {
            **context,
            "highlighted_fret": fret,
            "expected_note": expected,
            "guess": guess,
            "correct": correct,
            "elapsed_ms": elapsed_ms,
        },
    )
    if elapsed_ms is not None:
        _set_timings_cookie(
            response,
            TIMINGS_COOKIE_NAME_NOTE,
            BEST_STREAK_COOKIE_NAME_NOTE,
            parse_timings(times_name_note),
            parse_best_streak(best_streak_name_note),
            correct=correct,
            elapsed_ms=elapsed_ms,
        )
    return response
