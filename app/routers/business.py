"""Business CRUD endpoints (owner-only, JWT protected)."""
import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.dependencies import get_business_service, get_current_user_id
from app.schemas.business_schema import (BusinessResponse,BusinessUpdateRequest,ReviewAspectRequest,BusinessStatusUpdateRequest,)
from app.services.business_service import BusinessService

router = APIRouter(prefix="/api/business", tags=["Business"])


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_name: str = Form(...),
    service_type: str = Form(...),
    google_review_link: str = Form(...),
    business_description: str | None = Form(default=None),
    review_aspects: str | None = Form(default=None),
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


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
):
    await business_service.delete_business(user_id, business_id)

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