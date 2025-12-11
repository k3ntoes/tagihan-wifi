from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""

    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str
