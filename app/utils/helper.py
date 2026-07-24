"""Small shared helper functions used across the codebase."""

import re
import uuid
from datetime import datetime, timezone


def new_id() -> str:
    """Generate a unique string id (used for Mongo _id fields)."""
    return uuid.uuid4().hex


def utc_now() -> datetime:
    """Current UTC timestamp, timezone-aware."""
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    """Turn a business name into a URL-safe slug, e.g. 'My Cafe!' -> 'my-cafe'."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if not text:
        text = uuid.uuid4().hex[:8]
    return f"{text}-{uuid.uuid4().hex[:6]}"


def serialize_doc(doc: dict) -> dict:
    """
    Convert a raw MongoDB document into an API-safe dict:
    - renames `_id` to `id`
    - strips internal/sensitive fields (e.g. password_hash)
    """
    if not doc:
        return doc
    doc = dict(doc)
    doc["id"] = doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc
