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
from app.routers import auth, business, customer, pages, qr
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect()
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
