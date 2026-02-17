"""
Customer service for business logic operations.
"""

from typing import Optional, List
from fastapi import HTTPException, status

from app.db.database import Database
from app.repositories import CustomerRepository, PackageRepository
from app.schemas import CustomerResponse, CustomerCreate, CustomerUpdate, PackageInfo, PaginationMeta
from app.utils.sqids_helper import get_sqids_helper


class CustomerService:
    """
    Customer service handling business logic for customer operations.
    Similar to @Service in Spring Boot.
    """

    def __init__(self, db: Database):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.package_repo = PackageRepository(db)
        self.sqids_helper = get_sqids_helper()

    def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        """
        Create a new customer with business validation.
        
        Args:
            customer_data: Customer creation data
            
        Returns:
            Created customer response
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Validate and decode package_id if provided
            actual_package_id = None
            if customer_data.package_id is not None:
                try:
                    actual_package_id, model = self.sqids_helper.decode_with_prefix(
                        customer_data.package_id
                    )
                    if model != 'package':
                        raise ValueError("Not a package ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid package ID: {customer_data.package_id}",
                    )

                # Verify package exists and is active
                if not self.package_repo.exists_by_id(actual_package_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Package with ID {customer_data.package_id} not found or inactive",
                    )

            # Create customer
            customer_row = self.customer_repo.create(
                customer_data.name, actual_package_id, customer_data.monthly_fee
            )

            if not customer_row:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create customer",
                )

            self.db.conn.commit()

            # Build response
            return self._build_customer_response(customer_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_customer_by_id(self, customer_sqid: str) -> CustomerResponse:
        """
        Get customer by sqid.
        
        Args:
            customer_sqid: Customer sqid
            
        Returns:
            Customer response
            
        Raises:
            HTTPException: If customer not found or invalid sqid
        """
        try:
            # Decode sqid
            actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_sqid)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_sqid}",
            )

        customer_row = self.customer_repo.find_by_id(actual_customer_id)

        if not customer_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return self._build_customer_response_with_package(customer_row)

    def list_customers(
        self,
        page: int = 1,
        per_page: int = 10,
        name: Optional[str] = None,
        package_id: Optional[str] = None,
    ) -> tuple[List[CustomerResponse], PaginationMeta]:
        """
        List customers with filters and pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            name: Filter by customer name
            package_id: Filter by package sqid
            
        Returns:
            Tuple of (customer list, pagination meta)
            
        Raises:
            HTTPException: If invalid package_id or database error
        """
        try:
            # Decode package_id if provided
            actual_package_id = None
            if package_id and package_id.strip():
                try:
                    actual_package_id, model = self.sqids_helper.decode_with_prefix(package_id)
                    if model != 'package':
                        raise ValueError("Not a package ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid package ID: {package_id}",
                    )

            # Get customers from repository
            customers, total = self.customer_repo.find_all_with_filters(
                name=name, package_id=actual_package_id, page=page, per_page=per_page
            )

            # Build response list
            data = [self._build_customer_response_with_package(row) for row in customers]

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

    def update_customer(
        self, customer_sqid: str, customer_data: CustomerUpdate
    ) -> CustomerResponse:
        """
        Update customer with business validation.
        
        Args:
            customer_sqid: Customer sqid
            customer_data: Update data
            
        Returns:
            Updated customer response
            
        Raises:
            HTTPException: If validation fails or customer not found
        """
        try:
            # Decode customer sqid
            actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_sqid)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_sqid}",
            )

        try:
            # Verify customer exists
            if not self.customer_repo.exists_by_id(actual_customer_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                )

            # Validate and decode package_id if provided
            actual_package_id = None
            if customer_data.package_id is not None:
                try:
                    actual_package_id, model = self.sqids_helper.decode_with_prefix(
                        customer_data.package_id
                    )
                    if model != 'package':
                        raise ValueError("Not a package ID")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid package ID: {customer_data.package_id}",
                    )

                # Verify package exists and is active
                if not self.package_repo.exists_by_id(actual_package_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Package with ID {customer_data.package_id} not found or inactive",
                    )

            # Update customer
            updated_row = self.customer_repo.update(
                actual_customer_id,
                name=customer_data.name,
                package_id=actual_package_id,
                monthly_fee=customer_data.monthly_fee,
                package_start_date=customer_data.package_start_date.isoformat() if customer_data.package_start_date else None,
            )

            if not updated_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found or no changes made",
                )

            self.db.conn.commit()

            # Get full customer data with package info
            customer_row = self.customer_repo.find_by_id(actual_customer_id)
            return self._build_customer_response_with_package(customer_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete_customer(self, customer_sqid: str) -> None:
        """
        Soft delete customer.
        
        Args:
            customer_sqid: Customer sqid
            
        Raises:
            HTTPException: If customer not found or invalid sqid
        """
        try:
            # Decode customer sqid
            actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_sqid)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_sqid}",
            )

        try:
            # Soft delete customer
            affected = self.customer_repo.soft_delete(actual_customer_id)

            if affected == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                )

            self.db.conn.commit()

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def enable_customer(self, customer_sqid: str) -> CustomerResponse:
        """
        Enable/activate a disabled customer.
        
        Args:
            customer_sqid: Customer sqid
            
        Returns:
            Enabled customer response
            
        Raises:
            HTTPException: If customer not found or invalid sqid
        """
        try:
            # Decode customer sqid
            actual_customer_id, model = self.sqids_helper.decode_with_prefix(customer_sqid)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_sqid}",
            )

        try:
            # Enable customer
            affected = self.customer_repo.enable_customer(actual_customer_id)

            if affected == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found or already active",
                )

            self.db.conn.commit()

            # Get the updated customer with full details
            customer_row = self.customer_repo.find_by_id(actual_customer_id)
            if not customer_row:
                # If find_by_id fails, try find_inactive_customer to get the data
                customer_row = self.customer_repo.find_inactive_customer(actual_customer_id)
            
            return self._build_customer_response_with_package(customer_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def _build_customer_response(self, customer_row: tuple) -> CustomerResponse:
        """Build CustomerResponse from database row without package info."""
        customer_sqid = self.sqids_helper.encode_with_prefix(customer_row[0], 'customer')
        return CustomerResponse(
            id=customer_sqid,
            name=customer_row[1],
            package=None,
            monthly_fee=customer_row[3],
            created_at=customer_row[4],
            updated_at=customer_row[5],
        )

    def _build_customer_response_with_package(self, customer_row: tuple) -> CustomerResponse:
        """Build CustomerResponse from database row with package info."""
        customer_sqid = self.sqids_helper.encode_with_prefix(customer_row[0], 'customer')
        
        package_info = None
        if customer_row[2] is not None and customer_row[3] is not None:
            package_sqid = self.sqids_helper.encode_with_prefix(customer_row[2], 'package')
            package_info = PackageInfo(id=package_sqid, name=customer_row[3])

        return CustomerResponse(
            id=customer_sqid,
            name=customer_row[1],
            package=package_info,
            monthly_fee=customer_row[4],
            package_start_date=customer_row[5],
            created_at=customer_row[6],
            updated_at=customer_row[7],
        )
