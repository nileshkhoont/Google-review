"""Represents the shape of a document in the `qrcodes` collection."""

from typing import Any

from app.utils.helper import new_id, utc_now


def build_qr_document(
    business_id: str,
    file_path: str,
    target_url: str,
    qr_type: str = "review",
) -> dict[str, Any]:
    now = utc_now()
    return {
        "_id": new_id(),
        "business_id": business_id,
        "qr_type": qr_type,
        "file_path": file_path,
        "target_url": target_url,
        "created_at": now,
        "updated_at": now,
    }
