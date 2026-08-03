"""Represents the shape of a document in the `click_logs` collection."""

from typing import Any

from app.utils.helper import new_id, utc_now


def build_click_log_document(
    business_id: str,
    business_name: str,
    page: str,
    action: str,
) -> dict[str, Any]:
    return {
        "_id": new_id(),
        "business_id": business_id,
        "business_name": business_name,
        "page": page,
        "action": action,
        "created_at": utc_now(),
    }
