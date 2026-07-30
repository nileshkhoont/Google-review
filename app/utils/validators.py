"""Reusable validation helpers used by schemas and services."""

import re

GOOGLE_REVIEW_LINK_PATTERN = re.compile(
    r"^https:\/\/(www\.)?(g\.page|search\.google\.com|goo\.gl|maps\.google\.com|maps\.app\.goo\.gl)\/.+",
    re.IGNORECASE,
)


def is_valid_google_review_link(url: str) -> bool:
    """Loose validation that a URL looks like a Google review / maps link."""
    if not url:
        return False
    return bool(GOOGLE_REVIEW_LINK_PATTERN.match(url.strip()))


_URL_PATTERN = re.compile(r"^https?:\/\/.+", re.IGNORECASE)


def is_valid_url(url: str) -> bool:
    """Loose validation that a value is an http(s) URL."""
    if not url:
        return False
    return bool(_URL_PATTERN.match(url.strip()))
