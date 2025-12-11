"""
Comprehensive unit tests for pelanggan (customer) endpoints.

Tests all pelanggan-related endpoints with proper RBAC validation.
All pelanggan endpoints require ADMIN role.
"""

from fastapi import status
from app.core.sqids_manager import SqidsManager


class TestGetAllPelanggan:
    """Tests for GET /pelanggan endpoint."""

    def test_get_all_pelanggan_as_admin(self, test_client, admin_token, test_pelanggan):
        """Test admin can retrieve all pelanggan."""
        response = test_client.get(
            "/pelanggan", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data
        assert len(data["content"]) >= 1
        # Verify pelanggan structure
        assert "id" in data["content"][0]
        assert "nama" in data["content"][0]
        assert "alamat" in data["content"][0]
        assert "no_hp" in data["content"][0]
        assert "paket_id" in data["content"][0]

    def test_get_all_pelanggan_as_user(self, test_client, user_token, test_pelanggan):
        """Test regular user cannot retrieve pelanggan (403 Forbidden)."""
        response = test_client.get(
            "/pelanggan", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_pelanggan_no_auth(self, test_client, test_pelanggan):
        """Test unauthenticated request fails."""
        response = test_client.get("/pelanggan")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_pelanggan_pagination(
        self, test_client, admin_token, test_db, test_paket
    ):
        """Test pagination parameters work."""
        # Create multiple pelanggan
        for i in range(5):
            test_db.execute(
                "INSERT INTO pelanggan (nama, alamat, no_hp, paket_id, is_aktif) VALUES (?, ?, ?, ?, ?)",
                [
                    f"Pelanggan {i}",
                    f"Alamat {i}",
                    f"08123456{i:04d}",
                    test_paket["id"],
                    True,
                ],
            )
        test_db.commit()

        # Test with page size
        response = test_client.get(
            "/pelanggan?page=1&page_size=3",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "page" in data
        assert "page_size" in data


class TestGetPelangganById:
    """Tests for GET /pelanggan/{id} endpoint."""

    def test_get_pelanggan_by_id_as_admin(
        self, test_client, admin_token, test_pelanggan
    ):
        """Test admin can retrieve pelanggan by ID."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.get(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["nama"] == test_pelanggan["nama"]
        assert data["alamat"] == test_pelanggan["alamat"]
        assert data["no_hp"] == test_pelanggan["no_hp"]

    def test_get_pelanggan_by_id_as_user(self, test_client, user_token, test_pelanggan):
        """Test regular user cannot retrieve pelanggan by ID."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.get(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_pelanggan_by_id_not_found(self, test_client, admin_token):
        """Test getting non-existent pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)  # Non-existent ID

        response = test_client.get(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_pelanggan_by_invalid_id(self, test_client, admin_token):
        """Test getting pelanggan with invalid ID format."""
        response = test_client.get(
            "/pelanggan/invalid-id", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreatePelanggan:
    """Tests for POST /pelanggan endpoint."""

    def test_create_pelanggan_as_admin(self, test_client, admin_token, test_paket):
        """Test admin can create pelanggan."""
        response = test_client.post(
            "/pelanggan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": "New Pelanggan",
                "alamat": "Jl. Baru No. 456",
                "no_hp": "081234567777",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_create_pelanggan_as_user(self, test_client, user_token, test_paket):
        """Test regular user cannot create pelanggan (403 Forbidden)."""
        response = test_client.post(
            "/pelanggan",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "nama": "New Pelanggan",
                "alamat": "Jl. Baru No. 456",
                "no_hp": "081234567777",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_pelanggan_no_auth(self, test_client, test_paket):
        """Test unauthenticated request fails."""
        response = test_client.post(
            "/pelanggan",
            json={
                "nama": "New Pelanggan",
                "alamat": "Jl. Baru No. 456",
                "no_hp": "081234567777",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_pelanggan_duplicate(self, test_client, admin_token, test_pelanggan):
        """Test creating duplicate pelanggan fails."""
        response = test_client.post(
            "/pelanggan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": test_pelanggan["nama"],
                "alamat": "Different address",
                "no_hp": "081111111111",
                "paket_id": test_pelanggan["paket_id"],
                "is_aktif": True,
            },
        )

        # Should fail due to unique constraint (nama, paket_id)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
        ]

    def test_create_pelanggan_invalid_paket_id(self, test_client, admin_token):
        """Test creating pelanggan with non-existent paket_id."""
        response = test_client.post(
            "/pelanggan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": "New Pelanggan",
                "alamat": "Jl. Baru No. 456",
                "no_hp": "081234567777",
                "paket_id": 99999,  # Non-existent paket
                "is_aktif": True,
            },
        )

        # Should fail due to foreign key constraint
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_create_pelanggan_missing_fields(self, test_client, admin_token):
        """Test creating pelanggan with missing required fields."""
        response = test_client.post(
            "/pelanggan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": "Incomplete Pelanggan"
                # Missing alamat, no_hp, paket_id
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdatePelanggan:
    """Tests for PUT /pelanggan/{id} endpoint."""

    def test_update_pelanggan_as_admin(
        self, test_client, admin_token, test_pelanggan, test_paket
    ):
        """Test admin can update pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.put(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": "Updated Pelanggan Name",
                "alamat": "Updated Address",
                "no_hp": "081999999999",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_update_pelanggan_as_user(
        self, test_client, user_token, test_pelanggan, test_paket
    ):
        """Test regular user cannot update pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.put(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "nama": "Updated",
                "alamat": "Updated",
                "no_hp": "081999999999",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_pelanggan_not_found(self, test_client, admin_token, test_paket):
        """Test updating non-existent pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)

        response = test_client.put(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": "Updated",
                "alamat": "Updated",
                "no_hp": "081999999999",
                "paket_id": test_paket["id"],
                "is_aktif": True,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_pelanggan_deactivate(
        self, test_client, admin_token, test_pelanggan, test_paket
    ):
        """Test deactivating a pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.put(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "nama": test_pelanggan["nama"],
                "alamat": test_pelanggan["alamat"],
                "no_hp": test_pelanggan["no_hp"],
                "paket_id": test_paket["id"],
                "is_aktif": False,  # Deactivate
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestDeletePelanggan:
    """Tests for DELETE /pelanggan/{id} endpoint."""

    def test_delete_pelanggan_as_admin(
        self, test_client, admin_token, test_db, test_paket
    ):
        """Test admin can delete pelanggan."""
        # Create a pelanggan to delete
        test_db.execute(
            "INSERT INTO pelanggan (nama, alamat, no_hp, paket_id, is_aktif) VALUES (?, ?, ?, ?, ?)",
            ["Pelanggan To Delete", "Alamat", "081234567890", test_paket["id"], True],
        )
        test_db.commit()

        result = test_db.execute(
            "SELECT id FROM pelanggan WHERE nama = ?", ["Pelanggan To Delete"]
        ).fetchone()
        pelanggan_id = result[0]

        sqids = SqidsManager()
        encoded_id = sqids.encode(pelanggan_id)

        response = test_client.delete(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_delete_pelanggan_as_user(self, test_client, user_token, test_pelanggan):
        """Test regular user cannot delete pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.delete(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_pelanggan_not_found(self, test_client, admin_token):
        """Test deleting non-existent pelanggan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)

        response = test_client.delete(
            f"/pelanggan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_pelanggan_no_auth(self, test_client, test_pelanggan):
        """Test unauthenticated delete fails."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_pelanggan["id"])

        response = test_client.delete(f"/pelanggan/{encoded_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
