from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from guitar_exercises.config import Settings, get_settings

router = APIRouter()


class ExerciseListing(BaseModel):
    slug: str
    name: str
    description: str
    url: str


EXERCISES: list[ExerciseListing] = [
    ExerciseListing(
        slug="chord-notes",
        name="Chord Note Recognition",
        description=(
            "Name the note produced by each string of an open-position chord. "
            "Immediate per-string feedback."
        ),
        url="/exercises/chord-notes",
    ),
]


def get_templates(settings: Annotated[Settings, Depends(get_settings)]) -> Jinja2Templates:
    return Jinja2Templates(directory=settings.templates_dir)


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
