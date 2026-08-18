"""Authentication endpoints: login, current user, logout.

No registration endpoint exists — this app supports exactly one admin
account, authenticated against ADMIN_EMAIL / ADMIN_PASSWORD env vars.
"""

import math

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.dependencies import get_auth_service, get_current_user_id
from app.schemas.auth_schema import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.rate_limiter import check_login_rate_limit

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    retry_after = check_login_rate_limit(request.client.host)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )

    token = await auth_service.login(data)

    # Store as an httpOnly cookie so server-rendered pages can also use it,
    # while still returning the token in the body for API/JS clients.
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(user_id)
