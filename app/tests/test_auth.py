"""
Comprehensive unit tests for authentication endpoints.

Tests all authentication-related endpoints including registration, login,
token refresh, password management, and user info retrieval.
"""

from fastapi import status


class TestUserRegistration:
    """Tests for POST /auth/register endpoint."""

    def test_register_success(self, test_client):
        """Test successful user registration."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
        assert "hashed_password" not in data
        assert data["role"] == "USER"
        assert data["is_active"] is True

    def test_register_duplicate_username(self, test_client, admin_user):
        """Test registration with duplicate username."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "admin",  # Already exists
                "email": "newemail@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, test_client, admin_user):
        """Test registration with duplicate email."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "newusername",
                "email": "admin@example.com",  # Already exists
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_username(self, test_client):
        """Test registration with username too short."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "ab",  # Less than 3 characters
                "email": "user@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, test_client):
        """Test registration with password too short."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "user@example.com",
                "password": "12345",  # Less than 6 characters
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Tests for POST /auth/token (login) endpoint."""

    def test_login_success(self, test_client, admin_user):
        """Test successful login."""
        response = test_client.post(
            "/auth/login",
            data={
                "username": admin_user["username"],
                "password": admin_user["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, test_client):
        """Test login with non-existent username."""
        response = test_client.post(
            "/auth/login", data={"username": "nonexistent", "password": "password123"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect username or password" in response.json()["detail"].lower()

    def test_login_invalid_password(self, test_client, admin_user):
        """Test login with incorrect password."""
        response = test_client.post(
            "/auth/login",
            data={"username": admin_user["username"], "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect username or password" in response.json()["detail"].lower()

    def test_login_inactive_user(self, test_client, test_db):
        """Test login with inactive user."""
        from app.core.auth import get_password_hash

        # Create inactive user
        hashed_password = get_password_hash("password123")
        test_db.execute(
            """
            INSERT INTO users (username, email, hashed_password, is_active, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            ["inactiveuser", "inactive@example.com", hashed_password, False, "USER"],
        )
        test_db.commit()

        response = test_client.post(
            "/auth/login", data={"username": "inactiveuser", "password": "password123"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inactive" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Tests for POST /auth/refresh endpoint."""

    def test_refresh_token_success(self, test_client, admin_user):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = test_client.post(
            "/auth/login",
            data={
                "username": admin_user["username"],
                "password": admin_user["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = test_client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, test_client):
        """Test refresh with invalid token."""
        response = test_client.post(
            "/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_with_access_token(self, test_client, admin_token):
        """Test refresh with access token (should fail)."""
        response = test_client.post(
            "/auth/refresh",
            json={"refresh_token": admin_token},  # Using access token instead
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Tests for GET /auth/me endpoint."""

    def test_get_current_user_success(self, test_client, admin_user, admin_token):
        """Test successful retrieval of current user info."""
        response = test_client.get(
            "/auth/me", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == admin_user["username"]
        assert data["email"] == admin_user["email"]
        assert data["role"] == admin_user["role"]
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_current_user_no_token(self, test_client):
        """Test getting current user without authentication."""
        response = test_client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token."""
        response = test_client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """Tests for POST /auth/change-password endpoint."""

    def test_change_password_success(self, test_client, admin_user, admin_token):
        """Test successful password change."""
        response = test_client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "old_password": admin_user["password"],
                "new_password": "newpassword123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "successfully" in response.json()["message"].lower()

        # Verify can login with new password
        login_response = test_client.post(
            "/auth/login",
            data={"username": admin_user["username"], "password": "newpassword123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old_password(self, test_client, admin_token):
        """Test password change with incorrect old password."""
        response = test_client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"old_password": "wrongpassword", "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_no_auth(self, test_client):
        """Test password change without authentication."""
        response = test_client.post(
            "/auth/change-password",
            json={"old_password": "oldpass", "new_password": "newpass123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_short_new_password(self, test_client, admin_token):
        """Test password change with new password too short."""
        response = test_client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "old_password": "admin123",
                "new_password": "12345",  # Too short
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestForgotPassword:
    """Tests for POST /auth/forgot-password endpoint."""

    def test_forgot_password_success(self, test_client, admin_user):
        """Test successful password reset request."""
        response = test_client.post(
            "/auth/forgot-password", json={"email": admin_user["email"]}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "reset_token" in data
        assert data["reset_token"] is not None

    def test_forgot_password_nonexistent_email(self, test_client):
        """Test password reset request with non-existent email (always returns 200 for security)."""
        response = test_client.post(
            "/auth/forgot-password", json={"email": "nonexistent@example.com"}
        )

        # Returns 200 to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK

    def test_forgot_password_invalid_email(self, test_client):
        """Test password reset request with invalid email format."""
        response = test_client.post(
            "/auth/forgot-password", json={"email": "invalid-email"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResetPassword:
    """Tests for POST /auth/reset-password endpoint."""

    def test_reset_password_success(self, test_client, admin_user):
        """Test successful password reset."""
        # First get reset token
        forgot_response = test_client.post(
            "/auth/forgot-password", json={"email": admin_user["email"]}
        )
        reset_token = forgot_response.json()["reset_token"]

        # Reset password
        response = test_client.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "successfully" in response.json()["message"].lower()

        # Verify can login with new password
        login_response = test_client.post(
            "/auth/login",
            data={"username": admin_user["username"], "password": "newpassword123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_reset_password_invalid_token(self, test_client):
        """Test password reset with invalid token."""
        response = test_client.post(
            "/auth/reset-password",
            json={"token": "invalid_token", "new_password": "newpassword123"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_short_password(self, test_client, admin_user):
        """Test password reset with password too short."""
        # Get reset token
        forgot_response = test_client.post(
            "/auth/forgot-password", json={"email": admin_user["email"]}
        )
        reset_token = forgot_response.json()["reset_token"]

        # Try to reset with short password
        response = test_client.post(
            "/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "12345",  # Too short
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
