"""
Package API endpoints for CRUD operations.

Endpoints:
- POST /packages - Create new package (admin only)
- GET /packages - List all packages
- GET /packages/{id} - Get package by ID
- PUT /packages/{id} - Update package (admin only)
- DELETE /packages/{id} - Delete package (admin only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import PackageCreate, PackageUpdate, PackageResponse, PaginatedPackageResponse, PaginationMeta
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    package_data: PackageCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Create a new package (admin only).

    Args:
        package_data: Package details (name, speed, price)
        db: Database instance
        current_user: Authenticated admin user

    Returns:
        Created package details

    Raises:
        HTTPException 400: Package name already exists
        HTTPException 500: Database error
    """
    try:
        # Check if package name already exists
        existing = db.conn.execute(
            "SELECT id FROM packages WHERE name = ? AND is_active = true",
            [package_data.name],
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Package with name '{package_data.name}' already exists",
            )

        # Insert package
        result = db.conn.execute(
            """
            INSERT INTO packages (name, speed, price)
            VALUES (?, ?, ?)
            RETURNING id, name, speed, price, is_active, created_at, updated_at
            """,
            [package_data.name, package_data.speed, package_data.price],
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create package",
            )

        db.conn.commit()

        return PackageResponse(
            id=result[0],
            name=result[1],
            speed=result[2],
            price=result[3],
            is_active=result[4],
            created_at=result[5],
            updated_at=result[6],
        )

    except HTTPException:
        db.conn.rollback()
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("", response_model=PaginatedPackageResponse)
async def list_packages(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by package name (partial match)"),
    min_speed: Optional[int] = Query(None, ge=0, description="Filter by minimum speed (Mbps)"),
    max_speed: Optional[int] = Query(None, ge=0, description="Filter by maximum speed (Mbps)"),
    min_price: Optional[int] = Query(None, ge=0, description="Filter by minimum price"),
    max_price: Optional[int] = Query(None, ge=0, description="Filter by maximum price"),
    include_inactive: bool = Query(False, description="Include inactive packages"),
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all packages with optional filters and pagination.

    Supports filtering by:
    - name: Partial match on package name (case-insensitive)
    - min_speed/max_speed: Speed range in Mbps
    - min_price/max_price: Price range in Rupiah
    - include_inactive: Include inactive packages

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)

    Returns:
        Paginated list of packages matching filters
    """
    try:
        query = "SELECT id, name, speed, price, is_active, created_at, updated_at FROM packages WHERE 1=1"
        params = []
        
        # Active/inactive filter
        if not include_inactive:
            query += " AND is_active = true"
        
        # Name filter (partial match, case-insensitive)
        if name and name.strip():
            query += " AND LOWER(name) LIKE LOWER(?)"
            params.append(f"%{name.strip()}%")
        
        # Speed range filters
        if min_speed is not None:
            query += " AND speed >= ?"
            params.append(min_speed)
        
        if max_speed is not None:
            query += " AND speed <= ?"
            params.append(max_speed)
        
        # Price range filters
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM packages WHERE 1=1"
        count_params = []
        
        if not include_inactive:
            count_query += " AND is_active = true"
            
        if name and name.strip():
            count_query += " AND LOWER(name) LIKE LOWER(?)"
            count_params.append(f"%{name.strip()}%")
        
        if min_speed is not None:
            count_query += " AND speed >= ?"
            count_params.append(min_speed)
        
        if max_speed is not None:
            count_query += " AND speed <= ?"
            count_params.append(max_speed)
        
        if min_price is not None:
            count_query += " AND price >= ?"
            count_params.append(min_price)
        
        if max_price is not None:
            count_query += " AND price <= ?"
            count_params.append(max_price)
        
        total = db.conn.execute(count_query, count_params).fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        query += " ORDER BY name ASC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        results = db.conn.execute(query, params).fetchall()
        
        sqids_helper = get_sqids_helper()

        data = [
            PackageResponse(
                id=sqids_helper.encode_with_prefix(row[0], 'package'),
                name=row[1],
                speed=row[2],
                price=row[3],
                is_active=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in results
        ]
        
        meta = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
        
        return PaginatedPackageResponse(data=data, meta=meta)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get package by ID (sqid).

    Args:
        package_id: Package sqid
        db: Database instance
        current_user: Authenticated user

    Returns:
        Package details

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Invalid sqid
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get actual package_id
        try:
            actual_package_id, model = sqids_helper.decode_with_prefix(package_id)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_id}",
            )
        
        result = db.conn.execute(
            """
            SELECT id, name, speed, price, is_active, created_at, updated_at
            FROM packages
            WHERE id = ?
            """,
            [actual_package_id],
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package with ID {package_id} not found",
            )

        return PackageResponse(
            id=package_id,
            name=result[1],
            speed=result[2],
            price=result[3],
            is_active=result[4],
            created_at=result[5],
            updated_at=result[6],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: str,
    package_data: PackageUpdate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update package (admin only).

    Args:
        package_id: Package sqid
        package_data: Updated package details
        db: Database instance
        current_user: Authenticated admin user

    Returns:
        Updated package details

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Package name already exists or invalid sqid
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get actual package_id
        try:
            actual_package_id, model = sqids_helper.decode_with_prefix(package_id)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_id}",
            )
        
        # Check if package exists
        existing = db.conn.execute(
            "SELECT id FROM packages WHERE id = ?",
            [actual_package_id],
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package with ID {package_id} not found",
            )

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if package_data.name is not None:
            # Check if new name already exists (excluding current package)
            name_check = db.conn.execute(
                "SELECT id FROM packages WHERE name = ? AND id != ? AND is_active = true",
                [package_data.name, actual_package_id],
            ).fetchone()

            if name_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Package with name '{package_data.name}' already exists",
                )

            update_fields.append("name = ?")
            params.append(package_data.name)

        if package_data.speed is not None:
            update_fields.append("speed = ?")
            params.append(package_data.speed)

        if package_data.price is not None:
            update_fields.append("price = ?")
            params.append(package_data.price)

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(actual_package_id)

        # Execute update
        query = f"""
            UPDATE packages
            SET {', '.join(update_fields)}
            WHERE id = ?
            RETURNING id, name, speed, price, is_active, created_at, updated_at
        """

        result = db.conn.execute(query, params).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update package",
            )

        db.conn.commit()

        return PackageResponse(
            id=package_id,
            name=result[1],
            speed=result[2],
            price=result[3],
            is_active=result[4],
            created_at=result[5],
            updated_at=result[6],
        )

    except HTTPException:
        db.conn.rollback()
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete package (soft delete by setting is_active to false) - admin only.

    Args:
        package_id: Package sqid
        db: Database instance
        current_user: Authenticated admin user

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Package is in use by customers or invalid sqid
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get actual package_id
        try:
            actual_package_id, model = sqids_helper.decode_with_prefix(package_id)
            if model != 'package':
                raise ValueError("Not a package ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package ID: {package_id}",
            )
        
        # Check if package exists
        existing = db.conn.execute(
            "SELECT id FROM packages WHERE id = ?",
            [actual_package_id],
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package with ID {package_id} not found",
            )

        # Check if package is in use by any active customers
        customers_using = db.conn.execute(
            "SELECT COUNT(*) FROM customers WHERE package_id = ? AND is_active = true",
            [actual_package_id],
        ).fetchone()

        if customers_using and customers_using[0] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete package: {customers_using[0]} active customer(s) are using this package",
            )

        # Soft delete: set is_active to false
        db.conn.execute(
            """
            UPDATE packages
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [actual_package_id],
        )

        db.conn.commit()

    except HTTPException:
        db.conn.rollback()
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
