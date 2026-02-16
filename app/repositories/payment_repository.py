"""
Payment repository for data access operations.
"""

from typing import Optional, List
from .base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    """
    Payment repository handling all database operations for payments table.
    """

    def create(
        self,
        customer_id: int,
        payment_date: str,
        billing_month: int,
        billing_year: int,
        amount: int,
    ) -> Optional[tuple]:
        """Create a new payment."""
        query = """
            INSERT INTO payments (customer_id, payment_date, billing_month, billing_year, amount)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, customer_id, payment_date, billing_month, billing_year, amount, created_at, updated_at
        """
        result = self.execute_insert(
            query, [customer_id, payment_date, billing_month, billing_year, amount]
        )
        return result[0] if result else None

    def find_by_id(self, payment_id: int) -> Optional[tuple]:
        """Find payment by ID."""
        query = """
            SELECT id, customer_id, payment_date, billing_month, billing_year, 
                   amount, created_at, updated_at
            FROM payments
            WHERE id = ?
        """
        return self.execute_one(query, [payment_id])

    def find_all_with_filters(
        self,
        customer_id: Optional[int] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[tuple], int]:
        """
        Find all payments with optional filters and pagination.
        
        Returns:
            Tuple of (payments list, total count)
        """
        # Build base query
        query = """
            SELECT id, customer_id, payment_date, billing_month, billing_year, 
                   amount, created_at, updated_at
            FROM payments
            WHERE 1 = 1
        """
        params = []

        # Add filters
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)

        if year:
            query += " AND billing_year = ?"
            params.append(year)

        if month:
            query += " AND billing_month = ?"
            params.append(month)

        # Get total count
        count_query = "SELECT COUNT(*) FROM payments WHERE 1 = 1"
        count_params = []

        if customer_id:
            count_query += " AND customer_id = ?"
            count_params.append(customer_id)

        if year:
            count_query += " AND billing_year = ?"
            count_params.append(year)

        if month:
            count_query += " AND billing_month = ?"
            count_params.append(month)

        total = self.count(count_query, count_params)

        # Add pagination
        paginated_query, offset = self.build_pagination_query(
            query, page, per_page, "billing_year DESC, billing_month DESC, payment_date DESC"
        )
        params.extend([per_page, offset])

        payments = self.execute_query(paginated_query, params)

        return payments, total

    def find_by_customer_and_period(
        self, customer_id: int, billing_month: int, billing_year: int
    ) -> Optional[tuple]:
        """Find payment by customer and billing period."""
        query = """
            SELECT id, customer_id, payment_date, billing_month, billing_year, 
                   amount, created_at, updated_at
            FROM payments
            WHERE customer_id = ? AND billing_month = ? AND billing_year = ?
        """
        return self.execute_one(query, [customer_id, billing_month, billing_year])

    def exists_for_period(self, customer_id: int, billing_month: int, billing_year: int) -> bool:
        """Check if payment exists for customer in specific period."""
        query = """
            SELECT 1 FROM payments 
            WHERE customer_id = ? AND billing_month = ? AND billing_year = ?
        """
        result = self.execute_one(query, [customer_id, billing_month, billing_year])
        return result is not None

    def find_by_customer_and_year(self, customer_id: int, year: int) -> List[tuple]:
        """Find all payments for a customer in a specific year."""
        query = """
            SELECT id, customer_id, payment_date, billing_month, billing_year, 
                   amount, created_at, updated_at
            FROM payments
            WHERE customer_id = ? AND billing_year = ?
            ORDER BY billing_month ASC
        """
        return self.execute_query(query, [customer_id, year])

    def find_all_by_year(self, year: int) -> List[tuple]:
        """Find all payments in a specific year."""
        query = """
            SELECT id, customer_id, payment_date, billing_month, billing_year, 
                   amount, created_at, updated_at
            FROM payments
            WHERE billing_year = ?
            ORDER BY customer_id, billing_month ASC
        """
        return self.execute_query(query, [year])

    def get_payment_summary_by_year(self, year: int) -> Optional[tuple]:
        """Get total expected and collected payment for a year."""
        query = """
            SELECT
                SUM(c.monthly_fee) * 12 as total_expected,
                COALESCE(SUM(p.amount), 0) as total_collected
            FROM customers c
            LEFT JOIN payments p ON c.id = p.customer_id AND p.billing_year = ?
            WHERE c.is_active = true
        """
        return self.execute_one(query, [year])

    def delete(self, payment_id: int) -> int:
        """Delete a payment record."""
        query = "DELETE FROM payments WHERE id = ?"
        return self.execute_delete(query, [payment_id])

    def update(
        self,
        payment_id: int,
        customer_id: Optional[int] = None,
        payment_date: Optional[str] = None,
        billing_month: Optional[int] = None,
        billing_year: Optional[int] = None,
        amount: Optional[int] = None,
    ) -> Optional[tuple]:
        """Update payment fields."""
        updates = []
        params = []

        if customer_id is not None:
            updates.append("customer_id = ?")
            params.append(customer_id)

        if payment_date is not None:
            updates.append("payment_date = ?")
            params.append(payment_date)

        if billing_month is not None:
            updates.append("billing_month = ?")
            params.append(billing_month)

        if billing_year is not None:
            updates.append("billing_year = ?")
            params.append(billing_year)

        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)

        if not updates:
            return None

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(payment_id)

        query = f"""
            UPDATE payments
            SET {', '.join(updates)}
            WHERE id = ?
            RETURNING id, customer_id, payment_date, billing_month, billing_year, amount, created_at, updated_at
        """

        result = self.execute_insert(query, params)
        return result[0] if result else None

    def find_by_customer_year_month(
        self, customer_ids: List[int], year: int
    ) -> List[tuple]:
        """
        Find all payments for multiple customers in a specific year.
        Used for billing matrix.
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
