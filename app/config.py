"""Application configuration helpers.

This module keeps environment-dependent settings in one place so the rest of the
application can stay simple and focused on its responsibilities.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Settings:
    """Small settings container for the FastAPI app."""

    app_name: str = "Assessment Recommender API"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for the running application."""

    return Settings()
