"""Represents the shape of a document in the `businesses` collection."""

from typing import Any

from app.utils.helper import new_id, slugify, slugify_social, utc_now


def build_business_document(
    owner_id: str,
    business_name: str,
    service_type: str,
    google_review_link: str,
    business_description: str | None = None,
    review_aspects: list[str] | None = None,
    logo_path: str | None = None,
    website: str | None = None,
    instagram: str | None = None,
    facebook: str | None = None,
    whatsapp_channel: str | None = None,
    youtube: str | None = None,
    linkedin: str | None = None,
    twitter_x: str | None = None,
    custom_links: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    now = utc_now()
    return {
        "_id": new_id(),
        "owner_id": owner_id,
        "business_name": business_name,
        "slug": slugify(business_name),
        "social_slug": slugify_social(business_name),
        "service_type": service_type,
        "google_review_link": google_review_link,
        "business_description": business_description,
        "review_aspects": review_aspects or [],
        "logo_path": logo_path,
        "is_active": True,
        "website": website,
        "instagram": instagram,
        "facebook": facebook,
        "whatsapp_channel": whatsapp_channel,
        "youtube": youtube,
        "linkedin": linkedin,
        "twitter_x": twitter_x,
        "custom_links": custom_links or [],
        "created_at": now,
        "updated_at": now,
    }
