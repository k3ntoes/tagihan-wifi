"""
Billing service for business logic operations.
"""

import calendar
from typing import Optional, List, Dict
from fastapi import HTTPException, status

from app.db.database import Database
from app.repositories import BillingRepository
from app.schemas import BillingMatrixRow, PaymentByMonth, PaginationMeta, CustomerInfo
from app.utils.sqids_helper import get_sqids_helper


class BillingService:
    """
    Billing service handling business logic for billing matrix operations.
    Similar to @Service in Spring Boot.
    """

    def __init__(self, db: Database):
        self.db = db
        self.billing_repo = BillingRepository(db)
        self.sqids_helper = get_sqids_helper()

    def get_billing_matrix(
        self,
        year: int,
        page: int = 1,
        per_page: int = 10,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> tuple[List[BillingMatrixRow], PaginationMeta, List[str]]:
        """
        Get annual billing matrix for customers with pagination.
        
        Args:
            year: Billing year
            page: Page number
            per_page: Items per page
            customer_id: Filter by customer sqid
            customer_name: Filter by customer name
            
        Returns:
            Tuple of (matrix rows, pagination meta, month names)
            
        Raises:
            HTTPException: If invalid customer_id or database error
        """
        try:
            # Decode customer_id if provided
            actual_customer_id = None
            if customer_id and customer_id.strip():
                try:
                    actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_id)
                    if model != 'customer':
                        raise ValueError("Not a customer ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid customer ID: {customer_id}",
                    )

            # Get customers from repository
            customers, total = self.billing_repo.find_customers_with_filters(
                customer_id=actual_customer_id,
                customer_name=customer_name,
                page=page,
                per_page=per_page,
            )

            # Build pagination meta
            total_pages = (total + per_page - 1) // per_page
            meta = PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            )

            # If no customers, return empty response
            if not customers:
                return [], meta, list(calendar.month_name)[1:]

            # Build matrix rows
            rows = []
            for customer in customers:
                customer_id_val, name, monthly_fee = customer
                row = self._build_billing_row(customer_id_val, name, monthly_fee, year)
                rows.append(row)

            month_names = list(calendar.month_name)[1:]
            return rows, meta, month_names

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_billing_summary(self, year: int) -> Dict:
        """
        Get billing summary statistics for a year.
        
        Args:
            year: Billing year
            
        Returns:
            Dictionary with summary statistics
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            # Get summary data
            customer_count, total_expected, total_collected = self.billing_repo.get_billing_summary(year)

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

    def _build_billing_row(
        self, customer_id: int, customer_name: str, monthly_fee: int, year: int
    ) -> BillingMatrixRow:
        """
        Build a billing matrix row for a customer.
        
        Args:
            customer_id: Customer database ID
            customer_name: Customer name
            monthly_fee: Monthly fee amount
            year: Billing year
            
        Returns:
            BillingMatrixRow with payment status for all months
        """
        # Generate customer sqid
        customer_sqid = self.sqids_helper.encode_with_prefix(customer_id, 'customer')

        # Get all payments for this customer in the specified year
        payments = self.billing_repo.find_payments_by_customer_and_year(customer_id, year)

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

        # Create customer info object
        customer_info = CustomerInfo(
            id=customer_sqid,
            name=customer_name,
            monthly_fee=monthly_fee,
            package=None,  # Package info not needed for billing matrix
        )

        # Create matrix row
        return BillingMatrixRow(
            customer=customer_info,
            payments=payments_by_month,
            total_paid=total_paid,
            total_expected=total_expected,
            completion_percentage=round(completion_percentage, 2),
        )
