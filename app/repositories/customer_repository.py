"""
Customer repository for data access operations.
"""

from typing import List, Optional

from .base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    """
    Customer repository handling all database operations for customers table.
    """

    def create(self, name: str, package_id: Optional[int], monthly_fee: int) -> Optional[tuple]:
        """Create a new customer."""
        query = """
            INSERT INTO customers (name, package_id, monthly_fee)
            VALUES (?, ?, ?)
            RETURNING id, name, package_id, monthly_fee, created_at, updated_at
        """
        result = self.execute_insert(query, [name, package_id, monthly_fee])
        return result[0] if result else None

    def find_by_id(self, customer_id: int) -> Optional[tuple]:
        """Find customer by ID."""
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name, 
                   c.monthly_fee, c.package_start_date, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.id = ? AND c.is_active = true
        """
        return self.execute_one(query, [customer_id])

    def find_all_with_filters(
        self,
        name: Optional[str] = None,
        package_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[tuple], int]:
        """
        Find all customers with optional filters and pagination.

        Returns:
            Tuple of (customers list, total count)
        """
        # Build base query
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name, 
                   c.monthly_fee, c.package_start_date, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.is_active = true
        """
        params = []

        # Add filters
        if name and name.strip():
            query += " AND LOWER(c.name) LIKE LOWER(?)"
            params.append(f"%{name.strip()}%")

        if package_id is not None:
            query += " AND c.package_id = ?"
            params.append(package_id)

        # Get total count
        count_query = """
            SELECT COUNT(*)
            FROM customers c
            WHERE c.is_active = true
        """
        count_params = []

        if name and name.strip():
            count_query += " AND LOWER(c.name) LIKE LOWER(?)"
            count_params.append(f"%{name.strip()}%")

        if package_id is not None:
            count_query += " AND c.package_id = ?"
            count_params.append(package_id)

        total = self.count(count_query, count_params)

        # Add pagination
        paginated_query, offset = self.build_pagination_query(query, page, per_page, "c.name ASC")
        params.extend([per_page, offset])

        customers = self.execute_query(paginated_query, params)

        return customers, total

    def find_all_inactive_with_filters(
        self,
        name: Optional[str] = None,
        package_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[tuple], int]:
        """
        Find all inactive customers with optional filters and pagination.

        Returns:
            Tuple of (customers list, total count)
        """
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name,
                   c.monthly_fee, c.package_start_date, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.is_active = false
        """
        params: List[object] = []

        if name and name.strip():
            query += " AND LOWER(c.name) LIKE LOWER(?)"
            params.append(f"%{name.strip()}%")

        if package_id is not None:
            query += " AND c.package_id = ?"
            params.append(package_id)

        count_query = """
            SELECT COUNT(*)
            FROM customers c
            WHERE c.is_active = false
        """
        count_params: List[object] = []

        if name and name.strip():
            count_query += " AND LOWER(c.name) LIKE LOWER(?)"
            count_params.append(f"%{name.strip()}%")

        if package_id is not None:
            count_query += " AND c.package_id = ?"
            count_params.append(package_id)

        total = self.count(count_query, count_params)

        paginated_query, offset = self.build_pagination_query(query, page, per_page, "c.name ASC")
        params.extend([per_page, offset])

        customers = self.execute_query(paginated_query, params)
        return customers, total

    def update(
        self,
        customer_id: int,
        name: Optional[str] = None,
        package_id: Optional[int] = None,
        monthly_fee: Optional[int] = None,
        package_start_date: Optional[str] = None,
    ) -> Optional[tuple]:
        """Update customer fields."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if package_id is not None:
            updates.append("package_id = ?")
            params.append(package_id)

        if monthly_fee is not None:
            updates.append("monthly_fee = ?")
            params.append(monthly_fee)

        if package_start_date is not None:
            updates.append("package_start_date = ?")
            params.append(package_start_date)

        if not updates:
            return None

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(customer_id)

        query = f"""
            UPDATE customers
            SET {', '.join(updates)}
            WHERE id = ? AND is_active = true
            RETURNING id, name, package_id, monthly_fee, package_start_date, created_at, updated_at
        """

        result = self.execute_insert(query, params)
        return result[0] if result else None

    def soft_delete(self, customer_id: int) -> int:
        """Soft delete customer by setting is_active to false."""
        query = """
            UPDATE customers
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = true
        """
        return self.execute_update(query, [customer_id])

    def exists_by_id(self, customer_id: int) -> bool:
        """Check if customer exists and is active."""
        query = "SELECT 1 FROM customers WHERE id = ? AND is_active = true"
        result = self.execute_one(query, [customer_id])
        return result is not None

    def find_all_active(self) -> List[tuple]:
        """Find all active customers."""
        query = """
            SELECT id, name, monthly_fee
            FROM customers
            WHERE is_active = true
            ORDER BY name ASC
        """
        return self.execute_query(query)

    def find_by_ids(self, customer_ids: List[int]) -> List[tuple]:
        """Find customers by list of IDs."""
        if not customer_ids:
            return []

        placeholders = ",".join(["?"] * len(customer_ids))
        query = f"""
            SELECT c.id, c.name, c.package_id, p.name as package_name, 
                   c.monthly_fee, c.package_start_date, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.id IN ({placeholders}) AND c.is_active = true
        """
        return self.execute_query(query, customer_ids)

    def enable_customer(self, customer_id: int) -> int:
        """Enable/activate a customer by setting is_active to true."""
        query = """
            UPDATE customers
            SET is_active = true, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = false
        """
        return self.execute_update(query, [customer_id])

    def find_inactive_customer(self, customer_id: int) -> Optional[tuple]:
        """Find inactive customer by ID (for enabling)."""
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name, 
                   c.monthly_fee, c.package_start_date, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.id = ? AND c.is_active = false
        """
        return self.execute_one(query, [customer_id])
