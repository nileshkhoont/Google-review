"""
Centralized application configuration.

All environment-dependent values are loaded from the .env file using
Pydantic Settings. Nothing in the rest of the codebase should read
os.environ directly -- everything goes through `settings`.
"""

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

# Matches GEMINI_API_KEY_1, GEMINI_API_KEY_2, ... GEMINI_API_KEY_42, etc.
# Keys are discovered rather than declared, so adding/removing/reordering
# them in .env never requires touching this file.
_GEMINI_KEY_PATTERN = re.compile(r"^GEMINI_API_KEY_(\d+)$")



class Settings(BaseSettings):
    # App
    app_name: str = "ReviewQR-AI"
    app_env: str = "development"
    app_debug: bool = True
    base_url: str = "http://localhost:8000"

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "reviewqr_ai"

    # JWT
    jwt_secret_key: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Admin login — this app has exactly one account, defined here rather
    # than in a database. Set these in .env; login fails closed if unset.
    admin_email: str = ""
    admin_password: str = ""

    # QR codes
    qr_code_dir: str = "app/static/qr_codes"
    
    # Review Generation
    review_variants: int = 2

    # Max attempts to get a usable plain-text review from the AI provider
    # before giving up (guards against the AI returning raw/broken JSON).
    review_generation_max_attempts: int = 3

    # Max attempts per language to get a complete set of translated
    # reviews back from the AI provider (guards against incomplete/
    # malformed responses, which happen more often for less-represented
    # languages like Roman Gujarati).
    translation_max_attempts: int = 3

    # Number of random business aspects used when
    # the customer has not selected any manually.
    random_aspects_count: int = 2
    
    
    # ---------------------------------------------------------
    # AI Provider
    # ---------------------------------------------------------

    # Which AI provider to use:
    # gemini | groq
    ai_provider: str = "gemini"

    # ---------------------------------------------------------
    # Gemini
    # ---------------------------------------------------------

    # Must be a model supported for generateContent by the current Gemini API.
    # Using the server-side discovered working model.
    # NOTE: GeminiClient expects a model *name* (google.generativeai will prefix with "models/" internally).
    gemini_model: str = "gemini-flash-latest"

    @property
    def gemini_key_list(self) -> list[str]:
        """
        All configured Gemini API keys, in try-order.

        Keys are discovered from any GEMINI_API_KEY_<n> variable (in .env or
        the real environment) rather than declared as fixed fields, so
        adding, removing, reordering, or disabling (by leaving the value
        empty) a key only ever requires editing .env.
        """
        # os.environ takes precedence over .env, matching how the rest of
        # Settings resolves values, and lets keys be overridden at the
        # process level without touching the file.
        merged = {**dotenv_values(self._env_path), **os.environ}

        numbered: list[tuple[int, str]] = []
        for name, value in merged.items():
            match = _GEMINI_KEY_PATTERN.match(name.upper())
            if match and value and value.strip():
                numbered.append((int(match.group(1)), value.strip()))

        numbered.sort(key=lambda pair: pair[0])
        return [value for _, value in numbered]

    # ---------------------------------------------------------
    # Groq
    # ---------------------------------------------------------

    groq_api_key: str = ""
    # Recommended model for review generation.
    # You can change this later without changing code.
    groq_model: str = "llama-3.3-70b-versatile"

    # Load .env reliably regardless of the working directory.
    # This file lives at: <repo_root>/app/config.py
    # so the repo root is one level up.
    _repo_root = Path(__file__).resolve().parent.parent
    _env_path = _repo_root / ".env"

    # extra="ignore": GEMINI_API_KEY_<n> variables are discovered dynamically
    # (see gemini_key_list below) rather than declared as fields, so they
    # must not trip pydantic-settings' default "extra fields forbidden".
    model_config = SettingsConfigDict(
        env_file=str(_env_path), env_file_encoding="utf-8", extra="ignore"
    )



@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


settings = get_settings()
