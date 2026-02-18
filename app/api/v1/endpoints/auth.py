"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import (
    UserLogin,
    TokenResponse,
    UserCreate,
    SingleUserResponse,
    PasswordChange,
    UserUpdateAdmin,
    PaginatedUserResponse,
)
from app.services import AuthService

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
    auth_service = AuthService(db)
    user = auth_service.get_me(int(current_user["sub"]))
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
    user = auth_service.change_password(user_id, password_data.old_password, password_data.new_password)
    return SingleUserResponse(data=user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Refresh JWT token (prolongs session)"""
    auth_service = AuthService(db)
    return auth_service.refresh_token(int(current_user["sub"]))


@router.get("/users", response_model=PaginatedUserResponse)
async def list_users(
    page: int = 1,
    per_page: int = 10,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """List all users (admin only)"""
    auth_service = AuthService(db)
    users, meta = auth_service.list_users(page=page, per_page=per_page)
    return PaginatedUserResponse(data=users, meta=meta)


@router.get("/users/{user_id}", response_model=SingleUserResponse)
async def get_user(
    user_id: int,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Get specific user (admin only)"""
    auth_service = AuthService(db)
    user = auth_service.get_user(user_id)
    return SingleUserResponse(data=user)


@router.patch("/users/{user_id}", response_model=SingleUserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateAdmin,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Update user (admin only)"""
    auth_service = AuthService(db)
    user = auth_service.update_user_admin(user_id, update_data)
    return SingleUserResponse(data=user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """Delete user (admin only)"""
    auth_service = AuthService(db)
    auth_service.delete_user(user_id, int(current_user["sub"]))
    return None

