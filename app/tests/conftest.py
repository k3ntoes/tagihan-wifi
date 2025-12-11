"""
Test configuration and fixtures for pytest.

This module provides shared fixtures for testing the WiFi billing application,
including test database setup, authentication tokens, and test data factories.
"""

from typing import Generator

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, get_password_hash
from app.core.database import get_db
from app.main import app

# Test Database Fixtures


@pytest.fixture(scope="function")
def test_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Create an in-memory test database with clean state for each test.

    This fixture creates a fresh database with all required tables and
    initial test data for each test function.
    """
    # Create in-memory database
    con = duckdb.connect(":memory:")
    cursor = con.cursor()

    # Create sequences
    cursor.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_paket START 1 INCREMENT 1;
        CREATE SEQUENCE IF NOT EXISTS seq_pelanggan START 1 INCREMENT 1;
        CREATE SEQUENCE IF NOT EXISTS seq_tagihan START 1 INCREMENT 1;
        CREATE SEQUENCE IF NOT EXISTS seq_users START 1 INCREMENT 1;
    """)

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_users'),
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_superuser BOOLEAN DEFAULT FALSE,
            role VARCHAR(20) DEFAULT 'USER',
            pelanggan_id INTEGER,
            reset_token VARCHAR(255),
            reset_token_expires TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create paket table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paket (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_paket'),
            nama TEXT NOT NULL,
            harga INTEGER NOT NULL,
            kecepatan VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(nama, kecepatan)
        );
    """)

    # Create pelanggan table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pelanggan (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_pelanggan'),
            nama TEXT NOT NULL,
            alamat TEXT NOT NULL,
            no_hp TEXT NOT NULL,
            paket_id INTEGER NOT NULL,
            is_aktif BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(paket_id) REFERENCES paket (id),
            UNIQUE(nama, paket_id)
        );
    """)

    # Create tagihan table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tagihan (
            id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_tagihan'),
            pelanggan_id INTEGER NOT NULL,
            paket_id INTEGER NOT NULL,
            tahun INTEGER NOT NULL,
            bulan INTEGER NOT NULL,
            tanggal_bayar DATE,
            nominal INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(pelanggan_id) REFERENCES pelanggan(id),
            FOREIGN KEY(paket_id) REFERENCES paket(id),
            UNIQUE(tahun, bulan, pelanggan_id)
        );
    """)

    cursor.commit()

    yield cursor

    # Cleanup
    cursor.close()
    con.close()


@pytest.fixture(scope="function")
def test_client(test_db) -> TestClient:
    """
    Create a FastAPI TestClient with test database dependency override.

    Args:
        test_db: Test database fixture

    Returns:
        FastAPI TestClient configured with test database
    """

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# User and Authentication Fixtures


@pytest.fixture(scope="function")
def admin_user(test_db) -> dict:
    """
    Create an admin user in the test database.

    Returns:
        Dictionary containing admin user data
    """
    admin_password = "admin123"
    hashed_password = get_password_hash(admin_password)

    test_db.execute(
        """
        INSERT INTO users (username, email, hashed_password, is_superuser, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ["admin", "admin@example.com", hashed_password, True, "ADMIN", True],
    )
    test_db.commit()

    # Get the created user
    result = test_db.execute(
        "SELECT id, username, email, role, is_active FROM users WHERE username = ?",
        ["admin"],
    ).fetchone()

    return {
        "id": result[0],
        "username": result[1],
        "email": result[2],
        "role": result[3],
        "is_active": result[4],
        "password": admin_password,
    }


@pytest.fixture(scope="function")
def regular_user(test_db) -> dict:
    """
    Create a regular user in the test database.

    Returns:
        Dictionary containing regular user data
    """
    user_password = "user123"
    hashed_password = get_password_hash(user_password)

    test_db.execute(
        """
        INSERT INTO users (username, email, hashed_password, is_superuser, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ["testuser", "user@example.com", hashed_password, False, "USER", True],
    )
    test_db.commit()

    # Get the created user
    result = test_db.execute(
        "SELECT id, username, email, role, is_active FROM users WHERE username = ?",
        ["testuser"],
    ).fetchone()

    return {
        "id": result[0],
        "username": result[1],
        "email": result[2],
        "role": result[3],
        "is_active": result[4],
        "password": user_password,
    }


@pytest.fixture(scope="function")
def regular_user_with_pelanggan(test_db, test_paket, test_pelanggan) -> dict:
    """
    Create a regular user linked to a pelanggan.

    Returns:
        Dictionary containing user data with pelanggan_id
    """
    user_password = "user123"
    hashed_password = get_password_hash(user_password)

    # Create the user linked to pelanggan
    test_db.execute(
        """
        INSERT INTO users (username, email, hashed_password, is_superuser, role, is_active, pelanggan_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "linkeduser",
            "linked@example.com",
            hashed_password,
            False,
            "USER",
            True,
            test_pelanggan["id"],
        ],
    )
    test_db.commit()

    # Get the created user
    result = test_db.execute(
        "SELECT id, username, email, role, is_active, pelanggan_id FROM users WHERE username = ?",
        ["linkeduser"],
    ).fetchone()

    return {
        "id": result[0],
        "username": result[1],
        "email": result[2],
        "role": result[3],
        "is_active": result[4],
        "pelanggan_id": result[5],
        "password": user_password,
    }


