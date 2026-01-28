"""
Database module for DuckDB persistence and schema management.

Best Practices Applied:
- Proper data types (TINYINT for month, SMALLINT for year)
- SEQUENCE for auto-increment IDs
- Composite indexes for common queries
- Optimized memory settings
- Prepared statements for efficiency
"""

import logging
from contextlib import contextmanager
from pathlib import Path

import duckdb

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for DuckDB persistent storage.
    Handles connection pooling and schema initialization with best practices.

    DuckDB optimizations:
    - Memory-efficient data types
    - Compound indexes for common query patterns
    - Proper transaction handling
    - Connection pooling via singleton pattern
    """

    def __init__(self, database_path: str = None, read_only: bool = False):
        """
        Initialize database connection.

        Args:
            database_path: Path to DuckDB file. Defaults to settings.DATABASE_PATH
            read_only: If True, open database in read-only mode
        """
        self.database_path = database_path or settings.DATABASE_PATH
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        config = {
            "threads": settings.DB_THREADS,
            "memory_limit": settings.DB_MEMORY_LIMIT,
            "max_memory": settings.DB_MAX_MEMORY,
        }

        try:
            self.conn = duckdb.connect(self.database_path, read_only=read_only, config=config)
            logger.info(f"Connected to DuckDB: {self.database_path}")

            if not read_only:
                self._set_pragmas()

            self._initialize_schema()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _set_pragmas(self):
        """Set optimal pragma settings for DuckDB performance."""
        pragmas = [
            "PRAGMA threads = 4",
            "PRAGMA memory_limit = '2GB'",
            "PRAGMA default_null_order = 'nulls_last'",
            "PRAGMA enable_object_cache = true",
            "PRAGMA force_compression = 'auto'",
        ]

        for pragma in pragmas:
            try:
                self.conn.execute(pragma)
            except Exception as e:
                logger.warning(f"Could not set pragma '{pragma}': {e}")

    def _initialize_schema(self):
        """Create tables and indexes if they don't exist."""
        try:
            # Create sequences for auto-increment
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_customers START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_payments START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_users START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_packages START 1")

            # Create packages table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    id INTEGER PRIMARY KEY DEFAULT nextval('seq_packages'),
                    name VARCHAR NOT NULL UNIQUE,
                    speed INTEGER NOT NULL CHECK (speed > 0),
                    price INTEGER NOT NULL CHECK (price > 0),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_packages_name ON packages(name)")

            # Create customers table with optimized data types
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY DEFAULT nextval('seq_customers'),
                    name VARCHAR NOT NULL,
                    package_id INTEGER,
                    monthly_fee INTEGER NOT NULL CHECK (monthly_fee > 0),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package_id) REFERENCES packages(id)
                )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)")

            # Create payments table with optimized data types
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY DEFAULT nextval('seq_payments'),
                    customer_id INTEGER NOT NULL,
                    payment_date DATE NOT NULL,
                    billing_month TINYINT NOT NULL CHECK (billing_month >= 1 AND billing_month <= 12),
                    billing_year SMALLINT NOT NULL CHECK (billing_year >= 2020 AND billing_year <= 2100),
                    amount INTEGER NOT NULL CHECK (amount > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, billing_month, billing_year)
                )
            """)

            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_payments_customer_year 
                ON payments(customer_id, billing_year, billing_month)
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_customer ON payments(customer_id)")

            # Create users table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY DEFAULT nextval('seq_users'),
                    username VARCHAR NOT NULL UNIQUE,
                    password_hash VARCHAR NOT NULL,
                    role VARCHAR NOT NULL CHECK (role IN ('admin', 'user')),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

            self.conn.commit()
            logger.info("Database schema initialized successfully")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        try:
            yield self.conn
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise e

    @contextmanager
    def transaction(self):
        """Context manager for transaction handling with auto-commit/rollback."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise

    def execute(self, query: str, params: list = None, fetch: str = None):
        """Execute query with optional parameter binding."""
        try:
            result = self.conn.execute(query, params or [])

            if fetch == 'all':
                return result.fetchall()
            elif fetch == 'one':
                return result.fetchone()
            else:
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_prepared(self, query: str, params: list):
        """Execute prepared statement with parameters."""
        try:
            return self.conn.execute(query, params)
        except Exception as e:
            logger.error(f"Prepared statement failed: {e}")
            raise

    def vacuum(self):
        """Optimize database file (remove unused space)."""
        try:
            self.conn.execute("PRAGMA database_list")
            self.conn.execute("CHECKPOINT")
            logger.info("Database checkpoint completed")
        except Exception as e:
            logger.warning(f"Checkpoint failed: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database instance
_db_instance = None


def get_db() -> Database:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def close_db():
    """Close global database instance."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
