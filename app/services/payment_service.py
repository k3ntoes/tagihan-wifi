"""
Payment service for business logic operations.
"""

from typing import Optional, List
from fastapi import HTTPException, status

from app.db.database import Database
from app.repositories import PaymentRepository, CustomerRepository
from app.schemas import PaymentResponse, PaymentCreate, PaginationMeta
from app.utils.sqids_helper import get_sqids_helper


class PaymentService:
    """
    Payment service handling business logic for payment operations.
    Similar to @Service in Spring Boot.
    """

    def __init__(self, db: Database):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.sqids_helper = get_sqids_helper()

    def create_payment(self, payment_data: PaymentCreate) -> PaymentResponse:
        """
        Create a new payment with business validation.
        
        Args:
            payment_data: Payment creation data
            
        Returns:
            Created payment response
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Decode customer_id from sqid
            actual_customer_id = None
            if payment_data.customer_id:
                try:
                    actual_customer_id, model = self.sqids_helper.decode_with_prefix(
                        payment_data.customer_id
                    )
                    if model != 'customer':
                        raise ValueError("Not a customer ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid customer ID: {payment_data.customer_id}",
                    )
            elif payment_data.customer_sqid:  # Backward compatibility
                try:
                    actual_customer_id, model = self.sqids_helper.decode_with_prefix(
                        payment_data.customer_sqid
                    )
                    if model != 'customer':
                        raise ValueError("Not a customer ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid customer sqid: {payment_data.customer_sqid}",
                    )

            if not actual_customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="customer_id must be provided",
                )

            # Verify customer exists and is active
            if not self.customer_repo.exists_by_id(actual_customer_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                )

            # Check for duplicate payment
            if self.payment_repo.exists_for_period(
                actual_customer_id, payment_data.billing_month, payment_data.billing_year
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment already exists for this customer and month/year",
                )

            # Create payment
            payment_row = self.payment_repo.create(
                actual_customer_id,
                payment_data.payment_date,
                payment_data.billing_month,
                payment_data.billing_year,
                payment_data.amount,
            )

            if not payment_row:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create payment",
                )

            self.db.conn.commit()

            # Build response
            return self._build_payment_response(payment_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment already exists for this customer and month/year",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_payment_by_id(self, payment_sqid: str) -> PaymentResponse:
        """
        Get payment by sqid.
        
        Args:
            payment_sqid: Payment sqid
            
        Returns:
            Payment response
            
        Raises:
            HTTPException: If payment not found or invalid sqid
        """
        try:
            # Decode sqid
            actual_payment_id, model = self.sqids_helper.decode_with_prefix(payment_sqid)
            if model != 'payment':
                raise ValueError("Not a payment ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment ID: {payment_sqid}",
            )

        payment_row = self.payment_repo.find_by_id(actual_payment_id)

        if not payment_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return self._build_payment_response(payment_row)

    def list_payments(
        self,
        page: int = 1,
        per_page: int = 10,
        customer_id: Optional[str] = None,
        customer_sqid: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> tuple[List[PaymentResponse], PaginationMeta]:
        """
        List payments with filters and pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            customer_id: Filter by customer sqid
            customer_sqid: Deprecated, filter by customer sqid
            year: Filter by billing year
            month: Filter by billing month
            
        Returns:
            Tuple of (payment list, pagination meta)
            
        Raises:
            HTTPException: If invalid customer_id or database error
        """
        try:
            # Decode customer_id if provided
            actual_customer_id = None
            if customer_id:
                try:
                    actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_id)
                    if model != 'customer':
                        raise ValueError("Not a customer ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid customer ID: {customer_id}",
                    )
            elif customer_sqid:  # Backward compatibility
                try:
                    actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_sqid)
                    if model != 'customer':
                        raise ValueError("Not a customer ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid customer sqid: {customer_sqid}",
                    )

            # Get payments from repository
            payments, total = self.payment_repo.find_all_with_filters(
                customer_id=actual_customer_id, year=year, month=month, page=page, per_page=per_page
            )

            # Build response list
            data = [self._build_payment_response(row) for row in payments]

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

            return data, meta

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def _build_payment_response(self, payment_row: tuple) -> PaymentResponse:
        """Build PaymentResponse from database row."""
        payment_sqid = self.sqids_helper.encode_with_prefix(payment_row[0], 'payment')
        customer_sqid = self.sqids_helper.encode_with_prefix(payment_row[1], 'customer')
        
        return PaymentResponse(
            id=payment_sqid,
            customer_id=customer_sqid,
            payment_date=payment_row[2],
            billing_month=payment_row[3],
            billing_year=payment_row[4],
            amount=payment_row[5],
            created_at=payment_row[6],
            updated_at=payment_row[7],
        )
