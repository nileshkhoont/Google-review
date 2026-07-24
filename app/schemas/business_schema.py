"""Pydantic schemas for business creation, update, and responses."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import is_valid_google_review_link


class BusinessCreateRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=150)
    service_type: str = Field(min_length=2, max_length=100)
    google_review_link: str
    business_description: str | None = Field(default=None, max_length=1000)
    review_aspects: list[str] = Field(default_factory=list)

    @field_validator("google_review_link")
    @classmethod
    def validate_review_link(cls, value: str) -> str:
        if not is_valid_google_review_link(value):
            raise ValueError("Please provide a valid Google review / maps link.")
        return value.strip()


class BusinessUpdateRequest(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=150)
    service_type: str | None = Field(default=None, min_length=2, max_length=100)
    google_review_link: str | None = None
    business_description: str | None = Field(default=None, max_length=1000)
    review_aspects: list[str] | None = None

    @field_validator("google_review_link")
    @classmethod
    def validate_review_link(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not is_valid_google_review_link(value):
            raise ValueError("Please provide a valid Google review / maps link.")
        return value.strip()

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
    service_type: str
    google_review_link: str
    business_description: str | None = None
    review_aspects: list[str] = Field(default_factory=list)
    logo_path: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
