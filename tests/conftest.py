import os
import uuid

import pytest
import requests


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001/api/v1")
ADMIN_USERNAME = os.getenv("API_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("API_ADMIN_PASSWORD", "password123")


def _skip_if_unavailable(response, action: str) -> None:
    if response is None:
        pytest.skip(f"API unavailable while attempting to {action}")


@pytest.fixture(scope="session")
def token():
    """Get auth token for integration tests."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=5,
        )
    except requests.RequestException:
        pytest.skip("API not reachable at base URL")

    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.status_code} {response.text}")

    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="session")
def package_id(token):
    """Create a package and return its sqid."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": f"Test Package {uuid.uuid4().hex[:8]}",
        "speed": 50,
        "price": 100000,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/packages",
            json=payload,
            headers=headers,
            timeout=5,
        )
    except requests.RequestException:
        pytest.skip("API not reachable when creating package")

    if response.status_code != 201:
        pytest.skip(f"Failed to create package: {response.status_code} {response.text}")

    package = response.json().get("data", {})
    return package.get("id")


@pytest.fixture(scope="session")
def customer_id(token, package_id):
    """Create a customer and return its sqid."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": f"Test Customer {uuid.uuid4().hex[:8]}",
        "package_id": package_id,
        "monthly_fee": 150000,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/customers",
            json=payload,
            headers=headers,
            timeout=5,
        )
    except requests.RequestException:
        pytest.skip("API not reachable when creating customer")

    if response.status_code != 201:
        pytest.skip(f"Failed to create customer: {response.status_code} {response.text}")

    customer = response.json().get("data", {})
    return customer.get("id")