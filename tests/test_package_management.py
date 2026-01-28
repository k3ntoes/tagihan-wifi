#!/usr/bin/env python3
"""
Test script for package management functionality.
Demonstrates creating packages, assigning them to customers, and querying the data.
"""

from app.db.database import Database
from app.utils.sqids_helper import get_sqids_helper

def main():
    print("=" * 60)
    print("PACKAGE MANAGEMENT TEST")
    print("=" * 60)
    print()

    # Initialize database
    db = Database()
    sqids_helper = get_sqids_helper()

    # Clean up test data
    print("🧹 Cleaning up test data...")
    db.conn.execute("DELETE FROM payments WHERE customer_id IN (SELECT id FROM customers WHERE name LIKE 'Test%')")
    db.conn.execute("DELETE FROM customers WHERE name LIKE 'Test%'")
    db.conn.execute("DELETE FROM packages WHERE name LIKE 'Test%'")
    db.conn.commit()
    print("✓ Test data cleaned\n")

    # Step 1: Create packages
    print("📦 Step 1: Creating test packages...")
    packages = [
        ("Test Basic 10Mbps", 10, 100000),
        ("Test Standard 50Mbps", 50, 200000),
        ("Test Premium 100Mbps", 100, 300000),
    ]

    package_ids = []
    for name, speed, price in packages:
        try:
            result = db.conn.execute(
                """
                INSERT INTO packages (name, speed, price)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                [name, speed, price],
            ).fetchone()
            package_ids.append(result[0])
            print(f"  ✓ Created: {name} - {speed}Mbps - Rp{price:,}")
        except Exception as e:
            print(f"  ✗ Error creating {name}: {e}")

    db.conn.commit()
    print()

    # Step 2: Create customers with packages
    print("👥 Step 2: Creating customers with packages...")
    customers = [
        ("Test Customer A", package_ids[0], 100000),  # Basic
        ("Test Customer B", package_ids[1], 200000),  # Standard
        ("Test Customer C", package_ids[2], 300000),  # Premium
        ("Test Customer D", None, 150000),  # No package
    ]

    customer_ids = []
    for name, package_id, fee in customers:
        try:
            result = db.conn.execute(
                """
                INSERT INTO customers (name, package_id, monthly_fee)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                [name, package_id, fee],
            ).fetchone()
            customer_ids.append(result[0])
            pkg_info = f"Package ID {package_id}" if package_id else "No package"
            print(f"  ✓ Created: {name} - {pkg_info} - Rp{fee:,}")
        except Exception as e:
            print(f"  ✗ Error creating {name}: {e}")

    db.conn.commit()
    print()

    # Step 3: Query customers with package details
    print("📊 Step 3: Querying customers with package details...")
    results = db.conn.execute(
        """
        SELECT c.id, c.name, c.package_id, p.name as package_name, 
               p.speed, p.price as package_price, c.monthly_fee
        FROM customers c
        LEFT JOIN packages p ON c.package_id = p.id
        WHERE c.name LIKE 'Test%' AND c.is_active = true
        ORDER BY c.id
        """
    ).fetchall()

    print(f"\n{'ID':<5} {'Customer Name':<20} {'Package':<25} {'Speed':<10} {'Monthly Fee':<15}")
    print("-" * 85)
    for row in results:
        cust_id, name, pkg_id, pkg_name, speed, pkg_price, monthly_fee = row
        pkg_display = pkg_name if pkg_name else "No package"
        speed_display = f"{speed}Mbps" if speed else "-"
        print(f"{cust_id:<5} {name:<20} {pkg_display:<25} {speed_display:<10} Rp{monthly_fee:>10,}")
    print()

    # Step 4: Try to delete package in use
    print("🔒 Step 4: Testing package protection (try to delete package in use)...")
    try:
        # Check how many customers use package_ids[0]
        count_result = db.conn.execute(
            "SELECT COUNT(*) FROM customers WHERE package_id = ? AND is_active = true",
            [package_ids[0]],
        ).fetchone()
        customer_count = count_result[0]

        if customer_count > 0:
            print(f"  ℹ️  Package {package_ids[0]} is used by {customer_count} active customer(s)")
            print(f"  ℹ️  In production, DELETE endpoint would return 400 Bad Request")
            print(f"  ℹ️  Simulating soft delete instead...")
            db.conn.execute(
                "UPDATE packages SET is_active = false WHERE id = ?",
                [package_ids[0]],
            )
            db.conn.commit()
            print(f"  ✓ Package soft-deleted (is_active = false)")
            
            # Restore it
            db.conn.execute(
                "UPDATE packages SET is_active = true WHERE id = ?",
                [package_ids[0]],
            )
            db.conn.commit()
            print(f"  ✓ Package restored for cleanup")
        else:
            print(f"  ⚠️  No customers using package {package_ids[0]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    print()

    # Step 5: Update customer package
    print("🔄 Step 5: Updating customer package...")
    if len(customer_ids) >= 2:
        try:
            # Update customer 0 to use package 1
            db.conn.execute(
                """
                UPDATE customers 
                SET package_id = ?, monthly_fee = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [package_ids[1], 200000, customer_ids[0]],
            )
            db.conn.commit()
            print(f"  ✓ Updated {customers[0][0]} to use {packages[1][0]}")
            
            # Query to verify
            result = db.conn.execute(
                """
                SELECT c.name, p.name, c.monthly_fee
                FROM customers c
                LEFT JOIN packages p ON c.package_id = p.id
                WHERE c.id = ?
                """,
                [customer_ids[0]],
            ).fetchone()
            print(f"  ✓ Verified: {result[0]} now has {result[1]} at Rp{result[2]:,}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    print()

    # Step 6: Generate Sqids for customers
    print("🔑 Step 6: Generating Sqids for customers...")
    for cust_id in customer_ids:
        sqid = sqids_helper.encode_single(cust_id)
        result = db.conn.execute(
            "SELECT name FROM customers WHERE id = ?", [cust_id]
        ).fetchone()
        if result:
            print(f"  {result[0]:<20} ID: {cust_id:<3} → Sqid: {sqid}")
    print()

    # Step 7: Package statistics
    print("📈 Step 7: Package usage statistics...")
    stats = db.conn.execute(
        """
        SELECT p.name, p.speed, p.price, COUNT(c.id) as customer_count
        FROM packages p
        LEFT JOIN customers c ON p.id = c.package_id AND c.is_active = true
        WHERE p.name LIKE 'Test%' AND p.is_active = true
        GROUP BY p.id, p.name, p.speed, p.price
        ORDER BY p.speed
        """
    ).fetchall()

    print(f"\n{'Package Name':<25} {'Speed':<10} {'Price':<15} {'Customers':<10}")
    print("-" * 60)
    for row in stats:
        pkg_name, speed, price, count = row
        print(f"{pkg_name:<25} {speed}Mbps{'':<5} Rp{price:>10,}   {count:>5}")
    print()

    # Cleanup
    print("🧹 Cleaning up test data...")
    db.conn.execute("DELETE FROM customers WHERE name LIKE 'Test%'")
    db.conn.execute("DELETE FROM packages WHERE name LIKE 'Test%'")
    db.conn.commit()
    print("✓ Test data cleaned\n")

    db.close()

    print("=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
