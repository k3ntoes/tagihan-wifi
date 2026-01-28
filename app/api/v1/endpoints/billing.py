"""
Billing matrix API endpoints for viewing annual payment status.

Endpoints:
- GET /billing-matrix/{year} - Get annual billing matrix for all customers (paginated)
"""

import calendar
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Path, Query

from app.core.auth import get_current_user
from app.db.database import Database, get_db
from app.schemas import BillingMatrixRow, PaymentByMonth, PaginatedBillingMatrixResponse, PaginationMeta
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/billing-matrix", tags=["billing"])


@router.get("/{year}", response_model=PaginatedBillingMatrixResponse)
async def get_billing_matrix(
    year: int = Path(..., ge=2020, le=2100, description="Billing year"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by specific customer ID (sqid)"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name (partial match)"),
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
    try:
        sqids_helper = get_sqids_helper()

        # Build query with filters
        query = """
            SELECT id, name, monthly_fee
            FROM customers
            WHERE is_active = true
        """
        params = []
        
        # Add customer_id filter
        if customer_id and customer_id.strip():
            try:
                actual_customer_id, model = sqids_helper.decode_with_prefix(customer_id)
                if model != 'customer':
                    raise ValueError("Not a customer ID")
                query += " AND id = ?"
                params.append(actual_customer_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid customer ID: {customer_id}",
                )
        
        # Add customer_name filter
        if customer_name and customer_name.strip():
            query += " AND LOWER(name) LIKE LOWER(?)"
            params.append(f"%{customer_name.strip()}%")
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM customers WHERE is_active = true"
        count_params = []
        
        if customer_id and customer_id.strip():
            try:
                actual_customer_id, model = sqids_helper.decode_with_prefix(customer_id)
                if model != 'customer':
                    raise ValueError("Not a customer ID")
                count_query += " AND id = ?"
                count_params.append(actual_customer_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid customer ID: {customer_id}",
                )
        
        if customer_name and customer_name.strip():
            count_query += " AND LOWER(name) LIKE LOWER(?)"
            count_params.append(f"%{customer_name.strip()}%")
        
        total = db.conn.execute(count_query, count_params).fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        query += " ORDER BY name ASC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        # Get paginated customers
        customers = db.conn.execute(query, params).fetchall()

        if not customers:
            return PaginatedBillingMatrixResponse(
                year=year,
                month_names=list(calendar.month_name)[1:],
                data=[],
                meta=PaginationMeta(
                    total=total,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                ),
            )

        # Build matrix rows
        rows = []

        for customer in customers:
            customer_id_val, name, monthly_fee = customer
            
            # Generate sqid on-the-fly with Laravel-style prefix
            customer_sqid = sqids_helper.encode_with_prefix(customer_id_val, 'customer')

            # Get all payments for this customer in the specified year
            payments = db.conn.execute(
                """
                SELECT billing_month, amount, payment_date
                FROM payments
                WHERE customer_id = ? AND billing_year = ?
                ORDER BY billing_month ASC
                """,
                [customer_id_val, year],
            ).fetchall()

            # Create payment map for quick lookup
            payment_map = {}
            for payment in payments:
                month, amount, payment_date = payment
                payment_map[month] = {
                    "amount": amount,
                    "payment_date": payment_date,
                }

            # Build payment array for all 12 months
            payments_by_month = []
            total_paid = 0
            total_expected = 0

            for month in range(1, 13):
                month_name = calendar.month_name[month]
                total_expected += monthly_fee

                if month in payment_map:
                    payment_info = payment_map[month]
                    total_paid += payment_info["amount"]
                    payments_by_month.append(
                        PaymentByMonth(
                            month=month,
                            month_name=month_name,
                            paid=True,
                            amount=payment_info["amount"],
                            payment_date=payment_info["payment_date"],
                        )
                    )
                else:
                    payments_by_month.append(
                        PaymentByMonth(
                            month=month,
                            month_name=month_name,
                            paid=False,
                            amount=None,
                            payment_date=None,
                        )
                    )

            # Calculate completion percentage
            completion_percentage = (
                (total_paid / total_expected * 100) if total_expected > 0 else 0
            )

            # Create matrix row
            row = BillingMatrixRow(
                customer_id=customer_sqid,
                customer_name=name,
                monthly_fee=monthly_fee,
                payments=payments_by_month,
                total_paid=total_paid,
                total_expected=total_expected,
                completion_percentage=round(completion_percentage, 2),
            )

            rows.append(row)

        meta = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return PaginatedBillingMatrixResponse(
            year=year,
            month_names=list(calendar.month_name)[1:],
            data=rows,
            meta=meta,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
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
    try:
        # Get active customers count
        customer_count = db.conn.execute(
            "SELECT COUNT(*) FROM customers WHERE is_active = true"
        ).fetchone()[0]

        # Calculate totals
        totals = db.conn.execute(
            """
            SELECT
                SUM(c.monthly_fee) * 12 as total_expected,
                COALESCE(SUM(p.amount), 0) as total_collected
            FROM customers c
            LEFT JOIN payments p ON c.id = p.customer_id AND p.billing_year = ?
            WHERE c.is_active = true
            """,
            [year],
        ).fetchone()

        total_expected = totals[0] or 0
        total_collected = totals[1] or 0
        pending = total_expected - total_collected
        completion_percentage = (
            (total_collected / total_expected * 100) if total_expected > 0 else 0
        )

        return {
            "year": year,
            "total_customers": customer_count,
            "total_expected": total_expected,
            "total_collected": total_collected,
            "pending": pending,
            "completion_percentage": round(completion_percentage, 2),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
