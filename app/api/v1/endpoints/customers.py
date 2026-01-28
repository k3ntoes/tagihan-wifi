"""
Customer API endpoints for CRUD operations.

Endpoints:
- POST /customers - Create new customer (admin only)
- GET /customers - List all customers
- GET /customers/{sqid} - Get customer by sqid
- PATCH /customers/{sqid} - Update customer (admin only)
- DELETE /customers/{sqid} - Delete customer (admin only)
"""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.sqids_helper import get_sqids_helper

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Create a new customer (admin only).

    Generates sqid on-the-fly from customer ID (not stored in DB).
    """
    try:
        sqids_helper = get_sqids_helper()

        # Insert customer
        result = db.conn.execute(
            """
            INSERT INTO customers (name, monthly_fee)
            VALUES (?, ?)
            RETURNING id, name, monthly_fee, created_at, updated_at
            """,
            [customer_data.name, customer_data.monthly_fee],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer",
            )

        db.conn.commit()

        customer_row = result[0]
        customer_id = customer_row[0]

        # Generate sqid on-the-fly from ID
        sqid = sqids_helper.encode_single(customer_id)

        return CustomerResponse(
            sqid=sqid,
            name=customer_row[1],
            monthly_fee=customer_row[2],
            created_at=customer_row[3],
            updated_at=customer_row[4],
        )

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


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all customers (authenticated users only).

    Returns all customers with sqid generated on-the-fly.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        result = db.conn.execute(
            """
            SELECT id, name, monthly_fee, created_at, updated_at
            FROM customers
            WHERE is_active = true
            ORDER BY name ASC
            """
        ).fetchall()

        customers = [
            CustomerResponse(
                sqid=sqids_helper.encode_single(row[0]),
                name=row[1],
                monthly_fee=row[2],
                created_at=row[3],
                updated_at=row[4],
            )
            for row in result
        ]

        return customers

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{sqid}", response_model=CustomerResponse)
async def get_customer(
    sqid: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get customer by sqid.

    Decodes sqid to get customer_id, then returns customer details.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get customer_id
        try:
            customer_id = sqids_helper.decode_single(sqid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer sqid: {sqid}",
            )
        
        result = db.conn.execute(
            """
            SELECT id, name, monthly_fee, created_at, updated_at
            FROM customers
            WHERE id = ? AND is_active = true
            LIMIT 1
            """,
            [customer_id],
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {sqid}",
            )

        row = result[0]
        return CustomerResponse(
            sqid=sqid,
            name=row[1],
            monthly_fee=row[2],
            created_at=row[3],
            updated_at=row[4],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.patch("/{sqid}", response_model=CustomerResponse)
async def update_customer(
    sqid: str,
    update_data: CustomerUpdate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update customer (admin only).

    Can update name and/or monthly_fee.
    """
    try:
        sqids_helper = get_sqids_helper()
        
        # Decode sqid to get customer_id
        try:
            customer_id = sqids_helper.decode_single(sqid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer sqid: {sqid}",
            )
        
        # Check if customer exists
        customer = db.conn.execute(
            "SELECT id FROM customers WHERE id = ? AND is_active = true LIMIT 1",
            [customer_id],
        ).fetchall()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {sqid}",
            )

        # Build update query dynamically
        updates = []
        params = []

        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)

        if update_data.monthly_fee is not None:
            updates.append("monthly_fee = ?")
            params.append(update_data.monthly_fee)

        if not updates:
            # No updates provided, return existing customer
            return await get_customer(sqid, db, current_user)

        # Add updated_at and customer_id
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(customer_id)

        # Execute update
        query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ? RETURNING id, name, monthly_fee, created_at, updated_at"
        result = db.conn.execute(query, params).fetchall()

        db.conn.commit()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update customer",
            )

        row = result[0]
        return CustomerResponse(
            sqid=sqid,
            name=row[1],
            monthly_fee=row[2],
            created_at=row[3],
            updated_at=row[4],
        )

    except HTTPException:
        raise
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/{sqid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    sqid: str,
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
            customer_id = sqids_helper.decode_single(sqid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid customer sqid: {sqid}",
            )
        
        # Check if customer exists
        customer = db.conn.execute(
            "SELECT id FROM customers WHERE id = ? LIMIT 1",
            [customer_id],
        ).fetchall()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {sqid}",
            )

        # Soft delete
        db.conn.execute(
            "UPDATE customers SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            [customer_id],
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
