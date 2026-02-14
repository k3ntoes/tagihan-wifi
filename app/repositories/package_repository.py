"""
Package repository for data access operations.
"""

from typing import Optional, List
from .base_repository import BaseRepository


class PackageRepository(BaseRepository):
    """
    Package repository handling all database operations for packages table.
    """

    def create(self, name: str, speed: int, price: int) -> Optional[tuple]:
        """Create a new package."""
        query = """
            INSERT INTO packages (name, speed, price)
            VALUES (?, ?, ?)
            RETURNING id, name, speed, price, is_active, created_at, updated_at
        """
        result = self.execute_insert(query, [name, speed, price])
        return result[0] if result else None

    def find_by_id(self, package_id: int, include_inactive: bool = False) -> Optional[tuple]:
        """Find package by ID."""
        query = """
            SELECT id, name, speed, price, is_active, created_at, updated_at
            FROM packages
            WHERE id = ?
        """
        if not include_inactive:
            query += " AND is_active = true"
        
        return self.execute_one(query, [package_id])

    def find_by_name(self, name: str) -> Optional[tuple]:
        """Find package by name (active only)."""
        query = """
            SELECT id, name, speed, price, is_active, created_at, updated_at
            FROM packages
            WHERE name = ? AND is_active = true
        """
        return self.execute_one(query, [name])

    def exists_by_name(self, name: str) -> bool:
        """Check if package with name exists (active only)."""
        query = "SELECT 1 FROM packages WHERE name = ? AND is_active = true"
        result = self.execute_one(query, [name])
        return result is not None

    def find_all_with_filters(
        self,
        name: Optional[str] = None,
        min_speed: Optional[int] = None,
        max_speed: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[tuple], int]:
        """
        Find all packages with optional filters and pagination.
        
        Returns:
            Tuple of (packages list, total count)
        """
        # Build base query
        query = "SELECT id, name, speed, price, is_active, created_at, updated_at FROM packages WHERE 1=1"
        params = []

        # Add filters
        if not include_inactive:
            query += " AND is_active = true"

        if name and name.strip():
            query += " AND LOWER(name) LIKE LOWER(?)"
            params.append(f"%{name.strip()}%")

        if min_speed is not None:
            query += " AND speed >= ?"
            params.append(min_speed)

        if max_speed is not None:
            query += " AND speed <= ?"
            params.append(max_speed)

        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)

        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)

        # Get total count
        count_query = "SELECT COUNT(*) FROM packages WHERE 1=1"
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

        total = self.count(count_query, count_params)

        # Add pagination
        paginated_query, offset = self.build_pagination_query(query, page, per_page, "name ASC")
        params.extend([per_page, offset])

        packages = self.execute_query(paginated_query, params)

        return packages, total

    def update(
        self,
        package_id: int,
        name: Optional[str] = None,
        speed: Optional[int] = None,
        price: Optional[int] = None,
    ) -> Optional[tuple]:
        """Update package fields."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if speed is not None:
            updates.append("speed = ?")
            params.append(speed)

        if price is not None:
            updates.append("price = ?")
            params.append(price)

        if not updates:
            return None

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(package_id)

        query = f"""
            UPDATE packages
            SET {', '.join(updates)}
            WHERE id = ? AND is_active = true
            RETURNING id, name, speed, price, is_active, created_at, updated_at
        """

        result = self.execute_insert(query, params)
        return result[0] if result else None

    def soft_delete(self, package_id: int) -> int:
        """Soft delete package by setting is_active to false."""
        query = """
            UPDATE packages
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = true
        """
        return self.execute_update(query, [package_id])

    def exists_by_id(self, package_id: int) -> bool:
        """Check if package exists and is active."""
        query = "SELECT 1 FROM packages WHERE id = ? AND is_active = true"
        result = self.execute_one(query, [package_id])
        return result is not None

    def find_all_active(self) -> List[tuple]:
        """Find all active packages."""
        query = """
            SELECT id, name, speed, price, is_active, created_at, updated_at
            FROM packages
            WHERE is_active = true
            ORDER BY name ASC
        """
        return self.execute_query(query)

    def has_customers(self, package_id: int) -> bool:
        """Check if package has any active customers."""
        query = """
            SELECT 1 FROM customers 
            WHERE package_id = ? AND is_active = true 
            LIMIT 1
        """
        result = self.execute_one(query, [package_id])
        return result is not None
