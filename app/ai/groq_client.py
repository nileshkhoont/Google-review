"""
Groq client used for AI text generation.

This class mirrors the interface of GeminiClient so the rest
of the application can switch AI providers without changing
business logic.
"""

from groq import AsyncGroq

from app.config import settings


class GroqClient:
    """
    Wrapper around the Groq Chat Completions API.
    """

    def __init__(self):
        self.client = AsyncGroq(
            api_key=settings.groq_api_key
        )

        self.model = settings.groq_model

    async def generate_text(self, prompt: str) -> str:
        """
        Generate text from the configured Groq model.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=1.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return (
            response.choices[0]
            .message.content
            .strip()
        )