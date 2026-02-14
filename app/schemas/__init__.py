"""
Pydantic models and schemas for request/response validation.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


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
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """Create user request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: RoleEnum = RoleEnum.USER


class UserResponse(BaseModel):
    """User response with authentication details"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: int  # User ID (integer, not sqid)
    username: str
    role: RoleEnum  # User role: admin or user
    is_active: bool
    created_at: datetime


class SingleUserResponse(BaseModel):
    """Single user response wrapper"""
    data: UserResponse


class PasswordChange(BaseModel):
    """Change password request"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserUpdateAdmin(BaseModel):
    """Update user request (admin only)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


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
    """Package response with id as sqid (generated on-the-fly, not stored in DB)"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: str  # sqid string, generated from internal id
    name: str
    speed: int  # Speed in Mbps
    price: int  # Price in Rupiah
    is_active: bool
    created_at: datetime
    updated_at: datetime
    customers_count: Optional[int] = None  # Total number of customers using this package (optional)


class PackageInfo(BaseModel):
    """Nested package info for customer response"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: str  # sqid string, generated from internal package id
    name: str  # Package name


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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: str  # sqid string, generated from internal id
    name: str
    package: Optional[PackageInfo] = None  # Nested package object or null
    monthly_fee: int  # Monthly subscription fee in Rupiah
    created_at: datetime
    updated_at: datetime
    payments_count: Optional[int] = None  # Total number of payments made (optional)


class SingleCustomerResponse(BaseModel):
    """Single customer response wrapper"""
    data: CustomerResponse


class SinglePackageResponse(BaseModel):
    """Single package response wrapper"""
    data: PackageResponse


class CustomerInfo(BaseModel):
    """Nested customer info for payment response"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: str  # sqid string, generated from internal customer id
    name: str  # Customer name
    monthly_fee: int  # Monthly subscription fee in Rupiah
    package: Optional[PackageInfo] = None  # Nested package info or null


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
    """Payment response with id as sqid (generated on-the-fly, not stored in DB)"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
    
    id: str  # sqid string, generated from internal id
    customer: CustomerInfo  # Nested customer object with package info
    payment_date: date  # Date when payment was made
    billing_month: int  # Month being paid for (1-12)
    billing_year: int  # Year being paid for
    amount: int  # Payment amount in Rupiah
    created_at: datetime
    updated_at: datetime


class SinglePaymentResponse(BaseModel):
    """Single payment response wrapper"""
    data: PaymentResponse


class PaymentLogParser(BaseModel):
    """Parser for manual payment log entries"""
    log_entry: str = Field(..., description='Format: "DD-MM-YYYY customer_name"')


class PaymentByMonth(BaseModel):
    """Payment status for a single month in billing matrix"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    month: int  # Month number (1-12)
    month_name: str  # Full month name (e.g., "January")
    paid: bool  # Whether payment was made for this month
    amount: Optional[int] = None  # Payment amount if paid, null otherwise
    payment_date: Optional[date] = None  # Payment date if paid, null otherwise


class BillingMatrixRow(BaseModel):
    """Row in billing matrix showing annual payment status for a customer"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    customer: CustomerInfo  # Nested customer object with package info
    payments: List[PaymentByMonth]  # Payment status for all 12 months
    total_paid: int  # Total amount paid in the year (Rupiah)
    total_expected: int  # Total expected for the year (monthly_fee × 12)
    completion_percentage: float  # Percentage of expected payments completed


class BillingMatrixResponse(BaseModel):
    """Billing matrix response showing payment overview for all customers in a year"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    year: int  # Billing year
    month_names: List[str]  # List of all month names (January to December)
    rows: List[BillingMatrixRow]  # Payment data for each customer


# ==================== Pagination Models ====================

class PaginationMeta(BaseModel):
    """Pagination metadata for list responses"""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    total: int = Field(..., ge=0, description="Total number of items across all pages")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages available")
    has_next: bool = Field(..., description="Whether there's a next page available")
    has_prev: bool = Field(..., description="Whether there's a previous page available")


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


class PaginatedUserResponse(BaseModel):
    """Paginated users response"""
    data: List[UserResponse]
    meta: PaginationMeta


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
