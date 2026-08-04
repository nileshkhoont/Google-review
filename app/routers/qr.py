"""QR code endpoints: fetch, download, and regenerate (owner-only)."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.dependencies import get_business_service, get_current_user_id, get_qr_service
from app.schemas.qr_schema import QRResponse
from app.services.business_service import BusinessService
from app.services.qr_service import QRService

router = APIRouter(prefix="/api/qr", tags=["QR Codes"])


@router.get("/{business_id}", response_model=QRResponse)
async def get_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    await business_service.get_business(user_id, business_id)  # ownership check
    return await qr_service.get_qr_for_business(business_id)


@router.get("/{business_id}/download")
async def download_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    business = await business_service.get_business(user_id, business_id)  # ownership check
    qr = await qr_service.get_qr_for_business(business_id)
    filename = f"{business['slug']}-qr.png"
    return FileResponse(qr["file_path"], media_type="image/png", filename=filename)


@router.get("/{business_id}/social", response_model=QRResponse)
async def get_social_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    await business_service.get_business(user_id, business_id)  # ownership check
    return await qr_service.get_qr_for_business(business_id, qr_type="social")


@router.get("/{business_id}/social/download")
async def download_social_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    business = await business_service.get_business(user_id, business_id)  # ownership check
    qr = await qr_service.get_qr_for_business(business_id, qr_type="social")
    filename = f"{business['slug']}-social-qr.png"
    return FileResponse(qr["file_path"], media_type="image/png", filename=filename)


@router.get("/{business_id}/combined", response_model=QRResponse)
async def get_combined_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    await business_service.get_business(user_id, business_id)  # ownership check
    return await qr_service.get_qr_for_business(business_id, qr_type="combined")


@router.get("/{business_id}/combined/download")
async def download_combined_qr(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
    business_service: BusinessService = Depends(get_business_service),
    qr_service: QRService = Depends(get_qr_service),
):
    business = await business_service.get_business(user_id, business_id)  # ownership check
    qr = await qr_service.get_qr_for_business(business_id, qr_type="combined")
    filename = f"{business['slug']}-combined-qr.png"
    return FileResponse(qr["file_path"], media_type="image/png", filename=filename)


