"""Represents the shape of a document in the `reviews` collection.

Storing generated reviews is optional (per project requirements) but is
useful for basic analytics later (e.g. counting reviews generated per
business), so it's kept as a lightweight history log.
"""

from typing import Any

from app.utils.helper import new_id, utc_now


def build_review_document(business_id: str, review_text: str) -> dict[str, Any]:
    return {
        "_id": new_id(),
        "business_id": business_id,
        "review_text": review_text,
        "created_at": utc_now(),
    }
