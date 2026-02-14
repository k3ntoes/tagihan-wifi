"""
Base repository class with common database operations.
"""

from typing import Optional, List, Any, Tuple
from app.db.database import Database


class BaseRepository:
    """
    Base repository class providing common database operations.
    Similar to JpaRepository in Spring Boot.
    """

    def __init__(self, db: Database):
        self.db = db
        self.conn = db.conn

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[tuple]:
        """Execute a SELECT query and return all results."""
        if params is None:
            params = []
        return self.conn.execute(query, params).fetchall()

    def execute_one(self, query: str, params: Optional[List[Any]] = None) -> Optional[tuple]:
        """Execute a SELECT query and return one result."""
        if params is None:
            params = []
        return self.conn.execute(query, params).fetchone()

    def execute_insert(self, query: str, params: Optional[List[Any]] = None) -> List[tuple]:
        """Execute an INSERT query with RETURNING clause."""
        if params is None:
            params = []
        result = self.conn.execute(query, params).fetchall()
        return result

    def execute_update(self, query: str, params: Optional[List[Any]] = None) -> int:
        """Execute an UPDATE query and return affected rows count."""
        if params is None:
            params = []
        cursor = self.conn.execute(query, params)
        return cursor.rowcount

    def execute_delete(self, query: str, params: Optional[List[Any]] = None) -> int:
        """Execute a DELETE query and return affected rows count."""
        if params is None:
            params = []
        cursor = self.conn.execute(query, params)
        return cursor.rowcount

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.conn.rollback()

    def count(self, query: str, params: Optional[List[Any]] = None) -> int:
        """Execute a COUNT query and return the count."""
        if params is None:
            params = []
        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else 0

    def build_pagination_query(
        self, base_query: str, page: int, per_page: int, order_by: str = "id ASC"
    ) -> Tuple[str, int]:
        """
        Build a paginated query with offset and limit.
        
        Args:
            base_query: Base SQL query without ORDER BY/LIMIT
            page: Page number (1-indexed)
            per_page: Items per page
            order_by: ORDER BY clause (default: "id ASC")
            
        Returns:
            Tuple of (query with pagination, offset)
        """
        offset = (page - 1) * per_page
        query = f"{base_query} ORDER BY {order_by} LIMIT ? OFFSET ?"
        return query, offset
