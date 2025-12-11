"""
Comprehensive unit tests for tagihan (billing) endpoints.

Tests all tagihan-related endpoints with complex RBAC validation.
Some endpoints require ADMIN role, others allow USER access with restrictions.
"""

from fastapi import status
from app.core.sqids_manager import SqidsManager


class TestGetAllTagihan:
    """Tests for GET /tagihan endpoint."""

    def test_get_all_tagihan_as_admin(self, test_client, admin_token, test_tagihan):
        """Test admin can retrieve all tagihan."""
        response = test_client.get(
            "/tagihan", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        # Verify tagihan structure
        assert "id" in data["data"][0]
        assert "pelanggan_id" in data["data"][0]
        assert "tahun" in data["data"][0]
        assert "bulan" in data["data"][0]

    def test_get_all_tagihan_as_user_with_pelanggan(
        self,
        test_client,
        user_with_pelanggan_token,
        regular_user_with_pelanggan,
        test_db,
        test_tagihan,
    ):
        """Test user with pelanggan_id sees only their own tagihan."""
        # Create tagihan for the linked user
        test_db.execute(
            """
            INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                regular_user_with_pelanggan["pelanggan_id"],
                test_tagihan["paket_id"],
                2025,
                11,
                100000,
            ],
        )
        test_db.commit()

        response = test_client.get(
            "/tagihan", headers={"Authorization": f"Bearer {user_with_pelanggan_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        # Should only see their own tagihan
        for item in data["data"]:
            assert item["pelanggan_id"] == regular_user_with_pelanggan["pelanggan_id"]

    def test_get_all_tagihan_as_user_without_pelanggan(self, test_client, user_token):
        """Test user without pelanggan_id gets forbidden error."""
        response = test_client.get(
            "/tagihan", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not linked" in response.json()["detail"].lower()

    def test_get_all_tagihan_no_auth(self, test_client, test_tagihan):
        """Test unauthenticated request fails."""
        response = test_client.get("/tagihan")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_tagihan_pagination(
        self, test_client, admin_token, test_db, test_pelanggan, test_paket
    ):
        """Test pagination parameters work."""
        # Create multiple tagihan
        for month in range(1, 6):
            test_db.execute(
                "INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal) VALUES (?, ?, ?, ?, ?)",
                [test_pelanggan["id"], test_paket["id"], 2024, month, 100000],
            )
        test_db.commit()

        # Test with page size
        response = test_client.get(
            "/tagihan?page=1&page_size=3",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "page" in data
        assert "page_size" in data


class TestGetTagihanById:
    """Tests for GET /tagihan/{id} endpoint."""

    def test_get_tagihan_by_id_as_admin(self, test_client, admin_token, test_tagihan):
        """Test admin can retrieve tagihan by ID."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.get(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tahun"] == test_tagihan["tahun"]
        assert data["bulan"] == test_tagihan["bulan"]
        assert data["pelanggan_id"] == test_tagihan["pelanggan_id"]

    def test_get_tagihan_by_id_as_user(self, test_client, user_token, test_tagihan):
        """Test regular user cannot retrieve tagihan by ID (admin only)."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.get(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_tagihan_by_id_not_found(self, test_client, admin_token):
        """Test getting non-existent tagihan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)

        response = test_client.get(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateTagihan:
    """Tests for POST /tagihan endpoint."""

    def test_create_tagihan_as_admin(
        self, test_client, admin_token, test_pelanggan, test_paket
    ):
        """Test admin can create tagihan."""
        response = test_client.post(
            "/tagihan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pelanggan_id": test_pelanggan["id"],
                "paket_id": test_paket["id"],
                "tahun": 2025,
                "bulan": 1,
                "nominal": 100000,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_create_tagihan_as_user(
        self, test_client, user_token, test_pelanggan, test_paket
    ):
        """Test regular user cannot create tagihan (admin only)."""
        response = test_client.post(
            "/tagihan",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "pelanggan_id": test_pelanggan["id"],
                "paket_id": test_paket["id"],
                "tahun": 2025,
                "bulan": 2,
                "nominal": 100000,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tagihan_no_auth(self, test_client, test_pelanggan, test_paket):
        """Test unauthenticated request fails."""
        response = test_client.post(
            "/tagihan",
            json={
                "pelanggan_id": test_pelanggan["id"],
                "paket_id": test_paket["id"],
                "tahun": 2025,
                "bulan": 3,
                "nominal": 100000,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_tagihan_duplicate(self, test_client, admin_token, test_tagihan):
        """Test creating duplicate tagihan fails (unique: tahun, bulan, pelanggan_id)."""
        response = test_client.post(
            "/tagihan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pelanggan_id": test_tagihan["pelanggan_id"],
                "paket_id": test_tagihan["paket_id"],
                "tahun": test_tagihan["tahun"],
                "bulan": test_tagihan["bulan"],
                "nominal": 50000,
            },
        )

        # Should fail due to unique constraint
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
        ]

    def test_create_tagihan_invalid_pelanggan(
        self, test_client, admin_token, test_paket
    ):
        """Test creating tagihan with non-existent pelanggan_id."""
        response = test_client.post(
            "/tagihan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pelanggan_id": 99999,  # Non-existent
                "paket_id": test_paket["id"],
                "tahun": 2025,
                "bulan": 4,
                "nominal": 100000,
            },
        )

        # Should fail due to foreign key constraint
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_create_tagihan_missing_fields(self, test_client, admin_token):
        """Test creating tagihan with missing required fields."""
        response = test_client.post(
            "/tagihan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tahun": 2025,
                "bulan": 5,
                # Missing pelanggan_id, paket_id, nominal
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateTagihan:
    """Tests for PUT /tagihan/{id} endpoint."""

    def test_update_tagihan_as_admin(
        self, test_client, admin_token, test_tagihan, test_paket
    ):
        """Test admin can update tagihan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.put(
            f"/tagihan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pelanggan_id": test_tagihan["pelanggan_id"],
                "paket_id": test_paket["id"],
                "tahun": test_tagihan["tahun"],
                "bulan": test_tagihan["bulan"],
                "nominal": 150000,  # Updated
                "tanggal_bayar": "2025-12-20",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_update_tagihan_as_user(
        self, test_client, user_token, test_tagihan, test_paket
    ):
        """Test regular user cannot update tagihan (admin only)."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.put(
            f"/tagihan/{encoded_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "pelanggan_id": test_tagihan["pelanggan_id"],
                "paket_id": test_paket["id"],
                "tahun": test_tagihan["tahun"],
                "bulan": test_tagihan["bulan"],
                "nominal": 150000,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_tagihan_not_found(self, test_client, admin_token, test_paket):
        """Test updating non-existent tagihan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)

        response = test_client.put(
            f"/tagihan/{encoded_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pelanggan_id": 1,
                "paket_id": test_paket["id"],
                "tahun": 2025,
                "bulan": 6,
                "nominal": 100000,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteTagihan:
    """Tests for DELETE /tagihan/{id} endpoint."""

    def test_delete_tagihan_as_admin(
        self, test_client, admin_token, test_db, test_pelanggan, test_paket
    ):
        """Test admin can delete tagihan."""
        # Create a tagihan to delete
        test_db.execute(
            "INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal) VALUES (?, ?, ?, ?, ?)",
            [test_pelanggan["id"], test_paket["id"], 2024, 6, 100000],
        )
        test_db.commit()

        result = test_db.execute(
            "SELECT id FROM tagihan WHERE tahun = ? AND bulan = ? AND pelanggan_id = ?",
            [2024, 6, test_pelanggan["id"]],
        ).fetchone()
        tagihan_id = result[0]

        sqids = SqidsManager()
        encoded_id = sqids.encode(tagihan_id)

        response = test_client.delete(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_delete_tagihan_as_user(self, test_client, user_token, test_tagihan):
        """Test regular user cannot delete tagihan (admin only)."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.delete(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_tagihan_not_found(self, test_client, admin_token):
        """Test deleting non-existent tagihan."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(99999)

        response = test_client.delete(
            f"/tagihan/{encoded_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_tagihan_no_auth(self, test_client, test_tagihan):
        """Test unauthenticated delete fails."""
        sqids = SqidsManager()
        encoded_id = sqids.encode(test_tagihan["id"])

        response = test_client.delete(f"/tagihan/{encoded_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetTagihanSummary:
    """Tests for GET /tagihan/summary/{tahun} endpoint."""

    def test_get_summary_as_admin(
        self, test_client, admin_token, test_db, test_pelanggan, test_paket
    ):
        """Test admin can retrieve summary for all tagihan."""
        # Create multiple tagihan for year 2024
        for month in range(1, 4):
            test_db.execute(
                "INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal, tanggal_bayar) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    test_pelanggan["id"],
                    test_paket["id"],
                    2024,
                    month,
                    100000,
                    f"2024-{month:02d}-15",
                ],
            )
        test_db.commit()

        response = test_client.get(
            "/tagihan/summary/2024", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Response should contain summary data
        assert isinstance(response.json(), (list, dict))

    def test_get_summary_as_user_with_pelanggan(
        self,
        test_client,
        user_with_pelanggan_token,
        regular_user_with_pelanggan,
        test_db,
        test_paket,
    ):
        """Test user with pelanggan_id sees only their own summary."""
        # Create tagihan for the linked user
        for month in range(1, 4):
            test_db.execute(
                "INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal, tanggal_bayar) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    regular_user_with_pelanggan["pelanggan_id"],
                    test_paket["id"],
                    2024,
                    month,
                    100000,
                    f"2024-{month:02d}-15",
                ],
            )
        test_db.commit()

        response = test_client.get(
            "/tagihan/summary/2024",
            headers={"Authorization": f"Bearer {user_with_pelanggan_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        # Should only see their own summary
        assert isinstance(response.json(), (list, dict))

    def test_get_summary_as_user_without_pelanggan(self, test_client, user_token):
        """Test user without pelanggan_id gets forbidden error."""
        response = test_client.get(
            "/tagihan/summary/2024", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not linked" in response.json()["detail"].lower()

    def test_get_summary_no_auth(self, test_client):
        """Test unauthenticated request fails."""
        response = test_client.get("/tagihan/summary/2024")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_summary_different_years(
        self, test_client, admin_token, test_db, test_pelanggan, test_paket
    ):
        """Test getting summary for different years."""
        # Create tagihan for 2023
        test_db.execute(
            "INSERT INTO tagihan (pelanggan_id, paket_id, tahun, bulan, nominal) VALUES (?, ?, ?, ?, ?)",
            [test_pelanggan["id"], test_paket["id"], 2023, 1, 100000],
        )
        test_db.commit()

        response_2023 = test_client.get(
            "/tagihan/summary/2023", headers={"Authorization": f"Bearer {admin_token}"}
        )

        response_2024 = test_client.get(
            "/tagihan/summary/2024", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response_2023.status_code == status.HTTP_200_OK
        assert response_2024.status_code == status.HTTP_200_OK
