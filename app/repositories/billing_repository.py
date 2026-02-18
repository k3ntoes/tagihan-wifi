"""
Billing repository for data access operations.
"""

from typing import List, Optional
from .base_repository import BaseRepository


class BillingRepository(BaseRepository):
    """
    Billing repository handling database operations for billing matrix views.
    """

    def find_customers_with_filters(
        self,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[tuple], int]:
        """
        Find customers for billing matrix with optional filters.
        
        Returns:
            Tuple of (customers list, total count)
        """
        # Build base query with package JOIN
        query = """
            SELECT c.id, c.name, c.monthly_fee, c.package_start_date, c.package_id, p.id as package_db_id, p.name as package_name
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.is_active = true
        """
        params = []

        # Add customer_id filter
        if customer_id is not None:
            query += " AND c.id = ?"
            params.append(customer_id)

        # Add customer_name filter
        if customer_name and customer_name.strip():
            query += " AND LOWER(c.name) LIKE LOWER(?)"
            params.append(f"%{customer_name.strip()}%")

        # Get total count
        count_query = "SELECT COUNT(*) FROM customers c WHERE c.is_active = true"
        count_params = []

        if customer_id is not None:
            count_query += " AND c.id = ?"
            count_params.append(customer_id)

        if customer_name and customer_name.strip():
            count_query += " AND LOWER(c.name) LIKE LOWER(?)"
            count_params.append(f"%{customer_name.strip()}%")

        total = self.count(count_query, count_params)

        # Add pagination
        paginated_query, offset = self.build_pagination_query(query, page, per_page, "c.name ASC")
        params.extend([per_page, offset])

        customers = self.execute_query(paginated_query, params)

        return customers, total

    def find_payments_by_customer_and_year(
        self, customer_id: int, year: int
    ) -> List[tuple]:
        """
        Find all payments for a customer in a specific year.
        
        Returns:
            List of tuples (billing_month, amount, payment_date)
        """
        query = """
            SELECT billing_month, amount, payment_date
            FROM payments
            WHERE customer_id = ? AND billing_year = ?
            ORDER BY billing_month ASC
        """
        return self.execute_query(query, [customer_id, year])

    def find_payments_by_customers_and_year(
        self, customer_ids: List[int], year: int
    ) -> List[tuple]:
        """
        Find all payments for multiple customers in a specific year.
        
        Returns:
            List of tuples (customer_id, billing_month, amount, payment_date)
        """
        if not customer_ids:
            return []

        placeholders = ','.join(['?'] * len(customer_ids))
        query = f"""
            SELECT customer_id, billing_month, amount, payment_date
            FROM payments
            WHERE customer_id IN ({placeholders}) AND billing_year = ?
            ORDER BY customer_id, billing_month ASC
        """
        params = customer_ids + [year]
        return self.execute_query(query, params)

    def get_billing_summary(self, year: int) -> Optional[tuple]:
        """
        Get billing summary for a specific year.
        
        Returns:
            Tuple of (customer_count, total_expected, total_collected)
        """
        # Get active customers count
        customer_count = self.count(
            "SELECT COUNT(*) FROM customers WHERE is_active = true"
        )

        # Calculate totals
        query = """
            SELECT
                SUM(c.monthly_fee) * 12 as total_expected,
                COALESCE(SUM(p.amount), 0) as total_collected
            FROM customers c
            LEFT JOIN payments p ON c.id = p.customer_id AND p.billing_year = ?
            WHERE c.is_active = true
        """
        totals = self.execute_one(query, [year])

        if totals:
            return (customer_count, totals[0] or 0, totals[1] or 0)
        
        return (customer_count, 0, 0)

    def count_active_customers(self) -> int:
        """Count all active customers."""
        return self.count("SELECT COUNT(*) FROM customers WHERE is_active = true")
