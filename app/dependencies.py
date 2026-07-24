"""
FastAPI dependency providers.

Centralizes:
- current-user extraction from JWT (cookie or Authorization header)
- repository/service construction, so routers stay thin
"""

from fastapi import Cookie, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.repositories.business_repository import BusinessRepository
from app.repositories.qr_repository import QRRepository
from app.repositories.review_repository import ReviewRepository
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.customer_service import CustomerService
from app.services.qr_service import QRService
from app.utils.jwt_utils import decode_access_token


def _extract_token(authorization: str | None, access_token_cookie: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return access_token_cookie


async def get_current_user_id(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> str:
    """Extract and validate the JWT, returning the authenticated user's id."""
    token = _extract_token(authorization, access_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )
    return payload["sub"]


async def get_optional_user_id(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> str | None:
    """Same as get_current_user_id but returns None instead of raising (for public pages)."""
    token = _extract_token(authorization, access_token)
    if not token:
        return None
    payload = decode_access_token(token)
    return payload.get("sub") if payload else None


# ---------------------------------------------------------------------------
# Service factory helpers (used by routers via Depends())
# ---------------------------------------------------------------------------


def get_auth_service() -> AuthService:
    return AuthService()


def get_business_service() -> BusinessService:
    db: AsyncIOMotorDatabase = get_db()
    return BusinessService(BusinessRepository(db), QRRepository(db))


def get_qr_service() -> QRService:
    db: AsyncIOMotorDatabase = get_db()
    return QRService(QRRepository(db))


def get_customer_service() -> CustomerService:
    db: AsyncIOMotorDatabase = get_db()
    return CustomerService(BusinessRepository(db), ReviewRepository(db))


def get_business_repository() -> BusinessRepository:
    return BusinessRepository(get_db())
