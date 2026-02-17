#!/usr/bin/env python3
"""
Setup script for Tagihan WiFi API.
Creates initial admin user and sample data.
"""

import getpass
import os
import sys
from datetime import date
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.auth import PasswordManager
from app.db.database import Database


def create_admin_user(db: Database, username: str, password: str):
    """Create initial admin user."""
    try:
        password_hash = PasswordManager.hash_password(password)
        result = db.conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            RETURNING id, username, role
            """,
            [username, password_hash, "admin"],
        ).fetchall()

        if result:
            user = result[0]
            db.conn.commit()
            print(f"✓ Admin user created: {user[1]} (ID: {user[0]})")
            return True
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"✗ User '{username}' already exists")
            return False
        print(f"✗ Error creating user: {e}")
        return False


def add_sample_customer(db: Database, name: str, monthly_fee: int, package_id: int | None = None, package_start_date: date | None = None):
    """Add a sample customer. Also creates a user account automatically."""
    try:
        result = db.conn.execute(
            """
            INSERT INTO customers (name, package_id, monthly_fee, package_start_date)
            VALUES (?, ?, ?, ?)
            RETURNING id, name, package_id, monthly_fee, package_start_date
            """,
            [name, package_id, monthly_fee, package_start_date.isoformat() if package_start_date else None],
        ).fetchall()

        if result:
            customer = result[0]
            db.conn.commit()
            date_str = f", start: {customer[4]}" if customer[4] else ""
            print(f"✓ Customer created: {customer[1]} (fee: Rp{monthly_fee:,}, package_id: {customer[2]}{date_str})")
            
            # Show auto-created user info
            username = name.strip().lower().replace(" ", "_")
            print(f"  ├─ User account created: username='{username}', password='liank' (role: user)")
            
            return customer[0]  # Return customer ID
    except Exception as e:
        print(f"✗ Error creating customer: {e}")
        return None


def add_sample_package(db: Database, name: str, speed: int, price: int) -> int | None:
    """Add a sample package. Returns package ID if created or found."""
    try:
        existing = db.conn.execute(
            "SELECT id FROM packages WHERE name = ?",
            [name],
        ).fetchone()

        if existing:
            return existing[0]

        result = db.conn.execute(
            """
            INSERT INTO packages (name, speed, price)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            [name, speed, price],
        ).fetchone()

        if result:
            db.conn.commit()
            print(f"✓ Package created: {name} ({speed} Mbps, Rp{price:,})")
            return result[0]
    except Exception as e:
        print(f"✗ Error creating package: {e}")
        return None


def update_sample_customer(db: Database, name: str, package_id: int | None, monthly_fee: int, package_start_date: date | None = None):
    """Update a sample customer with package assignment, monthly fee and package start date."""
    try:
        result = db.conn.execute(
            """
            UPDATE customers
            SET package_id = ?, monthly_fee = ?, package_start_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
            RETURNING id, name, package_id, monthly_fee, package_start_date
            """,
            [package_id, monthly_fee, package_start_date.isoformat() if package_start_date else None, name],
        ).fetchone()

        if result:
            db.conn.commit()
            date_str = f", start: {result[4]}" if result[4] else ""
            print(f"✓ Customer updated: {result[1]} (fee: Rp{result[3]:,}, package_id: {result[2]}{date_str})")
            return True
        print(f"✗ Customer not found for update: {name}")
        return False
    except Exception as e:
        print(f"✗ Error updating customer: {e}")
        return False


