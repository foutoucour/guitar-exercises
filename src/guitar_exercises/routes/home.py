from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from guitar_exercises.config import Settings, get_settings
from guitar_exercises.version import get_version

router = APIRouter()


class ExerciseListing(BaseModel):
    slug: str
    name: str
    description: str
    url: str
    icon: str
    icon_label: str


EXERCISES: list[ExerciseListing] = [
    ExerciseListing(
        slug="chord-notes",
        name="Chord Note Recognition",
        description=(
            "Name the note produced by each string of an open-position chord. "
            "Immediate per-string feedback."
        ),
        url="/exercises/chord-notes",
        icon="🎵",
        icon_label="Musical note — name the notes of the chord",
    ),
    ExerciseListing(
        slug="chord-name",
        name="Chord Name Recognition",
        description=(
            "Identify the chord name from its fretboard shape. "
            "Free-text input accepts aliases (e.g. Am, A minor, Aminor)."
        ),
        url="/exercises/chord-name",
        icon="🎸",
        icon_label="Guitar — name the chord from its shape",
    ),
    ExerciseListing(
        slug="find-note",
        name="Find the Note",
        description=(
            "A string and a target note are given. "
            "Click the fret on the fretboard where that note lives."
        ),
        url="/exercises/find-note",
        icon="🎯",
        icon_label="Target — find the note on the fretboard",
    ),
]


def get_templates(settings: Annotated[Settings, Depends(get_settings)]) -> Jinja2Templates:
    templates = Jinja2Templates(directory=settings.templates_dir)
    templates.env.globals["app_version"] = get_version()
    return templates


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "home.html",
        {"exercises": EXERCISES},
    )
