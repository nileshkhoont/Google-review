"""Public, customer-facing endpoints reached after scanning a QR code.

No authentication required — these are opened directly by customers.
"""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_click_log_service, get_customer_service
from app.schemas.click_log_schema import TrackClickRequest
from app.schemas.review_schema import (
    CustomerBusinessResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    TranslateReviewRequest,
    TranslateReviewResponse,
)
from app.services.click_log_service import ClickLogService
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/api/customer", tags=["Customer"])


@router.get("/{slug}", response_model=CustomerBusinessResponse)
async def get_customer_business(
    slug: str,
    customer_service: CustomerService = Depends(get_customer_service),
):
    business = await customer_service.get_business_by_slug(slug)
    return CustomerBusinessResponse(
        business_name=business["business_name"],
        service_type=business["service_type"],
        logo_path=business.get("logo_path"),
        google_review_link=business["google_review_link"],
        review_aspects=business.get("review_aspects", []),
        website=business.get("website"),
        instagram=business.get("instagram"),
        facebook=business.get("facebook"),
        whatsapp_channel=business.get("whatsapp_channel"),
        youtube=business.get("youtube"),
        linkedin=business.get("linkedin"),
        twitter_x=business.get("twitter_x"),
        custom_links=business.get("custom_links", []),
    )


@router.get("/social/{social_slug}", response_model=CustomerBusinessResponse)
async def get_customer_business_by_social_slug(
    social_slug: str,
    customer_service: CustomerService = Depends(get_customer_service),
):
    """Looked up by the social QR code's distinct slug (see /s/{slug})."""
    business = await customer_service.get_business_by_social_slug(social_slug)
    return CustomerBusinessResponse(
        business_name=business["business_name"],
        service_type=business["service_type"],
        logo_path=business.get("logo_path"),
        google_review_link=business["google_review_link"],
        review_aspects=business.get("review_aspects", []),
        website=business.get("website"),
        instagram=business.get("instagram"),
        facebook=business.get("facebook"),
        whatsapp_channel=business.get("whatsapp_channel"),
        youtube=business.get("youtube"),
        linkedin=business.get("linkedin"),
        twitter_x=business.get("twitter_x"),
        custom_links=business.get("custom_links", []),
    )


@router.post("/{slug}/generate-review", response_model=GenerateReviewResponse)
async def generate_review(
    slug: str,
    data: GenerateReviewRequest,
    customer_service: CustomerService = Depends(get_customer_service),
):
    return await customer_service.generate_review(
        slug=slug,
        rating=data.rating,
        selected_review_aspects=data.selected_review_aspects,)


@router.post("/{slug}/translate-review", response_model=TranslateReviewResponse)
async def translate_review(
    slug: str,
    data: TranslateReviewRequest,
    customer_service: CustomerService = Depends(get_customer_service),
):
    translation = await customer_service.translate_review(
        slug=slug,
        text=data.text,
        language=data.language,
    )
    return TranslateReviewResponse(translation=translation)


@router.post("/{slug}/track-click", status_code=status.HTTP_204_NO_CONTENT)
async def track_review_page_click(
    slug: str,
    data: TrackClickRequest,
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """Records a button click on the review landing page (/r/{slug})."""
    await click_log_service.record_click(slug=slug, page="review", action=data.action)


@router.post("/social/{social_slug}/track-click", status_code=status.HTTP_204_NO_CONTENT)
async def track_social_page_click(
    social_slug: str,
    data: TrackClickRequest,
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """Records a button click on the social-links landing page (/s/{slug})."""
    await click_log_service.record_click(slug=social_slug, page="social", action=data.action)