def add_sample_payment(db: Database, customer_id: int, payment_date: date, billing_month: int, billing_year: int, amount: int):
    """Add a sample payment."""
    try:
        result = db.conn.execute(
            """
            INSERT INTO payments (customer_id, payment_date, billing_month, billing_year, amount)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, customer_id, payment_date, billing_month, billing_year, amount
            """,
            [customer_id, payment_date.isoformat(), billing_month, billing_year, amount],
        ).fetchone()

        if result:
            db.conn.commit()
            return True
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            # Payment already exists, ignore silently
            return True
        print(f"✗ Error creating payment: {e}")
        return False


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def setup_sample_data(db: Database):
    """
    Setup sample packages, customers and payments.
    All customers are created as active (is_active=true) by default.
    Use POST /customers/{customer_id}/disable to test disable functionality.
    """
    sample_packages = [
        ("Paket 20 Mbps", 20, 150000),
        ("Paket 50 Mbps", 50, 200000),
        ("Paket 100 Mbps", 100, 275000),
    ]
    package_ids = [add_sample_package(db, name, speed, price) for name, speed, price in sample_packages]

    # Create customers with start dates
    sample_customers = [
        ("Opi", 150000, package_ids[0], date(2024, 1, 1)),
        ("Budi", 200000, package_ids[1], date(2024, 3, 15)),
        ("Siti", 175000, package_ids[2], date(2024, 2, 1)),
    ]

    customer_ids = []
    for name, fee, pkg_id, start_date in sample_customers:
        cust_id = add_sample_customer(db, name, fee, pkg_id, start_date)
        if cust_id:
            customer_ids.append((cust_id, name, fee, start_date))
            update_sample_customer(db, name, pkg_id, fee, start_date)

    # Add dummy payments for 2024
    print("\nAdding dummy payments for 2024...")
    for customer_id, name, monthly_fee, start_date in customer_ids:
        start_month = start_date.month
        
        # Add payments from start date to end of 2024
        for month in range(start_month, 13):
            payment_day = min(15, 28)  # Payment on 15th, or 28th for shorter months
            payment_date = date(2024, month, payment_day)
            
            # Random variation: sometimes payment is on 10th, sometimes on 20th
            if month % 3 == 0:
                payment_date = date(2024, month, min(10, 28))
            
            add_sample_payment(db, customer_id, payment_date, month, 2024, monthly_fee)
            print(f"  ✓ Payment added: {name} - {payment_date.strftime('%Y-%m-%d')} (Rp{monthly_fee:,})")


def setup_admin_non_interactive(db: Database, skip_admin: bool) -> bool:
    """Setup admin user in non-interactive mode. Returns True if successful."""
    if skip_admin:
        print("Skipping admin creation (SETUP_DB_SKIP_ADMIN=1)")
        return True

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        print("ADMIN_PASSWORD not set. Skipping admin creation.")
        return False

    user = db.conn.execute(
        "SELECT COUNT(*) FROM users WHERE username = ?",
        [username],
    ).fetchall()

    if user[0][0] > 0:
        print(f"User '{username}' already exists. Skipping...")
        return True

    if len(password) < 6:
        print("ADMIN_PASSWORD must be at least 6 characters. Skipping...")
        return False

    return create_admin_user(db, username, password)


def setup_admin_interactive(db: Database):
    """Setup admin user in interactive mode."""
    print("\n--- Create Admin User ---")
    username = input("Enter admin username (default: admin): ").strip() or "admin"

    # Check if user exists
    user = db.conn.execute(
        "SELECT COUNT(*) FROM users WHERE username = ?",
        [username],
    ).fetchall()

    if user[0][0] > 0:
        print(f"User '{username}' already exists. Skipping...")
    else:
        while True:
            password = getpass.getpass("Enter admin password: ")
            password_confirm = getpass.getpass("Confirm password: ")

            if password != password_confirm:
                print("✗ Passwords don't match. Try again.")
                continue

            if len(password) < 6:
                print("✗ Password must be at least 6 characters.")
                continue

            create_admin_user(db, username, password)
            break


def main():
    """Main setup function."""
    print("=" * 60)
    print("Tagihan WiFi API - Setup")
    print("=" * 60)

    non_interactive = _is_truthy(os.getenv("SETUP_DB_NON_INTERACTIVE"))
    skip_admin = _is_truthy(os.getenv("SETUP_DB_SKIP_ADMIN"))
    add_samples_env = os.getenv("SETUP_DB_ADD_SAMPLES")
    add_samples = _is_truthy(add_samples_env) if add_samples_env is not None else None

    # Initialize database
    print("\nInitializing database...")
    db = Database()
    print("✓ Database initialized")

    if non_interactive:
        print("\n--- Non-Interactive Setup ---")
        setup_admin_non_interactive(db, skip_admin)

        if add_samples:
            setup_sample_data(db)
        else:
            print("Skipping sample customers.")

        print("\nSetup Complete (non-interactive).")
        db.close()
        return

    # Interactive mode
    setup_admin_interactive(db)

    # Add sample customers (interactive)
    print("\n--- Add Sample Customers (Optional) ---")
    add_samples = input("Add sample customers? (y/n): ").strip().lower() == "y"

    if add_samples:
        setup_sample_data(db)

    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update SECRET_KEY in .env for production")
    print("2. Run: uvicorn main:app --reload")
    print("3. Visit: http://localhost:8000/docs")
    print("4. Login with your admin credentials")
    print("\nCustomer Management:")
    print("- All sample customers are created as ACTIVE")
    print("- User accounts auto-created for each customer")
    print("  ├─ Username: customer name (lowercase, spaces→underscores)")
    print("  └─ Default password: 'liank' (role: user)")
    print("- To test disable/enable: POST /customers/{customer_id}/disable")
    print("- To re-enable: POST /customers/{customer_id}/enable")
    print("- Disabled customers won't appear in billing matrix")

    db.close()


if __name__ == "__main__":
    main()
