"""
Payment API endpoints for recording and managing payments.

Endpoints:
- POST /payments - Record new payment (admin only)
- GET /payments - List payments with optional filters
- POST /payments/parse-log - Parse manual payment log entry (admin only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import PaymentCreate, PaymentResponse, PaymentLogParser
from app.utils.payment_parser import parse_payment_log
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
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
    try:
        # Resolve customer_id from sqid if provided
        customer_id = payment_data.customer_id
        if payment_data.customer_sqid and not customer_id:
            sqids_helper = get_sqids_helper()
            try:
                customer_id = sqids_helper.decode_single(payment_data.customer_sqid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid customer sqid: {payment_data.customer_sqid}",
                )

        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either customer_id or customer_sqid must be provided",
            )

        # Verify customer exists
        customer = db.conn.execute(
            "SELECT id FROM customers WHERE id = ? AND is_active = true LIMIT 1",
            [customer_id],
        ).fetchall()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}",
            )

        # Insert payment
        result = db.conn.execute(
            """
            INSERT INTO payments (customer_id, payment_date, billing_month, billing_year, amount)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, customer_id, payment_date, billing_month, billing_year, amount, created_at, updated_at
            """,
            [
                customer_id,
                payment_data.payment_date,
                payment_data.billing_month,
                payment_data.billing_year,
                payment_data.amount,
            ],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment",
            )

        db.conn.commit()

        row = result[0]
        payment_id = row[0]
        customer_id = row[1]
        
        # Generate sqid on-the-fly
        sqids_helper = get_sqids_helper()
        payment_sqid = sqids_helper.encode_single(payment_id)
        customer_sqid = sqids_helper.encode_single(customer_id)
        
        return PaymentResponse(
            sqid=payment_sqid,
            customer_sqid=customer_sqid,
            payment_date=row[2],
            billing_month=row[3],
            billing_year=row[4],
            amount=row[5],
            created_at=row[6],
            updated_at=row[7],
        )

    except HTTPException:
        raise
    except Exception as e:
        db.conn.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payment already exists for this customer and month/year",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    customer_sqid: Optional[str] = Query(None, description="Filter by customer sqid"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    year: Optional[int] = Query(None, description="Filter by billing year"),
    month: Optional[int] = Query(None, description="Filter by billing month"),
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List payments with optional filters.

    Filters:
    - customer_sqid: Get payments for specific customer (by sqid)
    - customer_id: Get payments for specific customer (by ID)
    - year: Get payments for specific year
    - month: Get payments for specific month
    """
    try:
        # Resolve customer_id from sqid if provided
        if customer_sqid and not customer_id:
            sqids_helper = get_sqids_helper()
            try:
                customer_id = sqids_helper.decode_single(customer_sqid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid customer sqid: {customer_sqid}",
                )

        # Build query dynamically
        query = """
                SELECT id,
                       customer_id,
                       payment_date,
                       billing_month,
                       billing_year,
                       amount,
                       created_at,
                       updated_at
                FROM payments
                WHERE 1 = 1"""
        params = []

        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)

        if year:
            query += " AND billing_year = ?"
            params.append(year)

        if month:
            query += " AND billing_month = ?"
            params.append(month)

        query += " ORDER BY billing_year DESC, billing_month DESC, payment_date DESC"

        result = db.conn.execute(query, params).fetchall()
        
        sqids_helper = get_sqids_helper()

        payments = [
            PaymentResponse(
                sqid=sqids_helper.encode_single(row[0]),
                customer_sqid=sqids_helper.encode_single(row[1]),
                payment_date=row[2],
                billing_month=row[3],
                billing_year=row[4],
                amount=row[5],
                created_at=row[6],
                updated_at=row[7],
            )
            for row in result
        ]

        return payments

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("/parse-log", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
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

        # Check for duplicate payment
        existing = db.conn.execute(
            """
            SELECT id FROM payments 
            WHERE customer_id = ? AND billing_month = ? AND billing_year = ?
            LIMIT 1
            """,
            [parsed.customer_id, parsed.billing_month, parsed.billing_year],
        ).fetchall()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payment already exists for {parsed.customer_name} in {parsed.billing_month}/{parsed.billing_year}",
            )

        # Insert payment
        result = db.conn.execute(
            """
            INSERT INTO payments (customer_id, payment_date, billing_month, billing_year, amount)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, customer_id, payment_date, billing_month, billing_year, amount, created_at, updated_at
            """,
            [
                parsed.customer_id,
                parsed.payment_date,
                parsed.billing_month,
                parsed.billing_year,
                parsed.amount,
            ],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment",
            )

        db.conn.commit()

        row = result[0]
        payment_id = row[0]
        customer_id = row[1]
        
        # Generate sqid on-the-fly
        sqids_helper = get_sqids_helper()
        payment_sqid = sqids_helper.encode_single(payment_id)
        customer_sqid = sqids_helper.encode_single(customer_id)
        
        return PaymentResponse(
            sqid=payment_sqid,
            customer_sqid=customer_sqid,
            payment_date=row[2],
            billing_month=row[3],
            billing_year=row[4],
            amount=row[5],
            created_at=row[6],
            updated_at=row[7],
        )

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
