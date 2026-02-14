"""
Test user management endpoints
"""

import pytest
import json
from datetime import datetime


class TestChangePassword:
    """Test password change endpoint"""

    def test_change_password_success(self, admin_client, admin_token):
        """Test successful password change"""
        response = admin_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "old_password": "admin123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["username"] == "admin"

    def test_change_password_wrong_old_password(self, admin_client, admin_token):
        """Test password change with wrong old password"""
        response = admin_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_missing_auth(self, admin_client):
        """Test password change without authentication"""
        response = admin_client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "admin123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints"""

    def test_list_users_success(self, admin_client, admin_token):
        """Test listing users successfully"""
        response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "per_page": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)

    def test_list_users_pagination(self, admin_client, admin_token):
        """Test user list pagination metadata"""
        response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "per_page": 5},
        )
        assert response.status_code == 200
        meta = response.json()["meta"]
        assert "total" in meta
        assert "page" in meta
        assert "perPage" in meta
        assert "totalPages" in meta
        assert "hasNext" in meta
        assert "hasPrev" in meta

    def test_list_users_non_admin(self, client, user_token):
        """Test that non-admin cannot list users"""
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_get_user_success(self, admin_client, admin_token):
        """Test getting specific user"""
        # First, list users to get a user ID
        list_response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        users = list_response.json()["data"]
        if users:
            user_id = users[0]["id"]
            response = admin_client.get(
                f"/api/v1/auth/users/{user_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == user_id

    def test_get_user_not_found(self, admin_client, admin_token):
        """Test getting non-existent user"""
        response = admin_client.get(
            "/api/v1/auth/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_update_user_role(self, admin_client, admin_token):
        """Test updating user role"""
        # Get a user first
        list_response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        users = list_response.json()["data"]
        # Find a non-admin user
        user_to_update = next((u for u in users if u["role"] == "user"), None)
        
        if user_to_update:
            response = admin_client.patch(
                f"/api/v1/auth/users/{user_to_update['id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role": "admin"},
            )
            assert response.status_code == 200
            assert response.json()["data"]["role"] == "admin"

    def test_update_user_active_status(self, admin_client, admin_token):
        """Test updating user active status"""
        list_response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        users = list_response.json()["data"]
        if users:
            user_to_update = users[0]
            response = admin_client.patch(
                f"/api/v1/auth/users/{user_to_update['id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"is_active": False},
            )
            assert response.status_code == 200
            assert response.json()["data"]["isActive"] == False

    def test_update_user_duplicate_username(self, admin_client, admin_token):
        """Test updating user to duplicate username"""
        list_response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        users = list_response.json()["data"]
        if len(users) >= 2:
            user1 = users[0]
            user2 = users[1]
            # Try to update user2 with user1's username
            response = admin_client.patch(
                f"/api/v1/auth/users/{user2['id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"username": user1["username"]},
            )
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"].lower()

    def test_delete_user_success(self, admin_client, admin_token, test_db):
        """Test deleting user successfully"""
        # Create a test user first
        from app.core.auth import AuthService
        from app.db.database import Database
        
        db = Database()
        auth_service = AuthService(db)
        test_user = auth_service.create_user("testdeleteuser", "password123", "user")
        
        # Now delete the user
        response = admin_client.delete(
            f"/api/v1/auth/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

    def test_delete_own_account(self, admin_client, admin_token):
        """Test that admin cannot delete own account"""
        # Get current admin user ID from token
        list_response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        admin_user = next(u for u in list_response.json()["data"] if u["role"] == "admin")
        
        response = admin_client.delete(
            f"/api/v1/auth/users/{admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "own account" in response.json()["detail"].lower()

    def test_delete_user_non_admin(self, client, user_token):
        """Test that non-admin cannot delete users"""
        response = client.delete(
            "/api/v1/auth/users/2",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


class TestResponseFormat:
    """Test response format and field names"""

    def test_user_response_camel_case(self, admin_client, admin_token):
        """Test that user response uses camelCase"""
        response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = response.json()
        if data["data"]:
            user = data["data"][0]
            # Check for camelCase fields
            assert "isActive" in user or "is_active" not in user
            assert "createdAt" in user or "created_at" not in user

    def test_pagination_meta_camel_case(self, admin_client, admin_token):
        """Test that pagination metadata uses camelCase"""
        response = admin_client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        meta = response.json()["meta"]
        # Check for camelCase fields
        assert "perPage" in meta or "per_page" not in meta
        assert "totalPages" in meta or "total_pages" not in meta
        assert "hasNext" in meta or "has_next" not in meta
        assert "hasPrev" in meta or "has_prev" not in meta
