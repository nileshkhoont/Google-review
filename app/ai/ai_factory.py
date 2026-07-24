"""
Factory for selecting the configured AI provider.
"""

from app.config import settings
from app.ai.gemini_client import GeminiClient
from app.ai.groq_client import GroqClient


def get_ai_client():
    """
    Return the configured AI client.

    Supported providers:
    - gemini
    - groq
    """

    provider = settings.ai_provider.lower()

    if provider == "groq":
        return GroqClient()

    if provider == "gemini":
        return GeminiClient()