"""
Server-rendered page routes (Jinja2 templates).

These routes only render HTML shells; the actual data is fetched
client-side by static/js/*.js calling the JSON API routers above.
This keeps a clean separation between page delivery and data access.
"""

import time

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")

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
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/businesses")
async def business_list_page(request: Request):
    return templates.TemplateResponse(request, "business_list.html")


@router.get("/businesses/create")
async def create_business_page(request: Request):
    return templates.TemplateResponse(request, "create_business.html")


@router.get("/businesses/{business_id}")
async def business_details_page(request: Request, business_id: str):
    return templates.TemplateResponse(
        request, "business_details.html", {"business_id": business_id}
    )


@router.get("/businesses/{business_id}/edit")
async def edit_business_page(request: Request, business_id: str):
    return templates.TemplateResponse(
        request, "edit_business.html", {"business_id": business_id}
    )


@router.get("/r/{slug}")
async def customer_landing_page(request: Request, slug: str):
    """The page a customer lands on after scanning the review QR code."""
    return templates.TemplateResponse(
        request, "customer_landing.html", {"slug": slug}
    )


@router.get("/s/{slug}")
async def social_landing_page(request: Request, slug: str):
    """The page a customer lands on after scanning the social media QR code."""
    return templates.TemplateResponse(
        request, "social_landing.html", {"slug": slug}
    )
