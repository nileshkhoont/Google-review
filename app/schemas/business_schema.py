"""Pydantic schemas for business creation, update, and responses."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import is_valid_google_review_link, is_valid_hex_color, is_valid_url

# Optional social links a business owner can attach; every field feeds the
# second ("social media") QR code alongside the review QR code.
SOCIAL_LINK_FIELDS = (
    "website",
    "instagram",
    "facebook",
    "whatsapp_channel",
    "youtube",
    "linkedin",
    "twitter_x",
)


def _validate_social_link(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    if not is_valid_url(value):
        raise ValueError("Please provide a valid http(s) link.")
    return value.strip()


def _validate_primary_color(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    value = value.strip()
    if not is_valid_hex_color(value):
        raise ValueError("Please provide a valid hex color, e.g. #4f46e5.")
    return value


class CustomLink(BaseModel):
    """A user-defined third-party link (Zomato, Swiggy, Yelp, etc.) shown
    alongside the standard social platforms on the social media QR page."""

    title: str = Field(min_length=1, max_length=50)
    url: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title is required.")
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not is_valid_url(value):
            raise ValueError("Please provide a valid http(s) link.")
        return value.strip()


class BusinessCreateRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=150)
    service_type: str = Field(min_length=2, max_length=100)
    google_review_link: str
    business_description: str | None = Field(default=None, max_length=1000)
    review_aspects: list[str] = Field(default_factory=list)

    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    whatsapp_channel: str | None = None
    youtube: str | None = None
    linkedin: str | None = None
    twitter_x: str | None = None
    custom_links: list[CustomLink] = Field(default_factory=list)

    # QR poster branding — both optional, both fall back to defaults at
    # generation time (see app/utils/qr_generator.py).
    qr_title: str | None = Field(default=None, max_length=150)
    primary_color: str | None = None

    # Whether the customer-facing review page offers a Gujarati/Hindi
    # translation of the generated review, alongside the default English.
    enable_gujarati: bool = True
    enable_hindi: bool = True

    @field_validator("google_review_link")
    @classmethod
    def validate_review_link(cls, value: str) -> str:
        if not is_valid_google_review_link(value):
            raise ValueError("Please provide a valid Google review / maps link.")
        return value.strip()

    @field_validator(*SOCIAL_LINK_FIELDS)
    @classmethod
    def validate_social_links(cls, value: str | None) -> str | None:
        return _validate_social_link(value)

    @field_validator("primary_color")
    @classmethod
    def validate_primary_color(cls, value: str | None) -> str | None:
        return _validate_primary_color(value)


class BusinessUpdateRequest(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=150)
    service_type: str | None = Field(default=None, min_length=2, max_length=100)
    google_review_link: str | None = None
    business_description: str | None = Field(default=None, max_length=1000)
    review_aspects: list[str] | None = None

    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    whatsapp_channel: str | None = None
    youtube: str | None = None
    linkedin: str | None = None
    twitter_x: str | None = None
    custom_links: list[CustomLink] | None = None

    qr_title: str | None = Field(default=None, max_length=150)
    primary_color: str | None = None

    enable_gujarati: bool = True
    enable_hindi: bool = True

    @field_validator("google_review_link")
    @classmethod
    def validate_review_link(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not is_valid_google_review_link(value):
            raise ValueError("Please provide a valid Google review / maps link.")
        return value.strip()

    @field_validator(*SOCIAL_LINK_FIELDS)
    @classmethod
    def validate_social_links(cls, value: str | None) -> str | None:
        return _validate_social_link(value)

    @field_validator("primary_color")
    @classmethod
    def validate_primary_color(cls, value: str | None) -> str | None:
        return _validate_primary_color(value)

class ReviewAspectRequest(BaseModel):
    service_type: str
    business_description: str | None = None


class BusinessStatusUpdateRequest(BaseModel):
    is_active: bool


class BusinessResponse(BaseModel):
    id: str
    owner_id: str
    business_name: str
    slug: str
    social_slug: str
    combined_slug: str
    service_type: str
    google_review_link: str
    business_description: str | None = None
    review_aspects: list[str] = Field(default_factory=list)
    logo_path: str | None = None
    qr_title: str | None = None
    primary_color: str | None = None
    enable_gujarati: bool = True
    enable_hindi: bool = True
    is_active: bool = True
    social_is_active: bool = True
    combined_is_active: bool = True
    combined_only: bool = False
    created_at: datetime
    updated_at: datetime

    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    whatsapp_channel: str | None = None
    youtube: str | None = None
    linkedin: str | None = None
    twitter_x: str | None = None
    custom_links: list[CustomLink] = Field(default_factory=list)
