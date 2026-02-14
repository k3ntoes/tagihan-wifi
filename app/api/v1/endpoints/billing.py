"""
Billing matrix API endpoints (Controller Layer).

Endpoints:
- GET /billing-matrix/{year} - Get annual billing matrix for all customers (paginated)
"""

from fastapi import APIRouter, Depends, Path

from app.core.auth import get_current_user
from app.db.database import Database, get_db
from app.schemas import PaginatedBillingMatrixResponse
from app.services import BillingService

router = APIRouter(prefix="/billing-matrix", tags=["billing"])


@router.get("/{year}", response_model=PaginatedBillingMatrixResponse)
async def get_billing_matrix(
    year: int = Path(..., ge=2020, le=2100, description="Billing year"),
    page: int = 1,
    per_page: int = 10,
    customer_id: str = None,
    customer_name: str = None,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get annual billing matrix for all active customers with pagination.

    Supports filtering by:
    - customer_id: Show only specific customer (sqid format)
    - customer_name: Filter by customer name (partial match, case-insensitive)

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)

    Returns a matrix showing payment status for all 12 months of the specified year.
    Each row shows:
    - Customer info (id, sqid, name, monthly_fee)
    - Payment status for each month (paid/unpaid, amount, date)
    - Summary (total paid, total expected, completion percentage)
    """
    service = BillingService(db)
    rows, meta, month_names = service.get_billing_matrix(
        year=year,
        page=page,
        per_page=per_page,
        customer_id=customer_id,
        customer_name=customer_name,
    )
    
    return PaginatedBillingMatrixResponse(
        year=year,
        month_names=month_names,
        data=rows,
        meta=meta,
    )


@router.get("/{year}/summary")
async def get_billing_summary(
    year: int = Path(..., ge=2020, le=2100, description="Billing year"),
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get summary statistics for billing matrix.

    Returns overall statistics:
    - Total customers
    - Total expected revenue
    - Total revenue collected
    - Overall completion percentage
    - Pending revenue
    """
    service = BillingService(db)
    return service.get_billing_summary(year)

