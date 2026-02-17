"""
User repository for data access operations.
"""

from typing import Optional, List, Dict, Any

from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    User repository handling database operations for users table.
    """

    def create(
        self,
        username: str,
        password_hash: str,
        role: str,
        is_active: bool = True,
        customer_id: Optional[int] = None,
    ) -> Optional[tuple]:
        """Create a new user."""
        query = """
            INSERT INTO users (username, password_hash, role, is_active, customer_id)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, username, role, is_active, created_at
        """
        result = self.execute_insert(
            query, [username, password_hash, role, is_active, customer_id]
        )
        return result[0] if result else None

    def find_by_username(self, username: str) -> Optional[tuple]:
        """Find user by username (includes password hash)."""
        query = """
            SELECT id, username, role, is_active, created_at, password_hash
            FROM users
            WHERE username = ?
        """
        return self.execute_one(query, [username])

    def find_by_id(self, user_id: int) -> Optional[tuple]:
        """Find user by ID."""
        query = """
            SELECT id, username, role, is_active, created_at
            FROM users
            WHERE id = ?
        """
        return self.execute_one(query, [user_id])

    def find_by_id_with_password(self, user_id: int) -> Optional[tuple]:
        """Find user by ID including password hash."""
        query = """
            SELECT id, username, role, is_active, created_at, password_hash
            FROM users
            WHERE id = ?
        """
        return self.execute_one(query, [user_id])

    def exists_by_username(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a username exists, optionally excluding a user ID."""
        query = "SELECT 1 FROM users WHERE username = ?"
        params: List[Any] = [username]

        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)

        result = self.execute_one(query, params)
        return result is not None

    def list_users(self, page: int = 1, per_page: int = 10) -> tuple[List[tuple], int]:
        """List users with pagination."""
        base_query = """
            SELECT id, username, role, is_active, created_at
            FROM users
        """
        count_query = "SELECT COUNT(*) FROM users"
        total = self.count(count_query)

        paginated_query, offset = self.build_pagination_query(
            base_query, page, per_page, "id DESC"
        )
        rows = self.execute_query(paginated_query, [per_page, offset])
        return rows, total

    def update(self, user_id: int, updates: Dict[str, Any]) -> Optional[tuple]:
        """Update user fields and return updated row."""
        if not updates:
            return self.find_by_id(user_id)

        update_parts = []
        params: List[Any] = []

        for field, value in updates.items():
            update_parts.append(f"{field} = ?")
            params.append(value)

        update_parts.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"""
            UPDATE users
            SET {', '.join(update_parts)}
            WHERE id = ?
            RETURNING id, username, role, is_active, created_at
        """
        result = self.execute_insert(query, params)
        return result[0] if result else None

    def update_password(self, user_id: int, password_hash: str) -> int:
        """Update user password hash."""
        query = """
            UPDATE users
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.execute_update(query, [password_hash, user_id])

    def delete(self, user_id: int) -> int:
        """Delete user by ID."""
        query = "DELETE FROM users WHERE id = ?"
        return self.execute_delete(query, [user_id])
