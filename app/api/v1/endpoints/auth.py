"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, status, HTTPException

from app.core.auth import AuthService, get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import (
    UserLogin, TokenResponse, UserCreate, UserResponse, SingleUserResponse,
    PasswordChange, UserUpdateAdmin, PaginatedUserResponse, PaginationMeta
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=SingleUserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Database = Depends(get_db)):
    """Register new user"""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data.username, user_data.password, user_data.role)
    return SingleUserResponse(data=user)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Database = Depends(get_db)):
    """Login and get JWT token"""
    auth_service = AuthService(db)
    return auth_service.authenticate_user(credentials.username, credentials.password)


@router.get("/me", response_model=SingleUserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """Get current user info"""
    user = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        [int(current_user["sub"])],
    ).fetchall()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user_data = user[0]
    from app.schemas import RoleEnum
    user = UserResponse(
        id=user_data[0],
        username=user_data[1],
        role=RoleEnum(user_data[2]),
        is_active=user_data[3],
        created_at=user_data[4],
    )
    return SingleUserResponse(data=user)


@router.post("/change-password", response_model=SingleUserResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Change current user password"""
    auth_service = AuthService(db)
    user_id = int(current_user["sub"])
    
    # Verify old password
    user_row = db.conn.execute(
        "SELECT username, password FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify old password matches
    if not auth_service.verify_password(password_data.old_password, user_row[1]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    
    # Update password
    hashed_new_password = auth_service.hash_password(password_data.new_password)
    db.conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        [hashed_new_password, user_id],
    )
    db.conn.commit()
    
    # Return updated user info
    user = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    from app.schemas import RoleEnum
    user_response = UserResponse(
        id=user[0],
        username=user[1],
        role=RoleEnum(user[2]),
        is_active=user[3],
        created_at=user[4],
    )
    return SingleUserResponse(data=user_response)


@router.get("/users", response_model=PaginatedUserResponse)
async def list_users(
    page: int = 1,
    per_page: int = 10,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """List all users (admin only)"""
    from app.schemas import RoleEnum
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    total = db.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    
    # Get paginated users
    users_rows = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users ORDER BY id DESC LIMIT ? OFFSET ?",
        [per_page, offset],
    ).fetchall()
    
    users = [
        UserResponse(
            id=row[0],
            username=row[1],
            role=RoleEnum(row[2]),
            is_active=row[3],
            created_at=row[4],
        )
        for row in users_rows
    ]
    
    # Calculate pagination meta
    total_pages = (total + per_page - 1) // per_page
    meta = PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    
    return PaginatedUserResponse(data=users, meta=meta)


@router.get("/users/{user_id}", response_model=SingleUserResponse)
async def get_user(
    user_id: int,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Get specific user (admin only)"""
    user = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    from app.schemas import RoleEnum
    user_response = UserResponse(
        id=user[0],
        username=user[1],
        role=RoleEnum(user[2]),
        is_active=user[3],
        created_at=user[4],
    )
    return SingleUserResponse(data=user_response)


@router.patch("/users/{user_id}", response_model=SingleUserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateAdmin,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Update user (admin only)"""
    auth_service = AuthService(db)
    
    # Check if user exists
    user = db.conn.execute(
        "SELECT id FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if username already exists (if updating username)
    if update_data.username:
        existing = db.conn.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            [update_data.username, user_id],
        ).fetchone()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    # Build update query
    update_fields = []
    update_values = []
    
    if update_data.username:
        update_fields.append("username = ?")
        update_values.append(update_data.username)
    
    if update_data.password:
        hashed_password = auth_service.hash_password(update_data.password)
        update_fields.append("password = ?")
        update_values.append(hashed_password)
    
    if update_data.role is not None:
        update_fields.append("role = ?")
        update_values.append(update_data.role.value)
    
    if update_data.is_active is not None:
        update_fields.append("is_active = ?")
        update_values.append(update_data.is_active)
    
    # Execute update if there are fields to update
    if update_fields:
        update_values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        db.conn.execute(query, update_values)
        db.conn.commit()
    
    # Return updated user
    user = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    from app.schemas import RoleEnum
    user_response = UserResponse(
        id=user[0],
        username=user[1],
        role=RoleEnum(user[2]),
        is_active=user[3],
        created_at=user[4],
    )
    return SingleUserResponse(data=user_response)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Delete user (admin only)"""
    # Check if user exists
    user = db.conn.execute(
        "SELECT id FROM users WHERE id = ?",
        [user_id],
    ).fetchone()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Prevent deleting own account
    if int(current_user["sub"]) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    
    # Delete user
    db.conn.execute("DELETE FROM users WHERE id = ?", [user_id])
    db.conn.commit()
    
    return None

