"""
Payment log parser for converting manual log entries to payment records.

Handles parsing of manual payment log entries in the format:
    "DD-MM-YYYY customer_name"

Example:
    "02-05-2025 opi" -> Payment on May 2, 2025. for customer named "opi"

The parser:
1. Extracts the date (DD-MM-YYYY format)
2. Finds the customer by name (case-insensitive)
3. Uses customer's monthly_fee as payment amount
4. Extracts billing month and year from the date
"""

import logging
import re
from datetime import date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.database import Database

logger = logging.getLogger(__name__)


class ParsedPayment(BaseModel):
    """Result from parsing a payment log entry."""
    model_config = {"arbitrary_types_allowed": True}
    
    customer_id: int
    customer_name: str
    payment_date: date
    billing_month: int
    billing_year: int
    amount: int


class PaymentLogParser:
    """
    Parser for converting manual payment log entries to structured payment data.
    
    Supports format: "DD-MM-YYYY customer_name"
    
    Features:
    - Case-insensitive customer name matching
    - Automatic billing month/year extraction from payment date
    - Customer lookup by name
    - Validation and error handling
    """

    # Regex pattern: DD-MM-YYYY followed by customer name
    # Format: "02-05-2025 opi" or "02-05-2025  opi" (multiple spaces ok)
    PATTERN = r'^(\d{2})-(\d{2})-(\d{4})\s+(.+)$'

    def __init__(self, db: Database):
        """
        Initialize parser with database connection.

        Args:
            db: Database instance for customer lookups
        """
        self.db = db

    def parse(self, log_entry: str) -> Optional[ParsedPayment]:
        """
        Parse a manual payment log entry.

        Args:
            log_entry: String in format "DD-MM-YYYY customer_name"

        Returns:
            ParsedPayment object if successful, None if parsing fails

        Raises:
            ValueError: If date is invalid or customer not found
        """
        # Strip whitespace
        log_entry = log_entry.strip()

        # Try to match pattern
        match = re.match(self.PATTERN, log_entry)
        if not match:
            logger.error(f"Invalid log entry format: {log_entry}")
            raise ValueError(
                f'Invalid format. Expected: "DD-MM-YYYY customer_name", got: "{log_entry}"'
            )

        # Extract parts
        day, month, year, customer_name = match.groups()

        try:
            day = int(day)
            month = int(month)
            year = int(year)
            customer_name = customer_name.strip()
        except ValueError as e:
            logger.error(f"Failed to parse date components: {e}")
            raise ValueError(f"Invalid date format: {day}-{month}-{year}")

        # Validate date components
        if not (1 <= day <= 31):
            raise ValueError(f"Invalid day: {day}")
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}")
        if not (2020 <= year <= 2100):
            raise ValueError(f"Invalid year: {year}")

        # Validate customer name not empty
        if not customer_name:
            raise ValueError("Customer name cannot be empty")

        # Try to create valid date
        try:
            payment_date = datetime(year, month, day).date()
        except ValueError as e:
            logger.error(f"Invalid date: {day}-{month}-{year}: {e}")
            raise ValueError(f"Invalid date: {day}-{month}-{year}")

        # Find customer by name (case-insensitive)
        customer = self._find_customer_by_name(customer_name)
        if not customer:
            logger.error(f"Customer not found: {customer_name}")
            raise ValueError(f"Customer not found: {customer_name}")

        customer_id = customer[0]
        monthly_fee = customer[2]

        logger.info(
            f"Parsed payment: customer={customer_name} (id={customer_id}), "
            f"date={payment_date}, amount={monthly_fee}"
        )

        return ParsedPayment(
            customer_id=customer_id,
            customer_name=customer_name,
            payment_date=payment_date,
            billing_month=month,
            billing_year=year,
            amount=monthly_fee,
        )

    def _find_customer_by_name(self, name: str) -> Optional[tuple]:
        """
        Find customer by name (case-insensitive search).

        Args:
            name: Customer name to search

        Returns:
            Tuple of (id, name, monthly_fee) if found, None otherwise
        """
        try:
            # Case-insensitive search
            result = self.db.conn.execute(
                """
                SELECT id, name, monthly_fee 
                FROM customers 
                WHERE LOWER(name) = LOWER(?)
                LIMIT 1
                """,
                [name],
            ).fetchall()

            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Database error searching for customer: {e}")
            raise ValueError(f"Database error: {e}")

    def batch_parse(self, log_entries: list[str]) -> tuple[list[ParsedPayment], list[dict]]:
        """
        Parse multiple log entries.

        Args:
            log_entries: List of log entry strings

        Returns:
            Tuple of (successful_payments, errors)
            errors is list of dicts with 'entry' and 'error' keys
        """
        successful = []
        errors = []

        for entry in log_entries:
            try:
                parsed = self.parse(entry)
                if parsed:
                    successful.append(parsed)
            except ValueError as e:
                errors.append({"entry": entry, "error": str(e)})
                logger.warning(f"Failed to parse entry '{entry}': {e}")

        return successful, errors


# Convenience function
def parse_payment_log(log_entry: str, db: Database) -> ParsedPayment:
    """
    Parse a single payment log entry.

    Args:
        log_entry: String in format "DD-MM-YYYY customer_name"
        db: Database instance

    Returns:
        ParsedPayment object

    Raises:
        ValueError: If parsing fails
    """
    parser = PaymentLogParser(db)
    return parser.parse(log_entry)
