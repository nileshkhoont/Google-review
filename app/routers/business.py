"""Business CRUD endpoints (owner-only, JWT protected)."""
import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.dependencies import get_business_service, get_click_log_service, get_current_user_id
from app.schemas.business_schema import (BusinessResponse,BusinessUpdateRequest,ReviewAspectRequest,BusinessStatusUpdateRequest,)
from app.schemas.click_log_schema import ActionCount
from app.services.business_service import BusinessService
from app.services.click_log_service import ClickLogService

router = APIRouter(prefix="/api/business", tags=["Business"])


def _validation_error_detail(exc: ValidationError) -> str:
    """
    Turn a Pydantic ValidationError into a single readable message.

    BusinessCreateRequest/BusinessUpdateRequest are built manually here from
    Form(...) fields rather than declared as endpoint parameters, so FastAPI
    never gets a chance to turn their ValidationError into its usual 422 —
    left alone it propagates as an unhandled exception (a bare 500). This
    reproduces that same 422 behavior with a message naming the bad field(s).
    """
    parts = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        parts.append(f"{field}: {error['msg']}")
    return "; ".join(parts)


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_name: str = Form(...),
    service_type: str = Form(...),
    google_review_link: str = Form(...),
    business_description: str | None = Form(default=None),
    review_aspects: str | None = Form(default=None),
    website: str | None = Form(default=None),
    instagram: str | None = Form(default=None),
    facebook: str | None = Form(default=None),
    whatsapp_channel: str | None = Form(default=None),
    youtube: str | None = Form(default=None),
    linkedin: str | None = Form(default=None),
    twitter_x: str | None = Form(default=None),
    custom_links: str | None = Form(default=None),
    qr_title: str | None = Form(default=None),
    primary_color: str | None = Form(default=None),
    logo: UploadFile | None = File(default=None),
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    from app.schemas.business_schema import BusinessCreateRequest

    try:
        data = BusinessCreateRequest(
            business_name=business_name,
            service_type=service_type,
            google_review_link=google_review_link,
            business_description=business_description,
            review_aspects=json.loads(review_aspects) if review_aspects else [],
            website=website,
            instagram=instagram,
            facebook=facebook,
            whatsapp_channel=whatsapp_channel,
            youtube=youtube,
            linkedin=linkedin,
            twitter_x=twitter_x,
            custom_links=json.loads(custom_links) if custom_links else [],
            qr_title=qr_title,
            primary_color=primary_color,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_validation_error_detail(exc)) from exc
    return await business_service.create_business(user_id, data, logo)


@router.get("", response_model=list[BusinessResponse])
async def list_businesses(
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.list_businesses(user_id)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.get_business(user_id, business_id)


@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    business_name: str | None = Form(default=None),
    service_type: str | None = Form(default=None),
    google_review_link: str | None = Form(default=None),
    business_description: str | None = Form(default=None),
    review_aspects: str | None = Form(default=None),
    website: str | None = Form(default=None),
    instagram: str | None = Form(default=None),
    facebook: str | None = Form(default=None),
    whatsapp_channel: str | None = Form(default=None),
    youtube: str | None = Form(default=None),
    linkedin: str | None = Form(default=None),
    twitter_x: str | None = Form(default=None),
    custom_links: str | None = Form(default=None),
    qr_title: str | None = Form(default=None),
    primary_color: str | None = Form(default=None),
    logo: UploadFile | None = File(default=None),
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    try:
        data = BusinessUpdateRequest(
            business_name=business_name,
            service_type=service_type,
            google_review_link=google_review_link,
            business_description=business_description,
            review_aspects=json.loads(review_aspects) if review_aspects else None,
            website=website,
            instagram=instagram,
            facebook=facebook,
            whatsapp_channel=whatsapp_channel,
            youtube=youtube,
            linkedin=linkedin,
            twitter_x=twitter_x,
            custom_links=json.loads(custom_links) if custom_links is not None else None,
            qr_title=qr_title,
            primary_color=primary_color,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_validation_error_detail(exc)) from exc
    return await business_service.update_business(user_id, business_id, data, logo)


@router.patch("/{business_id}/status", response_model=BusinessResponse)
async def update_business_status(
    business_id: str,
    data: BusinessStatusUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.set_business_status(user_id, business_id, data.is_active)


@router.patch("/{business_id}/social-status", response_model=BusinessResponse)
async def update_social_status(
    business_id: str,
    data: BusinessStatusUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.set_social_status(user_id, business_id, data.is_active)


@router.patch("/{business_id}/combined-status", response_model=BusinessResponse)
async def update_combined_status(
    business_id: str,
    data: BusinessStatusUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.set_combined_status(user_id, business_id, data.is_active)


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    await business_service.delete_business(user_id, business_id)

@router.get("/{business_id}/click-logs/summary", response_model=list[ActionCount])
async def get_business_click_summary(
    business_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str = Depends(get_current_user_id),
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """
    Per-button click counts for this business, most-clicked first.

    `start_date`/`end_date` (optional, "YYYY-MM-DD", interpreted as IST
    calendar days, inclusive) scope the counts to that date range instead
    of all-time. Passing just one of the two scopes to that single day.
    """
    return await click_log_service.get_business_summary(
        user_id, business_id, start_date=start_date, end_date=end_date
    )


@router.post("/review-aspects")
async def generate_review_aspects(
    data: ReviewAspectRequest,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    aspects = await business_service.generate_review_aspects(
        service_type=data.service_type,
        business_description=data.business_description,
    )

    return {
        "review_aspects": aspects
    }