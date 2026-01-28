"""
Billing matrix API endpoints for viewing annual payment status.

Endpoints:
- GET /billing-matrix/{year} - Get annual billing matrix for all customers
"""

import calendar

from fastapi import APIRouter, Depends, status, HTTPException, Path

from app.core.auth import get_current_user
from app.db.database import Database, get_db
from app.schemas import BillingMatrixResponse, BillingMatrixRow, PaymentByMonth
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/billing-matrix", tags=["billing"])


@router.get("/{year}", response_model=BillingMatrixResponse)
async def get_billing_matrix(
    year: int = Path(..., ge=2020, le=2100, description="Billing year"),
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get annual billing matrix for all active customers.

    Returns a matrix showing payment status for all 12 months of the specified year.
    Each row shows:
    - Customer info (id, sqid, name, monthly_fee)
    - Payment status for each month (paid/unpaid, amount, date)
    - Summary (total paid, total expected, completion percentage)
    """
    try:
        sqids_helper = get_sqids_helper()

        # Get all active customers
        customers = db.conn.execute(
            """
            SELECT id, name, monthly_fee
            FROM customers
            WHERE is_active = true
            ORDER BY name ASC
            """
        ).fetchall()

        if not customers:
            return BillingMatrixResponse(
                year=year,
                month_names=list(calendar.month_name)[1:],
                rows=[],
            )

        # Build matrix rows
        rows = []

        for customer in customers:
            customer_id, name, monthly_fee = customer
            
            # Generate sqid on-the-fly
            customer_sqid = sqids_helper.encode_single(customer_id)

            # Get all payments for this customer in the specified year
            payments = db.conn.execute(
                """
                SELECT billing_month, amount, payment_date
                FROM payments
                WHERE customer_id = ? AND billing_year = ?
                ORDER BY billing_month ASC
                """,
                [customer_id, year],
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
                customer_sqid=customer_sqid,
                customer_name=name,
                monthly_fee=monthly_fee,
                payments=payments_by_month,
                total_paid=total_paid,
                total_expected=total_expected,
                completion_percentage=round(completion_percentage, 2),
            )

            rows.append(row)

        return BillingMatrixResponse(
            year=year,
            month_names=list(calendar.month_name)[1:],
            rows=rows,
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
