"""Business CRUD endpoints (owner-only, JWT protected)."""
import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.dependencies import get_business_service, get_click_log_service, get_current_user_id
from app.schemas.business_schema import (BusinessResponse,BusinessUpdateRequest,ReviewAspectRequest,BusinessStatusUpdateRequest,)
from app.schemas.click_log_schema import ActionCount
from app.services.business_service import BusinessService
from app.services.click_log_service import ClickLogService

router = APIRouter(prefix="/api/business", tags=["Business"])


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
    logo: UploadFile | None = File(default=None),
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    from app.schemas.business_schema import BusinessCreateRequest

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
    )
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
    logo: UploadFile | None = File(default=None),
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
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
    )
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
    user_id: str = Depends(get_current_user_id),
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """Per-button click counts for this business, most-clicked first."""
    return await click_log_service.get_business_summary(user_id, business_id)


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