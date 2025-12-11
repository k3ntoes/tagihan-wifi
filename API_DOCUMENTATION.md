# API Documentation - Tagihan WiFi

## Base Information

- **Base URL**: `http://localhost:3000` (atau sesuai konfigurasi `app_host` dan `app_port`)
- **Content-Type**: `application/json`
- **Framework**: FastAPI
- **Database**: DuckDB

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

## 1. Paket (Package) Endpoints

### 1.1 Get All Paket
**Endpoint**: `GET /paket`

**Description**: Mengambil daftar semua paket dengan pagination

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
curl -X GET "http://localhost:3000/paket?page=1&size=10&nama=Premium"
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

---

## Interactive API Documentation

FastAPI menyediakan dokumentasi interaktif yang dapat diakses di:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

Gunakan dokumentasi interaktif untuk testing endpoint secara langsung.

---

## Contact & Support

Untuk pertanyaan atau bantuan lebih lanjut, hubungi tim backend developer.
