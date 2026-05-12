from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from guitar_exercises.config import Settings, get_settings
from guitar_exercises.logging import configure_logging
from guitar_exercises.routes import exercises, health, home


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(title="Guitar Exercises", version="0.1.0")
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    app.include_router(health.router)
    app.include_router(home.router)
    app.include_router(exercises.router)

    logger.info(f"App created (debug={settings.debug})")
    return app


app = create_app()
