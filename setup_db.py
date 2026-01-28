#!/usr/bin/env python3
"""
Setup script for Tagihan WiFi API.
Creates initial admin user and sample data.
"""

import getpass
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


def add_sample_customer(db: Database, name: str, monthly_fee: int):
    """Add a sample customer."""
    try:
        from app.utils.sqids_helper import get_sqids_helper

        sqids_helper = get_sqids_helper()

        result = db.conn.execute(
            """
            INSERT INTO customers (name, monthly_fee, sqid)
            VALUES (?, ?, ?)
            RETURNING id, sqid, name, monthly_fee
            """,
            [name, monthly_fee, "temp"],
        ).fetchall()

        if result:
            customer = result[0]
            customer_id = customer[0]

            # Generate sqid
            sqid_value = sqids_helper.encode_single(customer_id)

            # Update with actual sqid
            db.conn.execute(
                "UPDATE customers SET sqid = ? WHERE id = ?",
                [sqid_value, customer_id],
            )
            db.conn.commit()

            print(f"✓ Customer created: {customer[2]} (sqid: {sqid_value}, fee: Rp{monthly_fee:,})")
            return True
    except Exception as e:
        print(f"✗ Error creating customer: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Tagihan WiFi API - Setup")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    db = Database()
    print("✓ Database initialized")

    # Create admin user
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

    # Add sample customers
    print("\n--- Add Sample Customers (Optional) ---")
    add_samples = input("Add sample customers? (y/n): ").strip().lower() == "y"

    if add_samples:
        sample_customers = [
            ("Opi", 150000),
            ("Budi", 200000),
            ("Siti", 175000),
        ]

        for name, fee in sample_customers:
            add_sample_customer(db, name, fee)

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
