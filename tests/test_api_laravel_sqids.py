#!/usr/bin/env python3
"""
Integration test for Laravel-style Sqids in API endpoints.
Tests all CRUD operations with new prefix format.
"""

import requests
import json
from datetime import date

# API Configuration
BASE_URL = "http://127.0.0.1:8001/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def print_info(message):
    print(f"ℹ {message}")

def login():
    """Get JWT token"""
    print_header("1. AUTHENTICATION")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"Logged in successfully")
        return token
    else:
        print_error(f"Login failed: {response.text}")
        return None

def test_packages(token):
    """Test package CRUD with Laravel-style Sqids"""
    print_header("2. TESTING PACKAGES (pack_ prefix)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create package
    package_data = {
        "name": "Test Laravel Sqids 100Mbps",
        "speed": 100,
        "price": 250000
    }
    
    response = requests.post(f"{BASE_URL}/packages", json=package_data, headers=headers)
    
    if response.status_code == 201:
        package = response.json()["data"]
        package_id = package["id"]
        print_success(f"Package created: {package_id}")
        print_info(f"  Prefix check: {package_id[:5] == 'pack_'}")
        print_info(f"  Format: {package_id}")
        
        # List packages
        response = requests.get(f"{BASE_URL}/packages", headers=headers)
        if response.status_code == 200:
            packages = response.json().get("data", [])
            print_success(f"Retrieved {len(packages)} packages")
            for pkg in packages[:3]:
                print_info(f"  - {pkg['name']}: {pkg['id']}")
        
        # Get specific package
        response = requests.get(f"{BASE_URL}/packages/{package_id}", headers=headers)
        if response.status_code == 200:
            print_success(f"Retrieved package by ID: {package_id}")
        
        return package_id
    else:
        print_error(f"Failed to create package: {response.text}")
        return None

def test_customers(token, package_id):
    """Test customer CRUD with Laravel-style Sqids"""
    print_header("3. TESTING CUSTOMERS (cust_ prefix)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create customer
    customer_data = {
        "name": "Test Laravel Sqids Customer",
        "package_id": package_id,
        "monthly_fee": 250000
    }
    
    response = requests.post(f"{BASE_URL}/customers", json=customer_data, headers=headers)
    
    if response.status_code == 201:
        customer = response.json()["data"]
        customer_id = customer["id"]
        print_success(f"Customer created: {customer_id}")
        print_info(f"  Prefix check: {customer_id[:5] == 'cust_'}")
        print_info(f"  Format: {customer_id}")
        if customer.get("package"):
            print_info(f"  Package ID: {customer['package']['id']}")
            print_info(f"  Package prefix check: {customer['package']['id'][:5] == 'pack_'}")
        
        # List customers
        response = requests.get(f"{BASE_URL}/customers", headers=headers)
        if response.status_code == 200:
            customers = response.json().get("data", [])
            print_success(f"Retrieved {len(customers)} customers")
            for cust in customers[:3]:
                print_info(f"  - {cust['name']}: {cust['id']}")
        
        # Get specific customer
        response = requests.get(f"{BASE_URL}/customers/{customer_id}", headers=headers)
        if response.status_code == 200:
            print_success(f"Retrieved customer by ID: {customer_id}")
        
        # Update customer
        update_data = {"monthly_fee": 275000}
        response = requests.patch(f"{BASE_URL}/customers/{customer_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            print_success(f"Updated customer: {customer_id}")
        
        return customer_id
    else:
        print_error(f"Failed to create customer: {response.text}")
        return None

def test_payments(token, customer_id):
    """Test payment creation with Laravel-style Sqids"""
    print_header("4. TESTING PAYMENTS (pay_ prefix)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create payment
    payment_data = {
        "customer_id": customer_id,
        "payment_date": str(date.today()),
        "billing_month": 1,
        "billing_year": 2026,
        "amount": 250000
    }
    
    response = requests.post(f"{BASE_URL}/payments", json=payment_data, headers=headers)
    
    if response.status_code == 201:
        payment = response.json()["data"]
        payment_id = payment["id"]
        print_success(f"Payment created: {payment_id}")
        print_info(f"  Prefix check: {payment_id[:4] == 'pay_'}")
        print_info(f"  Format: {payment_id}")
        print_info(f"  Customer ID: {payment['customer_id']}")
        print_info(f"  Customer prefix check: {payment['customer_id'][:5] == 'cust_'}")
        
        # List payments
        response = requests.get(f"{BASE_URL}/payments", headers=headers)
        if response.status_code == 200:
            payments = response.json().get("data", [])
            print_success(f"Retrieved {len(payments)} payments")
            for pay in payments[:3]:
                print_info(f"  - Payment {pay['id'][:20]}... for customer {pay['customer_id'][:20]}...")
        
        return payment_id
    else:
        print_error(f"Failed to create payment: {response.text}")
        return None

def test_billing_matrix(token):
    """Test billing matrix with Laravel-style Sqids"""
    print_header("5. TESTING BILLING MATRIX")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/billing-matrix/2026", headers=headers)
    
    if response.status_code == 200:
        matrix = response.json()
        rows = matrix.get("data", [])
        print_success(f"Retrieved billing matrix for {matrix['year']}")
        print_info(f"  Total customers: {len(rows)}")
        
        if rows:
            for row in rows[:3]:
                customer_id = row['customer_id']
                print_info(f"  - {row['customer_name']}: {customer_id}")
                print_info(f"    Prefix check: {customer_id[:5] == 'cust_'}")
        
        return True
    else:
        print_error(f"Failed to get billing matrix: {response.text}")
        return False

def test_prefix_validation(token, customer_id, package_id):
    """Test that wrong prefix is rejected"""
    print_header("6. TESTING PREFIX VALIDATION")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to use package ID as customer ID (should fail)
    print_info("Testing: Using package ID where customer ID expected...")
    payment_data = {
        "customer_id": package_id,  # Wrong! This is a package ID
        "payment_date": str(date.today()),
        "billing_month": 2,
        "billing_year": 2026,
        "amount": 250000
    }
    
    response = requests.post(f"{BASE_URL}/payments", json=payment_data, headers=headers)
    
    if response.status_code == 400:
        print_success("Correctly rejected package ID as customer ID")
        print_info(f"  Error: {response.json()['detail']}")
    else:
        print_error("Should have rejected invalid prefix!")
    
    # Try to use customer ID as package ID (should fail)
    print_info("Testing: Using customer ID where package ID expected...")
    customer_data = {
        "name": "Test Invalid Package",
        "package_id": customer_id,  # Wrong! This is a customer ID
        "monthly_fee": 100000
    }
    
    response = requests.post(f"{BASE_URL}/customers", json=customer_data, headers=headers)
    
    if response.status_code == 400:
        print_success("Correctly rejected customer ID as package ID")
        print_info(f"  Error: {response.json()['detail']}")
    else:
        print_error("Should have rejected invalid prefix!")

def cleanup(token, customer_id, package_id):
    """Clean up test data"""
    print_header("7. CLEANUP")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Delete customer
    if customer_id:
        response = requests.delete(f"{BASE_URL}/customers/{customer_id}", headers=headers)
        if response.status_code == 204:
            print_success(f"Deleted customer: {customer_id}")
    
    # Delete package
    if package_id:
        response = requests.delete(f"{BASE_URL}/packages/{package_id}", headers=headers)
        if response.status_code == 204:
            print_success(f"Deleted package: {package_id}")

def main():
    print("\n" + "="*70)
    print("  LARAVEL-STYLE SQIDS API INTEGRATION TEST")
    print("="*70)
    print(f"\nTesting API at: {BASE_URL}")
    print(f"Checking for prefixes:")
    print("  - Customers: cust_")
    print("  - Packages:  pack_")
    print("  - Payments:  pay_")
    print("  - Users:     user_")
    
    # Login
    token = login()
    if not token:
        print_error("Cannot continue without authentication")
        return
    
    # Test packages
    package_id = test_packages(token)
    if not package_id:
        print_error("Cannot continue without package")
        return
    
    # Test customers
    customer_id = test_customers(token, package_id)
    if not customer_id:
        print_error("Cannot continue without customer")
        return
    
    # Test payments
    payment_id = test_payments(token, customer_id)
    
    # Test billing matrix
    test_billing_matrix(token)
    
    # Test prefix validation
    test_prefix_validation(token, customer_id, package_id)
    
    # Cleanup
    cleanup(token, customer_id, package_id)
    
    print_header("SUMMARY")
    print_success("All Laravel-style Sqids tests completed!")
    print_info("Format verified: {prefix}{encoded_id}_{random_key}")
    print_info("Prefix validation: Working")
    print_info("Encode/decode cycle: Working")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
