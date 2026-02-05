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


class SingleUserResponse(BaseModel):
    """Single user response wrapper"""
    data: UserResponse


# ==================== Package Models ====================

class PackageCreate(BaseModel):
    """Create package request"""
    name: str = Field(..., min_length=1, max_length=100)
    speed: int = Field(..., gt=0, description="Speed in Mbps")
    price: int = Field(..., gt=0, description="Price in Rupiah")

    @field_validator("speed", "price")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be greater than 0")
        return v


class PackageUpdate(BaseModel):
    """Update package request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    speed: Optional[int] = Field(None, gt=0)
    price: Optional[int] = Field(None, gt=0)


class PackageResponse(BaseModel):
    """Package response"""
    id: str  # sqid string, generated on-the-fly
    name: str
    speed: int
    price: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PackageInfo(BaseModel):
    """Nested package info for customer response"""
    id: str  # sqid string
    name: str

    class Config:
        from_attributes = True


# ==================== Customer Models ====================

class CustomerCreate(BaseModel):
    """Create customer request"""
    name: str = Field(..., min_length=1, max_length=100)
    package_id: Optional[str] = Field(None, description="Package ID as sqid (optional)")
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
    package_id: Optional[str] = None  # sqid string
    monthly_fee: Optional[int] = Field(None, gt=0)


class CustomerResponse(BaseModel):
    """Customer response with id as sqid (generated on-the-fly, not stored in DB)"""
    id: str  # sqid string, generated from internal id
    name: str
    package: Optional[PackageInfo] = None  # nested package object or null
    monthly_fee: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SingleCustomerResponse(BaseModel):
    """Single customer response wrapper"""
    data: CustomerResponse


class SinglePackageResponse(BaseModel):
    """Single package response wrapper"""
    data: PackageResponse


# ==================== Payment Models ====================

class PaymentCreate(BaseModel):
    """Create payment request"""
    customer_id: Optional[str] = None  # sqid string
    customer_sqid: Optional[str] = None  # Deprecated: use customer_id instead
    payment_date: date
    billing_month: int = Field(..., ge=1, le=12)
    billing_year: int = Field(..., ge=2020, le=2099)
    amount: int = Field(..., gt=0)


class PaymentResponse(BaseModel):
    """Payment response with id as sqid (generated on-the-fly)"""
    id: str  # sqid string, generated from internal id
    customer_id: str  # sqid string, generated from internal customer_id
    payment_date: date
    billing_month: int
    billing_year: int
    amount: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SinglePaymentResponse(BaseModel):
    """Single payment response wrapper"""
    data: PaymentResponse


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
    customer_id: str  # sqid string, generated from internal customer_id
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


# ==================== Pagination Models ====================

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedPackageResponse(BaseModel):
    """Paginated packages response"""
    data: List[PackageResponse]
    meta: PaginationMeta


class PaginatedCustomerResponse(BaseModel):
    """Paginated customers response"""
    data: List[CustomerResponse]
    meta: PaginationMeta


class PaginatedPaymentResponse(BaseModel):
    """Paginated payments response"""
    data: List[PaymentResponse]
    meta: PaginationMeta


class PaginatedBillingMatrixResponse(BaseModel):
    """Paginated billing matrix response"""
    year: int
    month_names: List[str]
    data: List[BillingMatrixRow]
    meta: PaginationMeta


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
