"""Calls Gemini through GeminiClient and returns a cleaned review string."""
import json
import re
from app.config import settings
from app.ai.ai_factory import get_ai_client
from app.ai.prompt_builder import  (build_review_prompt,build_review_aspects_prompt, build_translation_prompt,)
from app.utils.logger import logger


# Gemini often wraps its JSON output in a Markdown code fence (```json ... ```
# or plain ``` ... ```) despite being asked not to. json.loads() chokes on the
# fence markers even though the JSON inside is valid, so it must be stripped
# before parsing.
_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """Remove a surrounding Markdown code fence, if present; otherwise
    return the (whitespace-trimmed) text unchanged."""
    stripped = (text or "").strip()
    match = _CODE_FENCE_PATTERN.match(stripped)
    return match.group(1).strip() if match else stripped


def _clean_review_text(raw_text: str) -> str:
    """
    Clean the raw Gemini response.

    Removes surrounding quotes, markdown, and extra whitespace while
    preserving the actual review content.
    """
    text = (raw_text or "").strip()

    # Remove surrounding quotes
    text = text.strip('"').strip("'")

    # Remove markdown formatting
    text = (
        text.replace("**", "")
        .replace("*", "")
        .replace("__", "")
        .replace("_", "")
        .replace("`", "")
    )

    # Normalize whitespace
    text = " ".join(text.split())

    return text

def _extract_reviews(raw_text: str) -> list[str]:
    """
    Extract multiple reviews returned as JSON.

    Expected format:

    {
        "reviews": [
            {"review": "..."},
            {"review": "..."}
        ]
    }
    """

    try:
        data = json.loads(_strip_code_fences(raw_text))
    except Exception as exc:
        logger.warning(
            "Review JSON parsing failed (%s) | raw response (first 200 chars): %r",
            exc, (raw_text or "")[:200],
        )
        return []

    reviews = []

    for item in data.get("reviews", []):
        review = item.get("review", "").strip()

        if review:
            reviews.append(_clean_review_text(review))

    logger.info("Review JSON parsing succeeded, extracted %d review(s).", len(reviews))
    return reviews


def _extract_translated_reviews(raw_text: str) -> list[str]:
    """
    Extract translated reviews returned as JSON.

    Expected format:

    {
        "reviews": [
            {"review": "..."},
            {"review": "..."}
        ]
    }
    """

    try:
        data = json.loads(_strip_code_fences(raw_text))
    except Exception as exc:
        logger.warning(
            "Translated review JSON parsing failed (%s) | raw response (first 200 chars): %r",
            exc, (raw_text or "")[:200],
        )
        return []

    translated_reviews = []

    for item in data.get("reviews", []):
        review = item.get("review", "").strip()

        if review:
            translated_reviews.append(
                _clean_review_text(review)
            )

    logger.info(
        "Translated review JSON parsing succeeded, extracted %d review(s).",
        len(translated_reviews),
    )
    return translated_reviews


def _looks_like_json(text: str) -> bool:
    """
    Heuristic check for raw JSON leaking through as a "review".

    The prompt always asks Gemini to wrap reviews in a JSON object, so any
    genuine plain-text review should never start with '{' or '['. This is
    used to detect the case where json.loads() failed (malformed/truncated
    JSON) and the fallback text-cleaning left the raw JSON structure intact.
    """
    stripped = (text or "").strip()
    if not stripped:
        return True
    return stripped[0] in "{["


