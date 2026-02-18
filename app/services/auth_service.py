"""
Auth service for authentication and user management operations.
"""

from typing import List, Tuple

from fastapi import HTTPException, status

from app.core.auth import PasswordManager, TokenManager
from app.db.database import Database
from app.repositories import UserRepository
from app.schemas import RoleEnum, UserResponse, TokenResponse, PaginationMeta, UserUpdateAdmin


class AuthService:
    """
    Auth service handling authentication and user management.
    """

    def __init__(self, db: Database):
        self.db = db
        self.user_repo = UserRepository(db)

    def create_user(self, username: str, password: str, role: RoleEnum) -> UserResponse:
        """Create a new user."""
        try:
            if self.user_repo.exists_by_username(username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )

            password_hash = PasswordManager.hash_password(password)
            row = self.user_repo.create(username, password_hash, role.value, True)

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user",
                )

            self.db.conn.commit()
            return self._build_user_response(row)
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def authenticate_user(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token."""
        user = self.user_repo.find_by_username(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        user_id, username_val, role, is_active, created_at, password_hash = user

        if not is_active or not PasswordManager.verify_password(password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        return TokenManager.create_access_token(user_id, username_val, role)

    def get_me(self, user_id: int) -> UserResponse:
        """Get current user info."""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return self._build_user_response(user)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> UserResponse:
        """Change current user password."""
        try:
            user = self.user_repo.find_by_id_with_password(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            password_hash = user[5]
            if not PasswordManager.verify_password(old_password, password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Old password is incorrect",
                )

            new_hash = PasswordManager.hash_password(new_password)
            self.user_repo.update_password(user_id, new_hash)
            self.db.conn.commit()

            updated = self.user_repo.find_by_id(user_id)
            return self._build_user_response(updated)
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def list_users(self, page: int = 1, per_page: int = 10) -> Tuple[List[UserResponse], PaginationMeta]:
        """List users with pagination."""
        rows, total = self.user_repo.list_users(page=page, per_page=per_page)
        users = [self._build_user_response(row) for row in rows]

        total_pages = (total + per_page - 1) // per_page
        meta = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return users, meta

    def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return self._build_user_response(user)

    def update_user_admin(self, user_id: int, update_data: UserUpdateAdmin) -> UserResponse:
        """Update user (admin only)."""
        try:
            existing = self.user_repo.find_by_id(user_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if update_data.username and self.user_repo.exists_by_username(
                update_data.username, exclude_id=user_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )

            updates = {}
            if update_data.username:
                updates["username"] = update_data.username

            if update_data.password:
                updates["password_hash"] = PasswordManager.hash_password(update_data.password)

            if update_data.role is not None:
                updates["role"] = update_data.role.value

            if update_data.is_active is not None:
                updates["is_active"] = update_data.is_active

            updated = self.user_repo.update(user_id, updates)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user",
                )

            self.db.conn.commit()
            return self._build_user_response(updated)
        except HTTPException:
            self.db.conn.rollback()
            raise
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )

    def delete_user(self, user_id: int, current_user_id: int) -> None:
        """Delete user (admin only)."""
        try:
            if current_user_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account",
                )

            user = self.user_repo.find_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            self.user_repo.delete(user_id)
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

    def refresh_token(self, user_id: int) -> TokenResponse:
        """Refresh access token for current user."""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        user_id_val, username, role, is_active, created_at = user
        
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )
        
        return TokenManager.create_access_token(user_id_val, username, role)

    def _build_user_response(self, row: tuple) -> UserResponse:
        """Build UserResponse from database row."""
        return UserResponse(
            id=row[0],
            username=row[1],
            role=RoleEnum(row[2]),
            is_active=bool(row[3]),
            created_at=row[4],
        )
