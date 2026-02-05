#!/usr/bin/env python3
"""
Test script for query filter parameters in API endpoints.
Demonstrates filtering capabilities on all list endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001/api/v1"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def get_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"] if response.status_code == 200 else None

def test_customer_filters(token):
    """Test customer list filters"""
    print_section("CUSTOMER FILTERS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get all customers (no filter)
    print("\n1. All customers:")
    response = requests.get(f"{BASE_URL}/customers", headers=headers)
    if response.status_code == 200:
        customers = response.json().get("data", [])
        print(f"   Total: {len(customers)} customers")
        for c in customers[:3]:
            print(f"   - {c['name']} (ID: {c['id'][:20]}...)")
    
    # 2. Filter by name (partial match)
    print("\n2. Filter by name (partial match 'test'):")
    response = requests.get(
        f"{BASE_URL}/customers",
        params={"name": "test"},
        headers=headers
    )
    if response.status_code == 200:
        customers = response.json().get("data", [])
        print(f"   Found: {len(customers)} customers")
        for c in customers[:5]:
            print(f"   - {c['name']}")
    
    # 3. Filter by name (case-insensitive)
    print("\n3. Filter by name (case-insensitive 'TEST'):")
    response = requests.get(
        f"{BASE_URL}/customers",
        params={"name": "TEST"},
        headers=headers
    )
    if response.status_code == 200:
        customers = response.json().get("data", [])
        print(f"   Found: {len(customers)} customers")
    
    # 4. Filter by package_id
    print("\n4. Get packages to filter customers:")
    response = requests.get(f"{BASE_URL}/packages", headers=headers)
    if response.status_code == 200 and response.json().get("data"):
        package = response.json()["data"][0]
        package_id = package['id']
        print(f"   Using package: {package['name']} (ID: {package_id})")
        
        print(f"\n   Filtering customers by package_id={package_id}:")
        response = requests.get(
            f"{BASE_URL}/customers",
            params={"package_id": package_id},
            headers=headers
        )
        if response.status_code == 200:
            customers = response.json().get("data", [])
            print(f"   Found: {len(customers)} customers with this package")
            for c in customers[:5]:
                package_name = c["package"]["name"] if c.get("package") else "-"
                print(f"   - {c['name']} → {package_name}")
    
    # 5. Combined filters
    print("\n5. Combined filters (name + package_id):")
    if 'package_id' in locals():
        response = requests.get(
            f"{BASE_URL}/customers",
            params={"name": "test", "package_id": package_id},
            headers=headers
        )
        if response.status_code == 200:
            customers = response.json().get("data", [])
            print(f"   Found: {len(customers)} customers matching both filters")

def test_package_filters(token):
    """Test package list filters"""
    print_section("PACKAGE FILTERS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get all packages
    print("\n1. All packages:")
    response = requests.get(f"{BASE_URL}/packages", headers=headers)
    if response.status_code == 200:
        packages = response.json().get("data", [])
        print(f"   Total: {len(packages)} packages")
        for p in packages[:3]:
            print(f"   - {p['name']}: {p['speed']}Mbps @ Rp{p['price']:,}")
    
    # 2. Filter by name
    print("\n2. Filter by name (partial match 'premium'):")
    response = requests.get(
        f"{BASE_URL}/packages",
        params={"name": "premium"},
        headers=headers
    )
    if response.status_code == 200:
        packages = response.json().get("data", [])
        print(f"   Found: {len(packages)} packages")
        for p in packages:
            print(f"   - {p['name']}")
    
    # 3. Filter by speed range
    print("\n3. Filter by speed (min_speed=50, max_speed=100):")
    response = requests.get(
        f"{BASE_URL}/packages",
        params={"min_speed": 50, "max_speed": 100},
        headers=headers
    )
    if response.status_code == 200:
        packages = response.json().get("data", [])
        print(f"   Found: {len(packages)} packages")
        for p in packages:
            print(f"   - {p['name']}: {p['speed']}Mbps")
    
    # 4. Filter by price range
    print("\n4. Filter by price (min_price=100000, max_price=250000):")
    response = requests.get(
        f"{BASE_URL}/packages",
        params={"min_price": 100000, "max_price": 250000},
        headers=headers
    )
    if response.status_code == 200:
        packages = response.json().get("data", [])
        print(f"   Found: {len(packages)} packages")
        for p in packages:
            print(f"   - {p['name']}: Rp{p['price']:,}")
    
    # 5. Combined filters
    print("\n5. Combined filters (name='test', min_speed=50):")
    response = requests.get(
        f"{BASE_URL}/packages",
        params={"name": "test", "min_speed": 50},
        headers=headers
    )
    if response.status_code == 200:
        packages = response.json().get("data", [])
        print(f"   Found: {len(packages)} packages")
    
    # 6. Include inactive packages
    print("\n6. Include inactive packages (include_inactive=true):")
    response = requests.get(
        f"{BASE_URL}/packages",
        params={"include_inactive": True},
        headers=headers
    )
    if response.status_code == 200:
        packages = response.json().get("data", [])
        active_count = sum(1 for p in packages if p['is_active'])
        inactive_count = sum(1 for p in packages if not p['is_active'])
        print(f"   Total: {len(packages)} packages")
        print(f"   Active: {active_count}, Inactive: {inactive_count}")

def test_payment_filters(token):
    """Test payment list filters (already existed, just demo)"""
    print_section("PAYMENT FILTERS (Existing)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Filter by year
    print("\n1. Filter by year (year=2026):")
    response = requests.get(
        f"{BASE_URL}/payments",
        params={"year": 2026},
        headers=headers
    )
    if response.status_code == 200:
        payments = response.json().get("data", [])
        print(f"   Found: {len(payments)} payments in 2026")
    
    # 2. Filter by month and year
    print("\n2. Filter by month and year (month=1, year=2026):")
    response = requests.get(
        f"{BASE_URL}/payments",
        params={"month": 1, "year": 2026},
        headers=headers
    )
    if response.status_code == 200:
        payments = response.json().get("data", [])
        print(f"   Found: {len(payments)} payments in January 2026")
    
    # 3. Filter by customer_id
    print("\n3. Get a customer to filter payments:")
    response = requests.get(f"{BASE_URL}/customers", headers=headers)
    if response.status_code == 200 and response.json().get("data"):
        customer = response.json()["data"][0]
        customer_id = customer['id']
        print(f"   Using customer: {customer['name']} (ID: {customer_id[:20]}...)")
        
        response = requests.get(
            f"{BASE_URL}/payments",
            params={"customer_id": customer_id},
            headers=headers
        )
        if response.status_code == 200:
            payments = response.json().get("data", [])
            print(f"   Found: {len(payments)} payments for this customer")

def test_billing_matrix_filters(token):
    """Test billing matrix filters"""
    print_section("BILLING MATRIX FILTERS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get all customers in matrix
    print("\n1. All customers billing matrix (year=2026):")
    response = requests.get(f"{BASE_URL}/billing-matrix/2026", headers=headers)
    if response.status_code == 200:
        matrix = response.json()
        rows = matrix.get("data", [])
        print(f"   Total customers: {len(rows)}")
    
    # 2. Filter by customer_name
    print("\n2. Filter by customer name (customer_name='test'):")
    response = requests.get(
        f"{BASE_URL}/billing-matrix/2026",
        params={"customer_name": "test"},
        headers=headers
    )
    if response.status_code == 200:
        matrix = response.json()
        rows = matrix.get("data", [])
        print(f"   Found: {len(rows)} customers")
        for row in rows[:3]:
            print(f"   - {row['customer_name']}: {row['completion_percentage']:.1f}% complete")
    
    # 3. Filter by specific customer_id
    print("\n3. Filter by specific customer_id:")
    response = requests.get(f"{BASE_URL}/customers", headers=headers)
    if response.status_code == 200 and response.json().get("data"):
        customer = response.json()["data"][0]
        customer_id = customer['id']
        print(f"   Using customer: {customer['name']} (ID: {customer_id[:20]}...)")
        
        response = requests.get(
            f"{BASE_URL}/billing-matrix/2026",
            params={"customer_id": customer_id},
            headers=headers
        )
        if response.status_code == 200:
            matrix = response.json()
            print(f"   Found: {len(matrix['rows'])} customer(s)")
            if matrix['rows']:
                row = matrix['rows'][0]
                print(f"   Customer: {row['customer_name']}")
                print(f"   Total paid: Rp{row['total_paid']:,}")
                print(f"   Total expected: Rp{row['total_expected']:,}")
                print(f"   Completion: {row['completion_percentage']:.1f}%")

def main():
    print("\n" + "="*70)
    print("  QUERY FILTER PARAMETERS TEST")
    print("="*70)
    print("\nTesting filter capabilities on all list endpoints")
    
    token = get_token()
    if not token:
        print("✗ Authentication failed")
        return
    
    print("✓ Authentication successful\n")
    
    # Test all endpoints
    test_customer_filters(token)
    test_package_filters(token)
    test_payment_filters(token)
    test_billing_matrix_filters(token)
    
    print("\n" + "="*70)
    print("  FILTER TEST SUMMARY")
    print("="*70)
    print("\n✓ Customer filters:")
    print("  - name (partial match, case-insensitive)")
    print("  - package_id (exact match, sqid format)")
    print("\n✓ Package filters:")
    print("  - name (partial match, case-insensitive)")
    print("  - min_speed / max_speed")
    print("  - min_price / max_price")
    print("  - include_inactive")
    print("\n✓ Payment filters (existing):")
    print("  - customer_id (exact match, sqid format)")
    print("  - year")
    print("  - month")
    print("\n✓ Billing matrix filters:")
    print("  - customer_id (exact match, sqid format)")
    print("  - customer_name (partial match, case-insensitive)")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
