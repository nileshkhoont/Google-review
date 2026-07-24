"""Business logic for the single hardcoded admin login.

There are no user accounts or a `users` collection — this is an internal,
single-admin tool. The admin's credentials are read from environment
variables (`ADMIN_EMAIL` / `ADMIN_PASSWORD`) and compared directly; nothing
is persisted or looked up in the database.
"""

import secrets

from fastapi import HTTPException, status

from app.config import settings
from app.schemas.auth_schema import LoginRequest
from app.utils.jwt_utils import create_access_token

# Fixed identity for the one admin account. Other parts of the app (e.g.
# business ownership checks) key off of this constant instead of a real
# user id, so that existing logic keeps working unchanged with no
# `users` collection behind it.
ADMIN_ID = "admin"


class AuthService:
    async def login(self, data: LoginRequest) -> str:
        if not settings.admin_email or not settings.admin_password:
            # Fail closed rather than letting blank/misconfigured env vars
            # accidentally match blank input.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin credentials are not configured on the server.",
            )

        # Constant-time comparisons — this is the only credential check in
        # the app, so it's worth guarding against timing attacks.
        email_matches = secrets.compare_digest(
            data.email.strip().lower(), settings.admin_email.strip().lower()
        )
        password_matches = secrets.compare_digest(data.password, settings.admin_password)

        if not (email_matches and password_matches):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        return create_access_token(subject=ADMIN_ID)

    async def get_current_user(self, user_id: str) -> dict:
        if user_id != ADMIN_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again.",
            )
        return {
            "id": ADMIN_ID,
            "full_name": "Administrator",
            "email": settings.admin_email,
        }