@pytest.fixture(scope="function")
def admin_token(admin_user) -> str:
    """
    Create an access token for admin user.

    Args:
        admin_user: Admin user fixture

    Returns:
        JWT access token
    """
    token_data = {
        "sub": admin_user["username"],
        "user_id": admin_user["id"],
        "role": admin_user["role"],
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def user_token(regular_user) -> str:
    """
    Create an access token for regular user.

    Args:
        regular_user: Regular user fixture

    Returns:
        JWT access token
    """
    token_data = {
        "sub": regular_user["username"],
        "user_id": regular_user["id"],
        "role": regular_user["role"],
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def user_with_pelanggan_token(regular_user_with_pelanggan) -> str:
    """
    Create an access token for user linked to pelanggan.

    Args:
        regular_user_with_pelanggan: User with pelanggan fixture

    Returns:
        JWT access token
    """
    token_data = {
        "sub": regular_user_with_pelanggan["username"],
        "user_id": regular_user_with_pelanggan["id"],
        "role": regular_user_with_pelanggan["role"],
    }
    return create_access_token(token_data)


# Test Data Fixtures


@pytest.fixture(scope="function")
def test_paket(test_db) -> dict:
    """
    Create a test paket in the database.

    Returns:
        Dictionary containing paket data
    """
    test_db.execute(
        """
        INSERT INTO paket (nama, harga, kecepatan)
        VALUES (?, ?, ?)
        """,
        ["Paket Test 1", 100000, "10Mbps"],
    )
    test_db.commit()

    result = test_db.execute(
        "SELECT id, nama, harga, kecepatan FROM paket WHERE nama = ?", ["Paket Test 1"]
    ).fetchone()

    return {
        "id": result[0],
        "nama": result[1],
        "harga": result[2],
        "kecepatan": result[3],
    }


@pytest.fixture(scope="function")
def test_pelanggan(test_db, test_paket) -> dict:
    """
    Create a test pelanggan in the database.

    Returns:
        Dictionary containing pelanggan data
    """
    test_db.execute(
        """
        INSERT INTO pelanggan (nama, alamat, no_hp, paket_id, is_aktif)
        VALUES (?, ?, ?, ?, ?)
        """,
        ["Test Pelanggan", "Jl. Test No. 123", "081234567890", test_paket["id"], True],
    )
    test_db.commit()

    result = test_db.execute(
        "SELECT id, nama, alamat, no_hp, paket_id, is_aktif FROM pelanggan WHERE nama = ?",
        ["Test Pelanggan"],
    ).fetchone()

    return {
        "id": result[0],
        "nama": result[1],
        "alamat": result[2],
        "no_hp": result[3],
        "paket_id": result[4],
        "is_aktif": result[5],
    }


@pytest.fixture(scope="function")
def test_tagihan(test_db, test_pelanggan, test_paket) -> dict:
    """
    Create a test tagihan in the database.

    Returns:
        Dictionary containing tagihan data
    """
    test_db.execute(
        """
        INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, tanggal_bayar, nominal)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [test_pelanggan["id"], test_paket["id"], 2025, 12, "2025-12-15", 100000],
    )
    test_db.commit()

    result = test_db.execute(
        "SELECT id, pelanggan_id, paket_id, tahun, bulan, nominal FROM tagihan WHERE pelanggan_id = ? AND tahun = ? AND bulan = ?",
        [test_pelanggan["id"], 2025, 12],
    ).fetchone()

    return {
        "id": result[0],
        "pelanggan_id": result[1],
        "paket_id": result[2],
        "tahun": result[3],
        "bulan": result[4],
        "nominal": result[5],
    }
