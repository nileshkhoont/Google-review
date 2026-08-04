"""
FastAPI application entrypoint.

Responsibilities:
- Create the FastAPI app
- Manage MongoDB connection lifecycle
- Mount static files and register all routers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Database
from app.routers import auth, business, customer, logs, pages, qr
from app.utils.logger import logger


async def _backfill_social_slugs() -> None:
    """
    One-time migration for businesses created before the social-media QR
    feature existed: they have no `social_slug`, and if a "social" QR
    document already exists for them (from before social_slug existed) it
    still encodes the old shared-slug URL. Backfill a dedicated social_slug
    and (re)generate that QR so it points at the new /s/{social_slug} URL.
    """
    from app.repositories.qr_repository import QRRepository
    from app.services.qr_service import QRService
    from app.utils.helper import slugify_social

    db = Database.db
    qr_service = QRService(QRRepository(db))

    cursor = db["businesses"].find({"social_slug": {"$exists": False}})
    async for biz in cursor:
        social_slug = slugify_social(biz["business_name"])
        await db["businesses"].update_one(
            {"_id": biz["_id"]}, {"$set": {"social_slug": social_slug}}
        )
        await qr_service.generate_social_qr_for_business(
            business_id=biz["_id"],
            slug=social_slug,
            business_name=biz["business_name"],
            logo_path=biz.get("logo_path"),
        )
        logger.info("Backfilled social_slug for business %s", biz["_id"])


async def _backfill_combined_slugs() -> None:
    """
    Same as _backfill_social_slugs(), but for the combined (review + social)
    QR code: businesses created before that feature existed have no
    `combined_slug` and no "combined" QR document yet.
    """
    from app.repositories.qr_repository import QRRepository
    from app.services.qr_service import QRService
    from app.utils.helper import slugify_combined

    db = Database.db
    qr_service = QRService(QRRepository(db))

    cursor = db["businesses"].find({"combined_slug": {"$exists": False}})
    async for biz in cursor:
        combined_slug = slugify_combined(biz["business_name"])
        await db["businesses"].update_one(
            {"_id": biz["_id"]}, {"$set": {"combined_slug": combined_slug}}
        )
        await qr_service.generate_combined_qr_for_business(
            business_id=biz["_id"],
            slug=combined_slug,
            business_name=biz["business_name"],
            logo_path=biz.get("logo_path"),
        )
        logger.info("Backfilled combined_slug for business %s", biz["_id"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect()
    await _backfill_social_slugs()
    await _backfill_combined_slugs()
    yield
    await Database.disconnect()


app = FastAPI(
    title=settings.app_name,
    description="AI-assisted Google review collection platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else [settings.base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# JSON API routers
app.include_router(auth.router)
app.include_router(business.router)
app.include_router(qr.router)
app.include_router(customer.router)
app.include_router(logs.router)

# Server-rendered page routes
app.include_router(pages.router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.on_event("startup")
async def log_startup():
    logger.info("%s starting up in '%s' mode", settings.app_name, settings.app_env)
    logger.info(
        "\n%s\nLoaded Gemini API Keys : %d\n%s",
        "=" * 41, len(settings.gemini_key_list), "=" * 41,
    )
