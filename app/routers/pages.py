"""
Server-rendered page routes (Jinja2 templates).

These routes only render HTML shells; the actual data is fetched
client-side by static/js/*.js calling the JSON API routers above.
This keeps a clean separation between page delivery and data access.
"""

import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_click_log_service, get_optional_user_id
from app.services.click_log_service import ClickLogService

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


def _redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# Cache-busting token for static JS/CSS references (see base.html and each
# template's extra_scripts block): fixed for the lifetime of the process, so
# every restart/deploy forces browsers to fetch fresh static files instead of
# silently serving a stale cached copy alongside newer server-side code.
templates.env.globals["asset_version"] = str(int(time.time()))


@router.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/dashboard")
async def dashboard_page(request: Request, user_id: str | None = Depends(get_optional_user_id)):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/businesses")
async def business_list_page(request: Request, user_id: str | None = Depends(get_optional_user_id)):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(request, "business_list.html")


@router.get("/businesses/create")
async def create_business_page(request: Request, user_id: str | None = Depends(get_optional_user_id)):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(request, "create_business.html")


@router.get("/businesses/{business_id}")
async def business_details_page(
    request: Request, business_id: str, user_id: str | None = Depends(get_optional_user_id)
):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(
        request, "business_details.html", {"business_id": business_id}
    )


@router.get("/logs")
async def logs_page(request: Request, user_id: str | None = Depends(get_optional_user_id)):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(request, "logs.html")


@router.get("/businesses/{business_id}/edit")
async def edit_business_page(
    request: Request, business_id: str, user_id: str | None = Depends(get_optional_user_id)
):
    if not user_id:
        return _redirect_to_login()
    return templates.TemplateResponse(
        request, "edit_business.html", {"business_id": business_id}
    )


@router.get("/r/{slug}")
async def customer_landing_page(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """The page a customer lands on after scanning the review QR code."""
    background_tasks.add_task(_log_scan, click_log_service, slug, "review")
    return templates.TemplateResponse(
        request, "customer_landing.html", {"slug": slug}
    )


@router.get("/s/{slug}")
async def social_landing_page(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """The page a customer lands on after scanning the social media QR code."""
    background_tasks.add_task(_log_scan, click_log_service, slug, "social")
    return templates.TemplateResponse(
        request, "social_landing.html", {"slug": slug}
    )


@router.get("/c/{slug}")
async def combined_landing_page(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    click_log_service: ClickLogService = Depends(get_click_log_service),
):
    """The page a customer lands on after scanning the combined (review + social) QR code."""
    background_tasks.add_task(_log_scan, click_log_service, slug, "combined")
    return templates.TemplateResponse(
        request, "combined_landing.html", {"slug": slug}
    )


async def _log_scan(click_log_service: ClickLogService, slug: str, page: str) -> None:
    """
    Records a QR scan the moment the landing page is actually opened —
    this is the real "scan" event (unlike button clicks, tracked client-side,
    which only fire if the page's JS loads and the business fetch succeeds).
    Runs as a background task after the response is already sent, so an
    invalid/unknown slug (or a slow DB write) never delays page rendering —
    the page's own not-found state still renders client-side as before.
    """
    try:
        await click_log_service.record_click(slug=slug, page=page, action="qr_scan")
    except HTTPException:
        pass
