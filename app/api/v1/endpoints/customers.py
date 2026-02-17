"""
Customer API endpoints (Controller Layer).

Endpoints:
- POST /customers - Create new customer (admin only)
- GET /customers - List all customers
- GET /customers/{sqid} - Get customer by sqid
- PATCH /customers/{sqid} - Update customer (admin only)
- DELETE /customers/{sqid} - Delete customer (admin only)
"""

from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import (
    CustomerCreate, CustomerUpdate,
    PaginatedCustomerResponse,
    SingleCustomerResponse
)
from app.services import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])



@router.post("", response_model=SingleCustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Create a new customer (admin only).

    Generates sqid on-the-fly from customer ID (not stored in DB).
    Returns customer with nested package object.
    """
    service = CustomerService(db)
    customer = service.create_customer(customer_data)
    return SingleCustomerResponse(data=customer)


@router.get("", response_model=PaginatedCustomerResponse)
async def list_customers(
    page: int = 1,
    per_page: int = 10,
    name: str = None,
    package_id: str = None,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all customers (authenticated users only) with pagination.

    Supports filtering by:
    - name: Partial match on customer name (case-insensitive)
    - package_id: Exact match on package ID (sqid format)

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)

    Returns all active customers with sqid generated on-the-fly.
    """
    service = CustomerService(db)
    data, meta = service.list_customers(
        page=page, per_page=per_page, name=name, package_id=package_id
    )
    return PaginatedCustomerResponse(data=data, meta=meta)


@router.get("/{customer_id}", response_model=SingleCustomerResponse)
async def get_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get customer by ID (sqid).

    Decodes sqid to get customer_id, then returns customer details with nested package object.
    """
    service = CustomerService(db)
    customer = service.get_customer_by_id(customer_id)
    return SingleCustomerResponse(data=customer)


@router.patch("/{customer_id}", response_model=SingleCustomerResponse)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update customer (admin only).

    Can update name, package_id (as sqid), and/or monthly_fee.
    Returns customer with nested package object.
    """
    service = CustomerService(db)
    customer = service.update_customer(customer_id, update_data)
    return SingleCustomerResponse(data=customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete/deactivate customer (admin only).

    Soft delete: sets is_active to false.
    """
    service = CustomerService(db)
    service.delete_customer(customer_id)
    return None


@router.post("/{customer_id}/enable", response_model=SingleCustomerResponse)
async def enable_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Enable/activate a disabled customer (admin only).

    Sets is_active to true, making the customer visible in billing matrix again.
    """
    service = CustomerService(db)
    customer = service.enable_customer(customer_id)
    return SingleCustomerResponse(data=customer)


@router.post("/{customer_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Disable/deactivate customer (admin only).

    Soft delete: sets is_active to false.
    Customer will not appear in billing matrix until re-enabled.
    """
    service = CustomerService(db)
    service.delete_customer(customer_id)
    return None

