"""
Pydantic models and schemas for request/response validation.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class RoleEnum(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"


# ==================== Auth Models ====================

class UserLogin(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """Create user request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: RoleEnum = RoleEnum.USER


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Customer Models ====================

class CustomerCreate(BaseModel):
    """Create customer request"""
    name: str = Field(..., min_length=1, max_length=100)
    monthly_fee: int = Field(..., gt=0)

    @field_validator("monthly_fee")
    @classmethod
    def validate_fee(cls, v):
        if v <= 0:
            raise ValueError("Monthly fee must be greater than 0")
        return v


class CustomerUpdate(BaseModel):
    """Update customer request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    monthly_fee: Optional[int] = Field(None, gt=0)


class CustomerResponse(BaseModel):
    """Customer response with sqid (generated on-the-fly, not stored in DB)"""
    sqid: str  # Generated from id, not stored in database
    name: str
    monthly_fee: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Payment Models ====================

class PaymentCreate(BaseModel):
    """Create payment request"""
    customer_id: Optional[int] = None
    customer_sqid: Optional[str] = None
    payment_date: date
    billing_month: int = Field(..., ge=1, le=12)
    billing_year: int = Field(..., ge=2020, le=2099)
    amount: int = Field(..., gt=0)


class PaymentResponse(BaseModel):
    """Payment response with sqid (generated on-the-fly)"""
    sqid: str  # Generated from id, not stored in database
    customer_sqid: str  # Generated from customer_id
    payment_date: date
    billing_month: int
    billing_year: int
    amount: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentLogParser(BaseModel):
    """Parser for manual payment log entries"""
    log_entry: str = Field(..., description='Format: "DD-MM-YYYY customer_name"')


class PaymentByMonth(BaseModel):
    """Payment status for a single month"""
    month: int
    month_name: str
    paid: bool
    amount: Optional[int] = None
    payment_date: Optional[date] = None


class BillingMatrixRow(BaseModel):
    """Row in billing matrix for a customer"""
    customer_sqid: str  # Generated from customer_id
    customer_name: str
    monthly_fee: int
    payments: List[PaymentByMonth]
    total_paid: int
    total_expected: int
    completion_percentage: float


class BillingMatrixResponse(BaseModel):
    """Billing matrix response for a year"""
    year: int
    month_names: List[str]
    rows: List[BillingMatrixRow]


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
