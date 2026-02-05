#!/usr/bin/env python3
"""
Setup script for Tagihan WiFi API.
Creates initial admin user and sample data.
"""

import getpass
import os
import sys
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


def add_sample_customer(db: Database, name: str, monthly_fee: int, package_id: int | None = None):
    """Add a sample customer."""
    try:
        result = db.conn.execute(
            """
            INSERT INTO customers (name, package_id, monthly_fee)
            VALUES (?, ?, ?)
            RETURNING id, name, package_id, monthly_fee
            """,
            [name, package_id, monthly_fee],
        ).fetchall()

        if result:
            customer = result[0]
            db.conn.commit()
            print(f"✓ Customer created: {customer[1]} (fee: Rp{monthly_fee:,}, package_id: {customer[2]})")
            return True
    except Exception as e:
        print(f"✗ Error creating customer: {e}")
        return False


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


def update_sample_customer(db: Database, name: str, package_id: int | None, monthly_fee: int):
    """Update a sample customer with package assignment and monthly fee."""
    try:
        result = db.conn.execute(
            """
            UPDATE customers
            SET package_id = ?, monthly_fee = ?, updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
            RETURNING id, name, package_id, monthly_fee
            """,
            [package_id, monthly_fee, name],
        ).fetchone()

        if result:
            db.conn.commit()
            print(f"✓ Customer updated: {result[1]} (fee: Rp{result[3]:,}, package_id: {result[2]})")
            return True
        print(f"✗ Customer not found for update: {name}")
        return False
    except Exception as e:
        print(f"✗ Error updating customer: {e}")
        return False


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


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
        if skip_admin:
            print("Skipping admin creation (SETUP_DB_SKIP_ADMIN=1)")
        else:
            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD")

            if not password:
                print("ADMIN_PASSWORD not set. Skipping admin creation.")
            else:
                user = db.conn.execute(
                    "SELECT COUNT(*) FROM users WHERE username = ?",
                    [username],
                ).fetchall()

                if user[0][0] > 0:
                    print(f"User '{username}' already exists. Skipping...")
                else:
                    if len(password) < 6:
                        print("ADMIN_PASSWORD must be at least 6 characters. Skipping...")
                    else:
                        create_admin_user(db, username, password)

        if add_samples:
            sample_packages = [
                ("Paket 20 Mbps", 20, 150000),
                ("Paket 50 Mbps", 50, 200000),
                ("Paket 100 Mbps", 100, 275000),
            ]
            package_ids = [add_sample_package(db, name, speed, price) for name, speed, price in sample_packages]

            sample_customers = [
                ("Opi", 150000, package_ids[0]),
                ("Budi", 200000, package_ids[1]),
                ("Siti", 175000, package_ids[2]),
            ]

            for name, fee, pkg_id in sample_customers:
                add_sample_customer(db, name, fee, pkg_id)
                update_sample_customer(db, name, pkg_id, fee)
        else:
            print("Skipping sample customers.")

        print("\nSetup Complete (non-interactive).")
        db.close()
        return

    # Create admin user (interactive)
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

    # Add sample customers (interactive)
    print("\n--- Add Sample Customers (Optional) ---")
    add_samples = input("Add sample customers? (y/n): ").strip().lower() == "y"

    if add_samples:
        sample_packages = [
            ("Paket 20 Mbps", 20, 150000),
            ("Paket 50 Mbps", 50, 200000),
            ("Paket 100 Mbps", 100, 275000),
        ]
        package_ids = [add_sample_package(db, name, speed, price) for name, speed, price in sample_packages]

        sample_customers = [
            ("Opi", 150000, package_ids[0]),
            ("Budi", 200000, package_ids[1]),
            ("Siti", 175000, package_ids[2]),
        ]

        for name, fee, pkg_id in sample_customers:
            add_sample_customer(db, name, fee, pkg_id)
            update_sample_customer(db, name, pkg_id, fee)

    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update SECRET_KEY in .env for production")
    print("2. Run: uvicorn main:app --reload")
    print("3. Visit: http://localhost:8000/docs")
    print("4. Login with your admin credentials")

    db.close()


if __name__ == "__main__":
    main()
