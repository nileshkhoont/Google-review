"""Pydantic schemas for the customer-facing AI review generation flow."""

from pydantic import BaseModel, Field

class GenerateReviewRequest(BaseModel):
    rating: int | None = None
    selected_review_aspects: list[str] = Field(default_factory=list)


class ReviewVariant(BaseModel):
    en: str

class GenerateReviewResponse(BaseModel):
    reviews: list[ReviewVariant]
    business_name: str
    google_review_link: str


class TranslateReviewRequest(BaseModel):
    text: str
    language: str  # "gu" | "hi"


class TranslateReviewResponse(BaseModel):
    translation: str


class CustomerLink(BaseModel):
    title: str
    url: str


class CustomerBusinessResponse(BaseModel):
    business_name: str
    service_type: str
    logo_path: str | None = None
    google_review_link: str
    review_aspects: list[str] = Field(default_factory=list)

    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    whatsapp_channel: str | None = None
    youtube: str | None = None
    linkedin: str | None = None
    twitter_x: str | None = None
    custom_links: list[CustomerLink] = Field(default_factory=list)
