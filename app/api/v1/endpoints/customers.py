"""
Customer API endpoints for CRUD operations.

Endpoints:
- POST /customers - Create new customer (admin only)
- GET /customers - List all customers
- GET /customers/{sqid} - Get customer by sqid
- PATCH /customers/{sqid} - Update customer (admin only)
- DELETE /customers/{sqid} - Delete customer (admin only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, 
    PaginatedCustomerResponse, PaginationMeta,
    PackageInfo, SingleCustomerResponse
)
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=SingleCustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Create a new customer (admin only).

    Generates sqid on-the-fly from customer ID (not stored in DB).
    Returns customer with nested package object.
    """
    try:
        sqids_helper = get_sqids_helper()

        # Validate package_id if provided (now expects sqid string)
        actual_package_id = None
        if customer_data.package_id is not None:
            try:
                actual_package_id, model = sqids_helper.decode_with_prefix(customer_data.package_id)
                if model != 'package':
                    raise ValueError("Not a package ID")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package ID: {customer_data.package_id}",
                )
            
            package_check = db.conn.execute(
                "SELECT id, price FROM packages WHERE id = ? AND is_active = true",
                [actual_package_id],
            ).fetchone()
            
            if not package_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Package with ID {customer_data.package_id} not found or inactive",
                )

        # Insert customer
        result = db.conn.execute(
            """
            INSERT INTO customers (name, package_id, monthly_fee)
            VALUES (?, ?, ?)
            RETURNING id, name, package_id, monthly_fee, created_at, updated_at
            """,
            [customer_data.name, actual_package_id, customer_data.monthly_fee],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer",
            )

        db.conn.commit()

        customer_row = result[0]
        customer_id = customer_row[0]

        # Generate sqid on-the-fly from ID with Laravel-style prefix
        customer_sqid = sqids_helper.encode_with_prefix(customer_id, 'customer')
        
        # Get package info if package_id is set
        package_info = None
        if customer_row[2] is not None:
            pkg = db.conn.execute(
                "SELECT name FROM packages WHERE id = ?",
                [customer_row[2]],
            ).fetchone()
            if pkg:
                package_sqid = sqids_helper.encode_with_prefix(customer_row[2], 'package')
                package_info = PackageInfo(id=package_sqid, name=pkg[0])

        customer_response = CustomerResponse(
            id=customer_sqid,
            name=customer_row[1],
            package=package_info,
            monthly_fee=customer_row[3],
            created_at=customer_row[4],
            updated_at=customer_row[5],
        )
        
        return SingleCustomerResponse(data=customer_response)

    except ValueError as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("", response_model=PaginatedCustomerResponse)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by customer name (partial match)"),
    package_id: Optional[str] = Query(None, description="Filter by package ID (sqid)"),
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all customers (authenticated users only) with pagination.

    Supports filtering by:
    - name: Partial match on customer name (case-insensitive)
    - package_id: Exact match on package ID (sqid format)

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)

    Returns all active customers with sqid generated on-the-fly.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Build query with filters
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name, c.monthly_fee, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.is_active = true
        """
        params = []
        
        # Add name filter (partial match, case-insensitive)
        if name and name.strip():
            query += " AND LOWER(c.name) LIKE LOWER(?)"
            params.append(f"%{name.strip()}%")
        
        # Add package_id filter
        if package_id and package_id.strip():
            try:
                actual_package_id, model = sqids_helper.decode_with_prefix(package_id)
                if model != 'package':
                    raise ValueError("Not a package ID")
                query += " AND c.package_id = ?"
                params.append(actual_package_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package ID: {package_id}",
                )
        
        # Get total count
        count_query = """
            SELECT COUNT(*)
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.is_active = true
        """
        count_params = []
        
        if name and name.strip():
            count_query += " AND LOWER(c.name) LIKE LOWER(?)"
            count_params.append(f"%{name.strip()}%")
        
        if package_id and package_id.strip():
            try:
                actual_package_id, model = sqids_helper.decode_with_prefix(package_id)
                if model != 'package':
                    raise ValueError("Not a package ID")
                count_query += " AND c.package_id = ?"
                count_params.append(actual_package_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package ID: {package_id}",
                )
        
        total = db.conn.execute(count_query, count_params).fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        query += " ORDER BY c.name ASC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        result = db.conn.execute(query, params).fetchall()

        data = []
        for row in result:
            package_info = None
            if row[2] is not None and row[3] is not None:
                package_sqid = sqids_helper.encode_with_prefix(row[2], 'package')
                package_info = PackageInfo(id=package_sqid, name=row[3])
            
            data.append(CustomerResponse(
                id=sqids_helper.encode_with_prefix(row[0], 'customer'),
                name=row[1],
                package=package_info,
                monthly_fee=row[4],
                created_at=row[5],
                updated_at=row[6],
            ))
        
        meta = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
        
        return PaginatedCustomerResponse(data=data, meta=meta)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{customer_id}", response_model=SingleCustomerResponse)
async def get_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get customer by ID (sqid).

    Decodes sqid to get customer_id, then returns customer details with nested package object.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get customer_id
        try:
            actual_customer_id = sqids_helper.decode_single(customer_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_id}",
            )
        
        result = db.conn.execute(
            """
            SELECT c.id, c.name, c.package_id, p.name as package_name, c.monthly_fee, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.id = ? AND c.is_active = true
            LIMIT 1
            """,
            [actual_customer_id],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}",
            )

        row = result[0]
        
        # Get package info if package_id is set
        package_info = None
        if row[2] is not None and row[3] is not None:
            package_sqid = sqids_helper.encode_with_prefix(row[2], 'package')
            package_info = PackageInfo(id=package_sqid, name=row[3])
        
        customer_response = CustomerResponse(
            id=customer_id,
            name=row[1],
            package=package_info,
            monthly_fee=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
        
        return SingleCustomerResponse(data=customer_response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.patch("/{customer_id}", response_model=SingleCustomerResponse)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update customer (admin only).

    Can update name, package_id (as sqid), and/or monthly_fee.
    Returns customer with nested package object.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get customer_id
        try:
            actual_customer_id, model = sqids_helper.decode_with_prefix(customer_id)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_id}",
            )
        
        # Check if customer exists
        customer = db.conn.execute(
            "SELECT id FROM customers WHERE id = ? AND is_active = true LIMIT 1",
            [actual_customer_id],
        ).fetchall()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}",
            )

        # Build update query dynamically
        updates = []
        params = []

        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)
            
        if update_data.package_id is not None:
            # Decode package sqid to actual ID
            try:
                actual_package_id, model = sqids_helper.decode_with_prefix(update_data.package_id)
                if model != 'package':
                    raise ValueError("Not a package ID")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package ID: {update_data.package_id}",
                )
            
            # Validate package exists
            package_check = db.conn.execute(
                "SELECT id FROM packages WHERE id = ? AND is_active = true",
                [actual_package_id],
            ).fetchone()
            
            if not package_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Package with ID {update_data.package_id} not found or inactive",
                )
            updates.append("package_id = ?")
            params.append(actual_package_id)

        if update_data.monthly_fee is not None:
            updates.append("monthly_fee = ?")
            params.append(update_data.monthly_fee)

        if not updates:
            # No updates provided, return existing customer
            return await get_customer(customer_id, db, current_user)

        # Add updated_at and customer_id
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(actual_customer_id)

        # Execute update
        query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ? RETURNING id, name, package_id, monthly_fee, created_at, updated_at"
        result = db.conn.execute(query, params).fetchall()

        db.conn.commit()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update customer",
            )

        row = result[0]
        
        # Get package info if package_id is set
        package_info = None
        if row[2] is not None:
            pkg = db.conn.execute(
                "SELECT name FROM packages WHERE id = ?",
                [row[2]],
            ).fetchone()
            if pkg:
                package_sqid = sqids_helper.encode_with_prefix(row[2], 'package')
                package_info = PackageInfo(id=package_sqid, name=pkg[0])
        
        customer_response = CustomerResponse(
            id=customer_id,
            name=row[1],
            package=package_info,
            monthly_fee=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
        
        return SingleCustomerResponse(data=customer_response)

    except HTTPException:
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete/deactivate customer (admin only).

    Soft delete: sets is_active to false.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get customer_id
        try:
            actual_customer_id, model = sqids_helper.decode_with_prefix(customer_id)
            if model != 'customer':
                raise ValueError("Not a customer ID")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer ID: {customer_id}",
            )
        
        # Check if customer exists
        customer = db.conn.execute(
            "SELECT id FROM customers WHERE id = ? LIMIT 1",
            [actual_customer_id],
        ).fetchall()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}",
            )

        # Soft delete
        db.conn.execute(
            "UPDATE customers SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            [actual_customer_id],
        )
        db.conn.commit()

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
