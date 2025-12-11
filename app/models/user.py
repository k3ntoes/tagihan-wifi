from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Role


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=6)
    role: Role = Role.USER  # Default role is USER


class UserUpdate(BaseModel):
    """Schema for user update."""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    role: Optional[Role] = None
    pelanggan_id: Optional[int] = None


class UserInDB(UserBase):
    """Schema for user in database."""

    id: int
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    role: Role = Role.USER
    pelanggan_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserBase):
    """Schema for user response (without password)."""

    id: int
    is_active: bool = True
    is_superuser: bool = False
    role: Role = Role.USER
    pelanggan_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change."""

    old_password: str
    new_password: str = Field(..., min_length=6)


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=6)
