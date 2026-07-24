"""
Server-rendered page routes (Jinja2 templates).

These routes only render HTML shells; the actual data is fetched
client-side by static/js/*.js calling the JSON API routers above.
This keeps a clean separation between page delivery and data access.
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


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
    """The page a customer lands on after scanning the QR code."""
    return templates.TemplateResponse(
        request, "customer_landing.html", {"slug": slug}
    )
