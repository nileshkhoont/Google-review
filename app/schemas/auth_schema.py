"""Pydantic schemas for login and the current-user response.

There is no registration in this application — it's a single-admin,
internal tool. The admin's credentials live in environment variables
(see `Settings.admin_email` / `Settings.admin_password`), not in a
database, so there's no user document to model here.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
