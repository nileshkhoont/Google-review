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


_HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def is_valid_hex_color(value: str) -> bool:
    """Whether a value is a 6-digit hex color like '#4f46e5'."""
    if not value:
        return False
    return bool(_HEX_COLOR_PATTERN.match(value.strip()))