class ReviewGenerator:
    """
    Generates customer reviews using Gemini.

    Responsibilities:
    - Normalize rating according to business rules.
    - Build the prompt.
    - Call Gemini.
    - Clean the generated review.
    """

    def __init__(self, ai_client=None):
        self.ai_client = ai_client or get_ai_client()

    async def generate(
        self,
        business_name: str,
        service_type: str,
        business_description: str | None = None,
        rating: int | None = None,
        selected_review_aspects: list[str] | None = None,
    ) -> str:
        """
        Generate a review.

        Rating Rules
        ------------
        5 → Prompt uses 5-star tone.
        4 → Prompt uses 4-star tone.
        3 → Prompt uses 3-star tone.
        2 → Prompt uses 3-star tone.
        1 → Prompt uses 3-star tone.

        The customer's selected rating can still be stored separately if
        required by the application. This normalization only affects the
        AI prompt.
        """

        # Normalize rating for prompt generation
        effective_rating: int | None = None

        if rating is not None:
            try:
                effective_rating = max(3, min(int(rating), 5))
            except (TypeError, ValueError):
                effective_rating = 5

        prompt = build_review_prompt(
            business_name=business_name,
            service_type=service_type,
            business_description=business_description,
            rating=effective_rating,
            selected_review_aspects=selected_review_aspects,
            review_count=settings.review_variants,
        )

        max_attempts = settings.review_generation_max_attempts
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                raw_text = await self.ai_client.generate_text(prompt)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "AI call failed on attempt %s/%s: %s",
                    attempt, max_attempts, exc,
                )
                continue

            logger.debug("Raw AI response (attempt %s/%s): %s", attempt, max_attempts, raw_text)

            reviews = _extract_reviews(raw_text)

            if not reviews and not _looks_like_json(raw_text):
                reviews = [_clean_review_text(raw_text)]

            if reviews and not any(_looks_like_json(review) for review in reviews):
                logger.debug("Extracted reviews (attempt %s/%s): %s", attempt, max_attempts, reviews)
                return reviews

            logger.warning(
                "AI response was not usable plain text on attempt %s/%s, retrying.",
                attempt, max_attempts,
            )

        raise RuntimeError(
            "AI review generation did not return usable plain-text reviews "
            f"after {max_attempts} attempts."
        ) from last_error

    async def generate_review_aspects(
        self,
        service_type: str,
        business_description: str | None = None,
    ) -> list[str]:
        """
        Generate AI suggested review aspects.
        """

        prompt = build_review_aspects_prompt(
            service_type=service_type,
            business_description=business_description,
        )

        raw_text = await self.ai_client.generate_text(prompt)

        try:
            aspects = []
            for line in raw_text.splitlines():
                line = line.strip()
                if not line:
                   continue
                # Remove bullets or numbering if Gemini adds them
                line = line.lstrip("-•* ").strip()
                if "." in line and line.split(".", 1)[0].isdigit():
                   line = line.split(".", 1)[1].strip()
                if line.lower() not in [a.lower() for a in aspects]:
                   aspects.append(line)
            return aspects[:12]

        except Exception:
            return []



    async def _translate_language(
        self,
        reviews: list[str],
        language: str,
    ) -> list[str]:
        """
        Translate all reviews into a single language, retrying if the AI
        response doesn't parse into exactly one translation per review.

        Some languages (notably Roman Gujarati) are far less represented
        in the model's training data than others (Roman Hindi), so they
        fail to produce complete/valid JSON more often. Retrying the same
        prompt usually recovers a clean response.
        """
        prompt = build_translation_prompt(reviews=reviews, language=language)
        max_attempts = settings.translation_max_attempts
        last_raw: str | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                raw_text = await self.ai_client.generate_text(prompt)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "%s translation call failed on attempt %s/%s: %s",
                    language, attempt, max_attempts, exc,
                )
                continue

            last_raw = raw_text
            translated = _extract_translated_reviews(raw_text)

            if len(translated) == len(reviews):
                return translated

            logger.warning(
                "%s translation returned %s/%s reviews on attempt %s/%s. Raw response: %s",
                language, len(translated), len(reviews), attempt, max_attempts, raw_text,
            )

        logger.error(
            "%s translation did not return a complete set of reviews after %s attempts. "
            "Missing reviews will fall back to the original English text. Last raw response: %s",
            language, max_attempts, last_raw,
        )
        return _extract_translated_reviews(last_raw) if last_raw else []

    _LANGUAGE_NAMES = {
        "gu": "Gujarati",
        "hi": "Hindi",
    }

    async def translate_single_review(self, text: str, language_code: str) -> str:
        """
        Translate one review into one language, on demand (called when the
        customer switches the language tab for the review currently on
        screen, rather than eagerly translating every generated variant).
        """
        language_name = self._LANGUAGE_NAMES.get(language_code)
        if not language_name:
            raise ValueError(f"Unsupported language code: {language_code}")

        translated = await self._translate_language([text], language_name)
        return translated[0] if translated else text
