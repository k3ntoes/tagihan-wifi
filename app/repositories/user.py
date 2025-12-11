from typing import Optional

import duckdb

from app.core.auth import get_password_hash
from app.models.user import UserCreate, UserUpdate


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: duckdb.DuckDBPyConnection):
        self.db = db

    def get_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        result = self.db.execute(
            "SELECT * FROM users WHERE username = ?", [username]
        ).fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        result = self.db.execute(
            "SELECT * FROM users WHERE email = ?", [email]
        ).fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def get_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        result = self.db.execute(
            "SELECT * FROM users WHERE id = ?", [user_id]
        ).fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def create(self, user: UserCreate) -> dict:
        """Create a new user."""
        hashed_password = get_password_hash(user.password)

        result = self.db.execute(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (?, ?, ?, ?)
            RETURNING *
            """,
            [user.username, user.email, hashed_password, user.role.value],
        ).fetchone()

        self.db.commit()

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def update(self, user_id: int, user_update: UserUpdate) -> Optional[dict]:
        """Update user data."""
        # Get current user
        current_user = self.get_by_id(user_id)
        if not current_user:
            return None

        # Build update query dynamically
        update_fields = []
        params = []

        if user_update.email is not None:
            update_fields.append("email = ?")
            params.append(user_update.email)

        if user_update.password is not None:
            update_fields.append("hashed_password = ?")
            params.append(get_password_hash(user_update.password))

        if user_update.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(user_update.is_active)

        if user_update.role is not None:
            update_fields.append("role = ?")
            params.append(user_update.role.value)

        if user_update.pelanggan_id is not None:
            update_fields.append("pelanggan_id = ?")
            params.append(user_update.pelanggan_id)

        if not update_fields:
            return current_user

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"""
            UPDATE users 
            SET {", ".join(update_fields)}
            WHERE id = ?
            RETURNING *
        """

        result = self.db.execute(query, params).fetchone()
        self.db.commit()

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def delete(self, user_id: int) -> bool:
        """Soft delete user (set is_active to False)."""
        result = self.db.execute(
            """
            UPDATE users 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING id
            """,
            [user_id],
        ).fetchone()

        self.db.commit()
        return result is not None

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password."""
        hashed_password = get_password_hash(new_password)
        result = self.db.execute(
            """
            UPDATE users
            SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING id
            """,
            [hashed_password, user_id],
        ).fetchone()
        self.db.commit()
        return result is not None

    def set_reset_token(self, email: str, token: str, expires_at) -> bool:
        """Store password reset token for user."""
        result = self.db.execute(
            """
            UPDATE users
            SET reset_token = ?, reset_token_expires = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
            RETURNING id
            """,
            [token, expires_at, email],
        ).fetchone()
        self.db.commit()
        return result is not None

    def get_by_reset_token(self, token: str) -> Optional[dict]:
        """Get user by reset token if not expired."""
        result = self.db.execute(
            """
            SELECT * FROM users
            WHERE reset_token = ? AND reset_token_expires > CURRENT_TIMESTAMP
            """,
            [token],
        ).fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.db.description]
        return dict(zip(columns, result))

    def clear_reset_token(self, user_id: int) -> bool:
        """Clear reset token after use."""
        result = self.db.execute(
            """
            UPDATE users
            SET reset_token = NULL, reset_token_expires = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING id
            """,
            [user_id],
        ).fetchone()
        self.db.commit()
        return result is not None
