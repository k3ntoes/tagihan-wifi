# API Documentation - Tagihan WiFi

## Base Information

- **Base URL**: `http://localhost:3000` (atau sesuai konfigurasi `app_host` dan `app_port`)
- **Content-Type**: `application/json`
- **Framework**: FastAPI
- **Database**: DuckDB
- **Authentication**: JWT (JSON Web Token)
- **Authorization**: Role-Based Access Control (RBAC)

## Global Response Structure

### Pagination Response
Semua endpoint list menggunakan struktur pagination berikut:

```json
{
  "content": [...],
  "page": 1,
  "size": 10,
  "total_elements": 100,
  "total_pages": 10,
  "number_of_elements": 10,
  "is_last": false,
  "is_first": true,
  "is_empty": false
}
```

### Error Response
```json
{
  "detail": "Error message description"
}
```

atau

```json
{
  "errors": "Error message description"
}
```

## Encoding ID
Semua ID dalam response menggunakan **Sqids** (encoded string) untuk keamanan. 
- ID dalam response: string terenkripsi (contoh: `"k3aBc9Xy"`)
- ID dalam request POST/PUT: untuk `pelanggan_id` dan `paket_id` gunakan encoded string
- ID dalam path parameter: gunakan encoded string

---

## Authentication & Authorization

### Authentication
Semua endpoint (kecuali authentication endpoints) memerlukan **JWT token** dalam Authorization header.

**Format Header:**
```
Authorization: Bearer <access_token>
```

### Roles
Sistem menggunakan 2 role:
- **ADMIN**: Full access ke semua endpoints
- **USER**: Limited access - hanya bisa melihat data tagihan mereka sendiri

### Access Control Matrix

| Endpoint | ADMIN | USER |
|----------|-------|------|
| `/auth/*` | ✅ | ✅ |
| `/paket/*` | ✅ | ❌ (403 Forbidden) |
| `/pelanggan/*` | ✅ | ❌ (403 Forbidden) |
| `/tagihan/` (GET) | ✅ All data | ✅ Filtered by pelanggan_id |
| `/tagihan/summary/{tahun}` | ✅ All data | ✅ Filtered by pelanggan_id |
| `/tagihan/{id}` (GET) | ✅ | ❌ (403 Forbidden) |
| `/tagihan/` (POST/PUT/DELETE) | ✅ | ❌ (403 Forbidden) |

---

## 0. Authentication Endpoints

### 0.1 User Registration
**Endpoint**: `POST /auth/register`

**Description**: Mendaftarkan user baru

**Authentication**: None required

**Request Body**:
```json
{
  "username": "testuser",
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "USER"
}
```

**Request Body Schema**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| username | string | Yes | - | Username (min 3 chars) |
| email | string (email) | Yes | - | Email address |
| password | string | Yes | - | Password (min 6 chars) |
| role | string | No | USER | Role: ADMIN or USER |

**Response Success (201)**:
```json
{
  "id": 2,
  "username": "testuser",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "role": "USER",
  "pelanggan_id": null,
  "created_at": "2025-12-11T19:00:00",
  "updated_at": "2025-12-11T19:00:00"
}
```

