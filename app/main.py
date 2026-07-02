"""FastAPI application entrypoint for the assessment recommender service."""

from fastapi import FastAPI

from app.config import get_settings
from app.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Conversational SHL assessment recommender API.",
    )

    app.include_router(router)

    return app


app = create_app()
