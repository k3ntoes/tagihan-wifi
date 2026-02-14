"""
Package service for business logic operations.
"""

from typing import Optional, List
from fastapi import HTTPException, status

from app.db.database import Database
from app.repositories import PackageRepository
from app.schemas import PackageResponse, PackageCreate, PackageUpdate, PaginationMeta
from app.utils.sqids_helper import get_sqids_helper


class PackageService:
    """
    Package service handling business logic for package operations.
    Similar to @Service in Spring Boot.
    """

    def __init__(self, db: Database):
        self.db = db
        self.package_repo = PackageRepository(db)
        self.sqids_helper = get_sqids_helper()

    def create_package(self, package_data: PackageCreate) -> PackageResponse:
        """
        Create a new package with business validation.
        
        Args:
            package_data: Package creation data
            
        Returns:
            Created package response
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Check if package name already exists
            if self.package_repo.exists_by_name(package_data.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Package with name '{package_data.name}' already exists",
                )

            # Create package
            package_row = self.package_repo.create(
                package_data.name, package_data.speed, package_data.price
            )

            if not package_row:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create package",
                )

            self.db.conn.commit()

            # Build response
            return self._build_package_response(package_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def get_package_by_id(self, package_sqid: str) -> PackageResponse:
        """
        Get package by sqid.
        
        Args:
            package_sqid: Package sqid
            
        Returns:
            Package response
            
        Raises:
            HTTPException: If package not found or invalid sqid
        """
        try:
            # Decode sqid
            actual_package_id, model = self.sqids_helper.decode_with_prefix(package_sqid)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_sqid}",
            )

        package_row = self.package_repo.find_by_id(actual_package_id)

        if not package_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found",
            )

        return self._build_package_response(package_row)

    def list_packages(
        self,
        page: int = 1,
        per_page: int = 10,
        name: Optional[str] = None,
        min_speed: Optional[int] = None,
        max_speed: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        include_inactive: bool = False,
    ) -> tuple[List[PackageResponse], PaginationMeta]:
        """
        List packages with filters and pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            name: Filter by package name
            min_speed: Minimum speed filter
            max_speed: Maximum speed filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            include_inactive: Include inactive packages
            
        Returns:
            Tuple of (package list, pagination meta)
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            # Get packages from repository
            packages, total = self.package_repo.find_all_with_filters(
                name=name,
                min_speed=min_speed,
                max_speed=max_speed,
                min_price=min_price,
                max_price=max_price,
                include_inactive=include_inactive,
                page=page,
                per_page=per_page,
            )

            # Build response list
            data = [self._build_package_response(row) for row in packages]

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

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def update_package(
        self, package_sqid: str, package_data: PackageUpdate
    ) -> PackageResponse:
        """
        Update package with business validation.
        
        Args:
            package_sqid: Package sqid
            package_data: Update data
            
        Returns:
            Updated package response
            
        Raises:
            HTTPException: If validation fails or package not found
        """
        try:
            # Decode package sqid
            actual_package_id, model = self.sqids_helper.decode_with_prefix(package_sqid)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_sqid}",
            )

        try:
            # Verify package exists
            if not self.package_repo.exists_by_id(actual_package_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Package not found",
                )

            # Check if new name conflicts with existing package
            if package_data.name is not None:
                existing = self.package_repo.find_by_name(package_data.name)
                if existing and existing[0] != actual_package_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Package with name '{package_data.name}' already exists",
                    )

            # Update package
            updated_row = self.package_repo.update(
                actual_package_id,
                name=package_data.name,
                speed=package_data.speed,
                price=package_data.price,
            )

            if not updated_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Package not found or no changes made",
                )

            self.db.conn.commit()

            return self._build_package_response(updated_row)

        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete_package(self, package_sqid: str) -> None:
        """
        Soft delete package.
        
        Args:
            package_sqid: Package sqid
            
        Raises:
            HTTPException: If package not found, has customers, or invalid sqid
        """
        try:
            # Decode package sqid
            actual_package_id, model = self.sqids_helper.decode_with_prefix(package_sqid)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_sqid}",
            )

        try:
            # Check if package has customers
            if self.package_repo.has_customers(actual_package_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete package with active customers",
                )

            # Soft delete package
            affected = self.package_repo.soft_delete(actual_package_id)

            if affected == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Package not found",
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

    def _build_package_response(self, package_row: tuple) -> PackageResponse:
        """Build PackageResponse from database row."""
        package_sqid = self.sqids_helper.encode_with_prefix(package_row[0], 'package')
        return PackageResponse(
            id=package_sqid,
            name=package_row[1],
            speed=package_row[2],
            price=package_row[3],
            is_active=package_row[4],
            created_at=package_row[5],
            updated_at=package_row[6],
        )