**Response Error (400)**:
```json
{
  "detail": "Username already registered"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

---

### 0.2 User Login
**Endpoint**: `POST /auth/login`

**Description**: Login dan mendapatkan access token

**Authentication**: None required

**Request Body** (form-urlencoded):
```
username=admin&password=admin123
```

**Response Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response Error (401)**:
```json
{
  "detail": "Incorrect username or password"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

### 0.3 Refresh Token
**Endpoint**: `POST /auth/refresh`

**Description**: Refresh access token menggunakan refresh token

**Authentication**: None required

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token_here"}'
```

---

### 0.4 Get Current User
**Endpoint**: `GET /auth/me`

**Description**: Mendapatkan informasi user yang sedang login

**Authentication**: Required (Bearer token)

**Response Success (200)**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "role": "ADMIN",
  "pelanggan_id": null,
  "created_at": "2025-12-11T19:00:00",
  "updated_at": "2025-12-11T19:00:00"
}
```

**Example Request**:
```bash
TOKEN="your_access_token_here"
curl -X GET "http://localhost:3000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 0.5 Change Password
**Endpoint**: `POST /auth/change-password`

**Description**: Mengubah password user yang sedang login

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "old_password": "currentpassword",
  "new_password": "newpassword123"
}
```

**Request Body Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| old_password | string | Yes | Password lama |
| new_password | string | Yes | Password baru (min 6 chars) |

**Response Success (200)**:
```json
{
  "message": "Password changed successfully"
}
```

**Response Error (400)**:
```json
{
  "detail": "Incorrect old password"
}
```

**Example Request**:
```bash
TOKEN="your_access_token_here"
curl -X POST "http://localhost:3000/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "newadmin123"
  }'
```

---

### 0.6 Forgot Password
**Endpoint**: `POST /auth/forgot-password`

**Description**: Request reset password token

**Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response Success (200)**:
```json
{
  "message": "If email exists, reset token has been sent",
  "reset_token": "abc123xyz...",
  "expires_at": "2025-12-11T20:00:00"
}
```

> **Note**: Dalam production, `reset_token` tidak dikembalikan di response. Token harus dikirim via email.

**Example Request**:
```bash
curl -X POST "http://localhost:3000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 0.7 Reset Password
**Endpoint**: `POST /auth/reset-password`

**Description**: Reset password menggunakan reset token

**Authentication**: None required

**Request Body**:
```json
{
  "token": "reset_token_from_email",
  "new_password": "newpassword123"
}
```

**Request Body Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | Reset token dari email |
| new_password | string | Yes | Password baru (min 6 chars) |

**Response Success (200)**:
```json
{
  "message": "Password reset successfully"
}
```

**Response Error (400)**:
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123xyz...",
    "new_password": "newpassword123"
  }'
```

---

## 1. Paket (Package) Endpoints

### 1.1 Get All Paket
**Endpoint**: `GET /paket`

**Description**: Mengambil daftar semua paket dengan pagination

**Authentication**: Required (Bearer token)

**Authorization**: ADMIN only

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Nomor halaman |
| size | integer | No | 10 | Jumlah data per halaman |
| sort | string | No | null | Field untuk sorting |
| direction | string | No | null | Arah sorting (ASC/DESC) |
| nama | string | No | null | Filter berdasarkan nama paket |
| kecepatan | string | No | null | Filter berdasarkan kecepatan |

**Response Success (200)**:
```json
{
  "content": [
    {
      "id": "k3aBc9Xy",
      "nama": "Paket Premium",
      "harga": 300000,
      "kecepatan": "100 Mbps",
      "created_at": "2024-01-15 10:30:00",
      "updated_at": "2024-01-15 10:30:00"
    }
  ],
  "page": 1,
  "size": 10,
  "total_elements": 1,
  "total_pages": 1,
  "number_of_elements": 1,
  "is_last": true,
  "is_first": true,
  "is_empty": false
}
```

**Example Request**:
```bash
TOKEN="your_admin_token_here"
curl -X GET "http://localhost:3000/paket?page=1&size=10&nama=Premium" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 1.2 Get Paket by ID
**Endpoint**: `GET /paket/{id}`

**Description**: Mengambil detail paket berdasarkan ID

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID paket |

**Response Success (200)**:
```json
{
  "id": "k3aBc9Xy",
  "nama": "Paket Premium",
  "harga": 300000,
  "kecepatan": "100 Mbps",
  "created_at": "2024-01-15 10:30:00",
  "updated_at": "2024-01-15 10:30:00"
}
```

**Response Error (404)**:
```json
{
  "errors": "Paket not found"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/paket/k3aBc9Xy"
```

---

### 1.3 Create Paket
**Endpoint**: `POST /paket`

**Description**: Membuat paket baru

**Request Body**:
```json
{
  "nama": "Paket Premium",
  "harga": 300000,
  "kecepatan": "100 Mbps"
}
```

**Request Body Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nama | string | Yes | Nama paket |
| harga | integer | Yes | Harga paket |
| kecepatan | string | Yes | Kecepatan paket |

**Response Success (201)**:
```json
{
  "message": "Paket created successfully"
}
```

**Response Error (4xx)**:
```json
{
  "errors": "Error description"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/paket" \
  -H "Content-Type: application/json" \
  -d '{
    "nama": "Paket Premium",
    "harga": 300000,
    "kecepatan": "100 Mbps"
  }'
```

---

### 1.4 Update Paket
**Endpoint**: `PUT /paket/{id}`

**Description**: Mengupdate paket yang sudah ada

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID paket |

**Request Body**:
```json
{
  "nama": "Paket Premium Updated",
  "harga": 350000,
  "kecepatan": "150 Mbps"
}
```

**Request Body Schema**: Same as Create Paket

**Response Success (200)**:
```json
{
  "message": "Paket updated successfully"
}
```

**Response Error (404)**:
```json
{
  "errors": "Paket not found"
}
```

**Example Request**:
```bash
curl -X PUT "http://localhost:3000/paket/k3aBc9Xy" \
  -H "Content-Type: application/json" \
  -d '{
    "nama": "Paket Premium Updated",
    "harga": 350000,
    "kecepatan": "150 Mbps"
  }'
```

---

### 1.5 Delete Paket
**Endpoint**: `DELETE /paket/{id}`

**Description**: Menghapus paket

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID paket |

**Response Success (200)**:
```json
{
  "message": "Paket deleted successfully"
}
```

**Response Error (404)**:
```json
{
  "errors": "Paket not found"
}
```

**Example Request**:
```bash
curl -X DELETE "http://localhost:3000/paket/k3aBc9Xy"
```

---

## 2. Pelanggan (Customer) Endpoints

### 2.1 Get All Pelanggan
**Endpoint**: `GET /pelanggan`

**Description**: Mengambil daftar semua pelanggan dengan pagination

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Nomor halaman |
| size | integer | No | 10 | Jumlah data per halaman |
| sort | string | No | null | Field untuk sorting |
| direction | string | No | null | Arah sorting (ASC/DESC) |
| nama | string | No | null | Filter berdasarkan nama pelanggan |
| paket_id | integer | No | null | Filter berdasarkan ID paket (raw integer, bukan encoded) |

**Response Success (200)**:
```json
{
  "content": [
    {
      "id": "xY9zAb2C",
      "nama": "John Doe",
      "paket": {
        "id": "k3aBc9Xy",
        "nama": "Paket Premium",
        "harga": 300000,
        "kecepatan": "100 Mbps",
        "created_at": "2024-01-15 10:30:00",
        "updated_at": "2024-01-15 10:30:00"
      },
      "created_at": "2024-01-15 11:00:00",
      "updated_at": "2024-01-15 11:00:00"
    }
  ],
  "page": 1,
  "size": 10,
  "total_elements": 1,
  "total_pages": 1,
  "number_of_elements": 1,
  "is_last": true,
  "is_first": true,
  "is_empty": false
}
```

**Response Error (404)**:
```json
{
  "detail": "Data not found"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/pelanggan?page=1&size=10&nama=John"
```

---

### 2.2 Get Pelanggan by ID
**Endpoint**: `GET /pelanggan/{id}`

**Description**: Mengambil detail pelanggan berdasarkan ID

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID pelanggan |

**Response Success (200)**:
```json
{
  "id": "xY9zAb2C",
  "nama": "John Doe",
  "paket": {
    "id": "k3aBc9Xy",
    "nama": "Paket Premium",
    "harga": 300000,
    "kecepatan": "100 Mbps",
    "created_at": "2024-01-15 10:30:00",
    "updated_at": "2024-01-15 10:30:00"
  },
  "created_at": "2024-01-15 11:00:00",
  "updated_at": "2024-01-15 11:00:00"
}
```

**Response Error (404)**:
```json
{
  "detail": "Data not found"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/pelanggan/xY9zAb2C"
```

---

### 2.3 Create Pelanggan
**Endpoint**: `POST /pelanggan`

**Description**: Membuat pelanggan baru

**Request Body**:
```json
{
  "nama": "John Doe",
  "alamat": "Jl. Merdeka No. 123",
  "no_hp": "081234567890",
  "paket_id": 1
}
```

**Request Body Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nama | string | Yes | Nama pelanggan |
| alamat | string | Yes | Alamat pelanggan |
| no_hp | string | Yes | Nomor HP pelanggan |
| paket_id | integer | Yes | ID paket (raw integer, bukan encoded) |

**Response Success (201)**:
```json
{
  "message": "Data created successfully"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/pelanggan" \
  -H "Content-Type: application/json" \
  -d '{
    "nama": "John Doe",
    "alamat": "Jl. Merdeka No. 123",
    "no_hp": "081234567890",
    "paket_id": 1
  }'
```

---

### 2.4 Update Pelanggan
**Endpoint**: `PUT /pelanggan/{id}`

**Description**: Mengupdate pelanggan yang sudah ada

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID pelanggan |

**Request Body**: Same as Create Pelanggan

**Response Success (200)**:
```json
{
  "message": "Data updated successfully"
}
```

**Response Error (404)**:
```json
{
  "detail": "Data not found"
}
```

**Example Request**:
```bash
curl -X PUT "http://localhost:3000/pelanggan/xY9zAb2C" \
  -H "Content-Type: application/json" \
  -d '{
    "nama": "John Doe Updated",
    "alamat": "Jl. Merdeka No. 456",
    "no_hp": "081234567891",
    "paket_id": 2
  }'
```

---

### 2.5 Delete Pelanggan
**Endpoint**: `DELETE /pelanggan/{id}`

**Description**: Menghapus pelanggan

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID pelanggan |

**Response Success (200)**:
```json
{
  "message": "Data deleted successfully"
}
```

**Response Error (404)**:
```json
{
  "detail": "Data not found"
}
```

**Example Request**:
```bash
curl -X DELETE "http://localhost:3000/pelanggan/xY9zAb2C"
```

---

## 3. Tagihan (Billing) Endpoints

### 3.1 Get All Tagihan
**Endpoint**: `GET /tagihan`

**Description**: Mengambil daftar semua tagihan dengan pagination

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Nomor halaman |
| size | integer | No | 10 | Jumlah data per halaman |
| sort | string | No | null | Field untuk sorting |
| direction | string | No | null | Arah sorting (ASC/DESC) |
| tahun | integer | Yes | - | Filter berdasarkan tahun |
| bulan | integer | Yes | - | Filter berdasarkan bulan (1-12) |
| pelanggan_id | integer | No | null | Filter berdasarkan ID pelanggan (raw integer) |
| paket_id | integer | No | null | Filter berdasarkan ID paket (raw integer) |

**Response Success (200)**:
```json
{
  "content": [
    {
      "id": "Ab2Cd3Ef",
      "pelanggan": {
        "id": "xY9zAb2C",
        "nama": "John Doe"
      },
      "paket": {
        "id": "k3aBc9Xy",
        "nama": "Paket Premium",
        "harga": 300000,
        "kecepatan": "100 Mbps"
      },
      "tahun": 2024,
      "bulan": 1,
      "tanggal_bayar": "2024-01-20",
      "created_at": "2024-01-15 12:00:00",
      "updated_at": "2024-01-15 12:00:00"
    }
  ],
  "page": 1,
  "size": 10,
  "total_elements": 1,
  "total_pages": 1,
  "number_of_elements": 1,
  "is_last": true,
  "is_first": true,
  "is_empty": false
}
```

**Response Error (404)**:
```json
{
  "detail": "Page not found"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/tagihan?tahun=2024&bulan=1&page=1&size=10"
```

---

### 3.2 Get Tagihan by ID
**Endpoint**: `GET /tagihan/{id}`

**Description**: Mengambil detail tagihan berdasarkan ID

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID tagihan |

**Response Success (200)**:
```json
{
  "id": "Ab2Cd3Ef",
  "pelanggan": {
    "id": "xY9zAb2C",
    "nama": "John Doe"
  },
  "paket": {
    "id": "k3aBc9Xy",
    "nama": "Paket Premium",
    "harga": 300000,
    "kecepatan": "100 Mbps"
  },
  "tahun": 2024,
  "bulan": 1,
  "tanggal_bayar": "2024-01-20",
  "created_at": "2024-01-15 12:00:00",
  "updated_at": "2024-01-15 12:00:00"
}
```

**Response Error (404)**:
```json
{
  "detail": "Tagihan not found"
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/tagihan/Ab2Cd3Ef"
```

---

### 3.3 Create Tagihan
**Endpoint**: `POST /tagihan`

**Description**: Membuat tagihan baru

**Request Body**:
```json
{
  "pelanggan_id": "xY9zAb2C",
  "paket_id": "k3aBc9Xy",
  "tahun": 2024,
  "bulan": 1,
  "tanggal_bayar": "2024-01-20"
}
```

**Request Body Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pelanggan_id | string | Yes | Encoded ID pelanggan |
| paket_id | string | Yes | Encoded ID paket |
| tahun | integer | Yes | Tahun tagihan |
| bulan | integer | Yes | Bulan tagihan (1-12) |
| tanggal_bayar | string (date) | Yes | Tanggal bayar (format: YYYY-MM-DD) |

**Response Success (200)**:
```json
{
  "message": "saved successfully"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:3000/tagihan" \
  -H "Content-Type: application/json" \
  -d '{
    "pelanggan_id": "xY9zAb2C",
    "paket_id": "k3aBc9Xy",
    "tahun": 2024,
    "bulan": 1,
    "tanggal_bayar": "2024-01-20"
  }'
```

---

### 3.4 Update Tagihan
**Endpoint**: `PUT /tagihan/{id}`

**Description**: Mengupdate tagihan yang sudah ada

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID tagihan |

**Request Body**: Same as Create Tagihan

**Response Success (200)**:
```json
{
  "message": "updated successfully"
}
```

**Example Request**:
```bash
curl -X PUT "http://localhost:3000/tagihan/Ab2Cd3Ef" \
  -H "Content-Type: application/json" \
  -d '{
    "pelanggan_id": "xY9zAb2C",
    "paket_id": "k3aBc9Xy",
    "tahun": 2024,
    "bulan": 2,
    "tanggal_bayar": "2024-02-20"
  }'
```

---

### 3.5 Delete Tagihan
**Endpoint**: `DELETE /tagihan/{id}`

**Description**: Menghapus tagihan

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Encoded ID tagihan |

**Response Success (200)**:
```json
{
  "message": "deleted successfully"
}
```

**Example Request**:
```bash
curl -X DELETE "http://localhost:3000/tagihan/Ab2Cd3Ef"
```

---

### 3.6 Get Tagihan Summary
**Endpoint**: `GET /tagihan/summary/{tahun}`

**Description**: Mengambil summary tagihan per tahun

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tahun | string | Yes | Tahun untuk summary |

**Response Success (200)**:
```json
{
  "summary": [
    {
      "bulan": 1,
      "total_tagihan": 5,
      "total_pendapatan": 1500000
    },
    {
      "bulan": 2,
      "total_tagihan": 7,
      "total_pendapatan": 2100000
    }
  ]
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:3000/tagihan/summary/2024"
```

---

## HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request berhasil |
| 201 | Created - Resource berhasil dibuat |
| 400 | Bad Request - Request tidak valid |
| 401 | Unauthorized - Token tidak valid atau tidak ada |
| 403 | Forbidden - Tidak memiliki permission |
| 404 | Not Found - Resource tidak ditemukan |
| 422 | Validation Error - Data input tidak valid |
| 500 | Internal Server Error - Error di server |

---

## Common Notes

### 1. ID Encoding
- Semua ID yang dikirim dalam **response** menggunakan format **Sqids** (encoded string)
- ID di path parameter (`/{id}`) selalu menggunakan **encoded string**
- Untuk `pelanggan_id` dan `paket_id` di **request body**:
  - **Paket & Pelanggan**: gunakan **integer** (raw ID)
  - **Tagihan**: gunakan **encoded string**

### 2. Date Format
- Input: `YYYY-MM-DD` (contoh: `2024-01-20`)
- Output: `YYYY-MM-DD HH:MM:SS` (contoh: `2024-01-20 15:30:45`)

### 3. Pagination
- Default `page` = 1
- Default `size` = 10
- Sorting dapat digunakan dengan parameter `sort` dan `direction`

### 4. Error Handling
- Error responses memiliki field `detail` atau `errors` yang berisi pesan error
- Periksa HTTP status code untuk mengetahui jenis error

### 5. Authentication
- Gunakan `/auth/login` untuk mendapatkan access token
- Include access token di header: `Authorization: Bearer <token>`
- Access token berlaku 30 menit, refresh token 7 hari
- ADMIN memiliki full access, USER hanya bisa akses tagihan mereka

### 6. Default Credentials
- Username: `admin`
- Password: `newadmin123`
- Role: `ADMIN`

---

## Interactive API Documentation

FastAPI menyediakan dokumentasi interaktif yang dapat diakses di:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

Gunakan dokumentasi interaktif untuk testing endpoint secara langsung.

---

## Contact & Support

Untuk pertanyaan atau bantuan lebih lanjut, hubungi tim backend developer.
