"""
Payment API endpoints (Controller Layer).

Endpoints:
- POST /payments - Record new payment (admin only)
- GET /payments - List payments with optional filters
- POST /payments/parse-log - Parse manual payment log entry (admin only)
"""

from fastapi import APIRouter, Depends, status, HTTPException

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import PaymentCreate, SinglePaymentResponse, PaymentLogParser, PaginatedPaymentResponse
from app.services import PaymentService
from app.utils.payment_parser import parse_payment_log
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=SinglePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Record a new payment (admin only).

    Supports payment recording via either customer_id or customer_sqid.
    Prevents duplicate payments for the same (customer, month, year).
    """
    service = PaymentService(db)
    payment = service.create_payment(payment_data)
    return SinglePaymentResponse(data=payment)


@router.get("", response_model=PaginatedPaymentResponse)
async def list_payments(
    page: int = 1,
    per_page: int = 10,
    customer_id: str = None,
    customer_sqid: str = None,
    year: int = None,
    month: int = None,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List payments with optional filters and pagination.

    Filters:
    - customer_id: Get payments for specific customer (by sqid)
    - customer_sqid: Deprecated, use customer_id instead
    - year: Get payments for specific year
    - month: Get payments for specific month

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    """
    service = PaymentService(db)
    data, meta = service.list_payments(
        page=page,
        per_page=per_page,
        customer_id=customer_id,
        customer_sqid=customer_sqid,
        year=year,
        month=month,
    )
    return PaginatedPaymentResponse(data=data, meta=meta)


@router.post("/parse-log", response_model=SinglePaymentResponse, status_code=status.HTTP_201_CREATED)
async def parse_payment_log_endpoint(
    log_data: PaymentLogParser,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Parse a manual payment log entry and record the payment (admin only).

    Expected format: "DD-MM-YYYY customer_name"
    Example: "02-05-2025 opi"

    The system will:
    1. Parse the date as payment date
    2. Extract billing month and year from the date
    3. Find customer by name (case-insensitive)
    4. Use customer's monthly_fee as payment amount
    5. Record the payment
    """
    try:
        # Parse the log entry
        parsed = parse_payment_log(log_data.log_entry, db)

        # Create payment using service
        payment_data = PaymentCreate(
            customer_id=None,  # Will be set by service
            customer_sqid=None,
            payment_date=parsed.payment_date,
            billing_month=parsed.billing_month,
            billing_year=parsed.billing_year,
            amount=parsed.amount,
        )
        
        # Manually set customer_id for service
        sqids_helper = get_sqids_helper()
        customer_sqid = sqids_helper.encode_with_prefix(parsed.customer_id, 'customer')
        payment_data.customer_id = customer_sqid

        service = PaymentService(db)
        payment = service.create_payment(payment_data)
        return SinglePaymentResponse(data=payment)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )

