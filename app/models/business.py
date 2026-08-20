"""Represents the shape of a document in the `businesses` collection."""

from typing import Any

from app.utils.helper import new_id, slugify, slugify_combined, slugify_social, utc_now


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
    qr_title: str | None = None,
    primary_color: str | None = None,
    enable_gujarati: bool = True,
    enable_hindi: bool = True,
) -> dict[str, Any]:
    now = utc_now()
    return {
        "_id": new_id(),
        "owner_id": owner_id,
        "business_name": business_name,
        "slug": slugify(business_name),
        "social_slug": slugify_social(business_name),
        "combined_slug": slugify_combined(business_name),
        "service_type": service_type,
        "google_review_link": google_review_link,
        "business_description": business_description,
        "review_aspects": review_aspects or [],
        "logo_path": logo_path,
        # QR poster branding. Both fall back to sensible defaults at
        # generation time (qr_title -> business_name, primary_color -> the
        # generator's default brand color) when left unset, so these stay
        # optional everywhere else.
        "qr_title": qr_title,
        "primary_color": primary_color,
        "is_active": True,
        # Always True for newly created businesses — they only ever get the
        # combined QR. Absent (falsy via .get()) on businesses created
        # before this field existed, which keep their 3-QR setup untouched.
        "combined_only": True,
        "website": website,
        "instagram": instagram,
        "facebook": facebook,
        "whatsapp_channel": whatsapp_channel,
        "youtube": youtube,
        "linkedin": linkedin,
        "twitter_x": twitter_x,
        "custom_links": custom_links or [],
        "enable_gujarati": enable_gujarati,
        "enable_hindi": enable_hindi,
        "created_at": now,
        "updated_at": now,
    }
