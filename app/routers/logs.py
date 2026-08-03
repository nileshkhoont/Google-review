"""Admin-only endpoints for viewing button-click activity logs (JWT protected)."""

from fastapi import APIRouter, Depends

from app.dependencies import get_click_log_service, get_current_user_id
from app.schemas.click_log_schema import BusinessClickSummary, ClickLogListResponse
from app.services.click_log_service import ClickLogService

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("", response_model=ClickLogListResponse)
async def list_click_logs(
    limit: int = 50,
    skip: int = 0,
    business_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    return await click_log_service.get_global_logs(limit=limit, skip=skip, business_id=business_id)


@router.get("/summary", response_model=list[BusinessClickSummary])
async def get_click_log_summary(
    user_id: str = Depends(get_current_user_id),
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """Per-company (business) click totals, most-active first."""
    return await click_log_service.get_business_totals()
