# Tagihan WiFi API Documentation

Dokumentasi lengkap untuk API Backend Tagihan WiFi. Panduan ini dimaksudkan untuk membantu Frontend Developer dalam membangun interface dengan NextJS.

**Base URL:** `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Endpoints](#endpoints)
   - [Auth](#auth-endpoints)
   - [Packages](#package-endpoints)
   - [Customers](#customer-endpoints)
   - [Payments](#payment-endpoints)
   - [Billing Matrix](#billing-matrix-endpoints)
4. [Error Handling](#error-handling)
5. [Pagination](#pagination)
6. [NextJS Integration Examples](#nextjs-integration-examples)

---

## Authentication

### Login

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "bearer",
  "expiresIn": 3600
}
```

**Note:** Response uses camelCase format (e.g., `accessToken`, `tokenType`, `expiresIn`)

**Usage in NextJS:**
```typescript
const loginUser = async (username: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};
```

### Get Current User

**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** User `id` is an integer (not sqid). Response uses camelCase format.

### Register User (Admin Only)

**Endpoint:** `POST /auth/register`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "user"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 2,
    "username": "newuser",
    "role": "user",
    "isActive": true,
    "createdAt": "2026-02-05T10:30:00"
  }
}
```

**Note:** Response uses camelCase format.

---

## Response Format

### Important: Request vs Response Format

- **Request bodies and query parameters** use snake_case (e.g., `customer_id`, `payment_date`, `per_page`)
- **Response bodies** use camelCase (e.g., `customerId`, `paymentDate`, `perPage`, `isActive`)

This convention applies to all endpoints unless otherwise noted.

### Single Resource Response

Single resource responses (create, get single) are wrapped in a `data` object:

```json
{
  "data": {
    "id": "pkg_abc123xyz",
    "name": "Paket Premium",
    "speed": 100,
    "price": 250000,
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** All fields use camelCase format in responses. The `id` field is generated as sqid on-the-fly from internal database ID.

### Paginated Response

List responses (GET with pagination) return a paginated structure:

```json
{
  "data": [
    {
      "id": "pkg_abc123xyz",
      "name": "Paket Premium",
      ...
    }
  ],
  "meta": {
    "total": 10,
    "page": 1,
    "perPage": 10,
    "totalPages": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Note:** All fields use camelCase format. Request parameters use snake_case (e.g., `per_page`), but response uses camelCase (e.g., `perPage`).

### IDs Format (SQID)

All resource IDs use Laravel-style SQID format with prefixes:
- **Packages:** `pkg_abc123xyz`
- **Customers:** `cust_abc123xyz`
- **Payments:** `pay_abc123xyz`

These IDs are generated on-the-fly from internal database IDs and should be used in all API calls.

---

## Endpoints

### Auth Endpoints

#### POST /auth/login
Login and get JWT token.
- **Status:** 200
- **Error:** 401 (Invalid credentials)

#### GET /auth/me
Get current user information.
- **Status:** 200
- **Headers:** `Authorization: Bearer <token>`
- **Error:** 401 (Unauthorized)

#### POST /auth/change-password
Change current user password.
- **Status:** 200
- **Headers:** `Authorization: Bearer <token>`
- **Error:** 400 (Old password incorrect), 401 (Unauthorized), 404 (User not found)

#### GET /auth/users
List all users (admin only).
- **Status:** 200
- **Headers:** `Authorization: Bearer <admin_token>`
- **Requires:** `role: "admin"`
- **Error:** 401 (Unauthorized), 403 (Forbidden)

#### GET /auth/users/{user_id}
Get specific user (admin only).
- **Status:** 200
- **Headers:** `Authorization: Bearer <admin_token>`
- **Requires:** `role: "admin"`
- **Error:** 401 (Unauthorized), 403 (Forbidden), 404 (Not found)

#### PATCH /auth/users/{user_id}
Update user (admin only).
- **Status:** 200
- **Headers:** `Authorization: Bearer <admin_token>`
- **Requires:** `role: "admin"`
- **Error:** 400 (Invalid input), 401 (Unauthorized), 403 (Forbidden), 404 (Not found)

#### DELETE /auth/users/{user_id}
Delete user (admin only).
- **Status:** 204
- **Headers:** `Authorization: Bearer <admin_token>`
- **Requires:** `role: "admin"`
- **Error:** 400 (Cannot delete own account), 401 (Unauthorized), 403 (Forbidden), 404 (Not found)

#### POST /auth/register
Register new user (admin only).
- **Status:** 201
- **Headers:** `Authorization: Bearer <admin_token>`
- **Requires:** `role: "admin"`
- **Error:** 400 (Invalid input), 403 (Forbidden), 409 (Username already exists)

---

## Detailed Auth Endpoints Documentation

### POST /auth/change-password
Change current user password.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00"
  }
}
```

**Errors:**
- 400: Old password is incorrect
- 401: Unauthorized
- 404: User not found

---

### GET /auth/users
List all users (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
```
page=1                   # Page number (default: 1)
per_page=10              # Items per page (default: 10, max: 100)
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "isActive": true,
      "createdAt": "2026-02-05T10:00:00"
    },
    {
      "id": 2,
      "username": "user1",
      "role": "user",
      "isActive": true,
      "createdAt": "2026-02-05T10:30:00"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "perPage": 10,
    "totalPages": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not admin)

---

### GET /auth/users/{user_id}
Get specific user (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**URL Parameters:**
- `user_id`: User ID (integer)

**Response (200 OK):**
```json
{
  "data": {
    "id": 2,
    "username": "user1",
    "role": "user",
    "isActive": true,
    "createdAt": "2026-02-05T10:30:00"
  }
}
```

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not admin)
- 404: User not found

---

### PATCH /auth/users/{user_id}
Update user (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**URL Parameters:**
- `user_id`: User ID (integer)

**Request (all fields optional):**
```json
{
  "username": "updated_user",
  "password": "newpass123",
  "role": "admin",
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": 2,
    "username": "updated_user",
    "role": "admin",
    "isActive": false,
    "createdAt": "2026-02-05T10:30:00"
  }
}
```

**Errors:**
- 400: Username already exists or invalid input
- 401: Unauthorized
- 403: Forbidden (not admin)
- 404: User not found

---

### DELETE /auth/users/{user_id}
Delete user (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**URL Parameters:**
- `user_id`: User ID (integer)

**Response (204 No Content)**

**Errors:**
- 400: Cannot delete your own account
- 401: Unauthorized
- 403: Forbidden (not admin)
- 404: User not found

---

### Package Endpoints

#### POST /packages
Create new package (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Paket 100 Mbps",
  "speed": 100,
  "price": 250000
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "pkg_abc123xyz",
    "name": "Paket 100 Mbps",
    "speed": 100,
    "price": 250000,
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Response uses camelCase format.

**Errors:**
- 400: Package name already exists
- 401: Unauthorized
- 403: Forbidden (not admin)

---

#### GET /packages
List all packages with filters and pagination.

**Query Parameters:**
```
page=1                    # Page number (default: 1)
per_page=10               # Items per page (default: 10, max: 100)
name=premium              # Filter by name (partial match)
minSpeed=50               # Filter by minimum speed (Mbps)
maxSpeed=100              # Filter by maximum speed (Mbps)
minPrice=100000           # Filter by minimum price
maxPrice=300000           # Filter by maximum price
includeInactive=false     # Include inactive packages (default: false)
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "pkg_abc123xyz",
      "name": "Paket 100 Mbps",
      "speed": 100,
      "price": 250000,
      "isActive": true,
      "createdAt": "2026-02-05T10:00:00",
      "updatedAt": "2026-02-05T10:00:00"
    }
  ],
  "meta": {
    "total": 3,
    "page": 1,
    "perPage": 10,
    "totalPages": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Note:** Request uses snake_case parameters (e.g., `per_page`, `min_speed`), but response uses camelCase (e.g., `perPage`, `isActive`).

---

#### GET /packages/{id}
Get specific package by ID.

**URL Parameters:**
- `id`: Package SQID (e.g., `pkg_abc123xyz`)

**Response (200 OK):**
```json
{
  "data": {
    "id": "pkg_abc123xyz",
    "name": "Paket 100 Mbps",
    "speed": 100,
    "price": 250000,
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Response uses camelCase format.

**Errors:**
- 400: Invalid package ID format
- 404: Package not found

---

#### PUT /packages/{id}
Update package (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request (all fields optional):**
```json
{
  "name": "Paket 100 Mbps Updated",
  "speed": 110,
  "price": 260000
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "pkg_abc123xyz",
    "name": "Paket 100 Mbps Updated",
    "speed": 110,
    "price": 260000,
    "isActive": true,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T11:00:00"
  }
}
```

**Note:** Response uses camelCase format.

**Errors:**
- 400: Invalid input or package name already exists
- 403: Forbidden
- 404: Package not found

---

#### DELETE /packages/{id}
Delete package (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (204 No Content)**

**Errors:**
- 400: Invalid package ID
- 403: Forbidden
- 404: Package not found

---

### Customer Endpoints

#### POST /customers
Create new customer (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request:**
```json
{
  "name": "PT Mitra Bisnis",
  "package_id": "pkg_abc123xyz",
  "monthly_fee": 250000
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "cust_xyz789abc",
    "name": "PT Mitra Bisnis",
    "package": {
      "id": "pkg_abc123xyz",
      "name": "Paket 100 Mbps"
    },
    "monthlyFee": 250000,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Request uses snake_case (e.g., `package_id`, `monthly_fee`), but response uses camelCase (e.g., `monthlyFee`).

**Errors:**
- 400: Invalid package ID or input
- 401: Unauthorized
- 403: Forbidden

---

#### GET /customers
List all customers with filters and pagination.

**Query Parameters:**
```
page=1                   # Page number (default: 1)
per_page=10              # Items per page (default: 10, max: 100)
name=mitra               # Filter by customer name (partial match)
package_id=pkg_abc123xyz # Filter by package ID
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "cust_xyz789abc",
      "name": "PT Mitra Bisnis",
      "package": {
        "id": "pkg_abc123xyz",
        "name": "Paket 100 Mbps"
      },
      "monthlyFee": 250000,
      "createdAt": "2026-02-05T10:00:00",
      "updatedAt": "2026-02-05T10:00:00"
    }
  ],
  "meta": {
    "total": 5,
    "page": 1,
    "perPage": 10,
    "totalPages": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Note:** Request uses snake_case parameters (e.g., `per_page`, `package_id`), but response uses camelCase.

---

#### GET /customers/{id}
Get specific customer by ID.

**URL Parameters:**
- `id`: Customer SQID (e.g., `cust_xyz789abc`)

**Response (200 OK):**
```json
{
  "data": {
    "id": "cust_xyz789abc",
    "name": "PT Mitra Bisnis",
    "package": {
      "id": "pkg_abc123xyz",
      "name": "Paket 100 Mbps"
    },
    "monthlyFee": 250000,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Response uses camelCase format.

---

#### PATCH /customers/{id}
Update customer (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request (all fields optional):**
```json
{
  "name": "PT Mitra Bisnis Baru",
  "package_id": "pkg_def456ghi",
  "monthly_fee": 300000
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "cust_xyz789abc",
    "name": "PT Mitra Bisnis Baru",
    "package": {
      "id": "pkg_def456ghi",
      "name": "Paket Premium"
    },
    "monthlyFee": 300000,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T11:00:00"
  }
}
```

**Note:** Request uses snake_case (e.g., `package_id`, `monthly_fee`), but response uses camelCase.

---

#### DELETE /customers/{id}
Delete customer (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (204 No Content)**

---

### Payment Endpoints

#### POST /payments
Record new payment (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request:**
```json
{
  "customer_id": "cust_xyz789abc",
  "payment_date": "2026-02-05",
  "billing_month": 2,
  "billing_year": 2026,
  "amount": 250000
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "pay_abc123xyz",
    "customer": {
      "id": "cust_xyz789abc",
      "name": "PT Mitra Bisnis",
      "monthlyFee": 250000,
      "package": {
        "id": "pkg_abc123xyz",
        "name": "Paket 100 Mbps"
      }
    },
    "paymentDate": "2026-02-05",
    "billingMonth": 2,
    "billingYear": 2026,
    "amount": 250000,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Request uses snake_case (e.g., `customer_id`, `payment_date`), but response uses camelCase (e.g., `paymentDate`, `billingMonth`).

**Errors:**
- 400: Invalid customer ID or input
- 409: Payment already exists for this customer/month/year
- 401: Unauthorized
- 403: Forbidden

---

#### GET /payments
List all payments with filters and pagination.

**Query Parameters:**
```
page=1                   # Page number (default: 1)
per_page=10              # Items per page (default: 10, max: 100)
customer_id=cust_xyz789abc # Filter by customer ID
year=2026                # Filter by billing year
month=2                  # Filter by billing month
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "pay_abc123xyz",
      "customer": {
        "id": "cust_xyz789abc",
        "name": "PT Mitra Bisnis",
        "monthlyFee": 250000,
        "package": {
          "id": "pkg_abc123xyz",
          "name": "Paket 100 Mbps"
        }
      },
      "paymentDate": "2026-02-05",
      "billingMonth": 2,
      "billingYear": 2026,
      "amount": 250000,
      "createdAt": "2026-02-05T10:00:00",
      "updatedAt": "2026-02-05T10:00:00"
    }
  ],
  "meta": {
    "total": 15,
    "page": 1,
    "perPage": 10,
    "totalPages": 2,
    "hasNext": true,
    "hasPrev": false
  }
}
```

**Note:** Request uses snake_case parameters (e.g., `per_page`, `customer_id`), but response uses camelCase.

---

#### POST /payments/parse-log
Parse manual payment log entry and record payment (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request:**
```json
{
  "log_entry": "05-02-2026 PT Mitra Bisnis"
}
```

Format: `DD-MM-YYYY customer_name`

**Response (201 Created):**
```json
{
  "data": {
    "id": "pay_abc123xyz",
    "customer": {
      "id": "cust_xyz789abc",
      "name": "PT Mitra Bisnis",
      "monthlyFee": 250000,
      "package": {
        "id": "pkg_abc123xyz",
        "name": "Paket 100 Mbps"
      }
    },
    "paymentDate": "2026-02-05",
    "billingMonth": 2,
    "billingYear": 2026,
    "amount": 250000,
    "createdAt": "2026-02-05T10:00:00",
    "updatedAt": "2026-02-05T10:00:00"
  }
}
```

**Note:** Response uses camelCase format.

**Errors:**
- 400: Invalid format or customer not found
- 409: Payment already exists
- 401: Unauthorized
- 403: Forbidden

---

### Billing Matrix Endpoints

#### GET /billing-matrix/{year}
Get annual billing matrix for all customers (paginated).

**URL Parameters:**
- `year`: Billing year (e.g., 2026)

**Query Parameters:**
```
page=1                      # Page number (default: 1)
per_page=10                 # Items per page (default: 10, max: 100)
customer_id=cust_xyz789abc  # Filter by specific customer
customer_name=mitra         # Filter by customer name (partial match)
```

**Response (200 OK):**
```json
{
  "year": 2026,
  "monthNames": [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ],
  "data": [
    {
      "customer": {
        "id": "cust_xyz789abc",
        "name": "PT Mitra Bisnis",
        "monthlyFee": 250000,
        "package": {
          "id": "pkg_abc123xyz",
          "name": "Paket 100 Mbps"
        }
      },
      "payments": [
        {
          "month": 1,
          "monthName": "January",
          "paid": true,
          "amount": 250000,
          "paymentDate": "2026-01-15"
        },
        {
          "month": 2,
          "monthName": "February",
          "paid": true,
          "amount": 250000,
          "paymentDate": "2026-02-05"
        },
        {
          "month": 3,
          "monthName": "March",
          "paid": false,
          "amount": null,
          "paymentDate": null
        }
      ],
      "totalPaid": 500000,
      "totalExpected": 750000,
      "completionPercentage": 66.67
    }
  ],
  "meta": {
    "total": 5,
    "page": 1,
    "perPage": 10,
    "totalPages": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

**Note:** Request uses snake_case parameters (e.g., `per_page`, `customer_id`, `customer_name`), but response uses camelCase (e.g., `monthNames`, `totalPaid`, `totalExpected`, `completionPercentage`, `paymentDate`).

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Delete successful |
| 400 | Bad Request | Invalid input, malformed request |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate entry (e.g., payment already exists) |
| 500 | Server Error | Internal server error |

### Example Error Response

```json
{
  "detail": "Invalid customer ID: cust_invalid"
}
```

---

## Pagination

All list endpoints support pagination with the following parameters:

```
page=1              # Page number (1-indexed, default: 1)
per_page=10         # Items per page (default: 10, max: 100)
```

The response includes metadata with camelCase field names:

```json
{
  "meta": {
    "total": 100,           # Total number of items
    "page": 1,              # Current page
    "perPage": 10,          # Items per page
    "totalPages": 10,       # Total number of pages
    "hasNext": true,        # Is there a next page?
    "hasPrev": false        # Is there a previous page?
  }
}
```

**Example: Get page 2 with 20 items per page**
```
GET /packages?page=2&per_page=20
```

**Note:** Request parameters use snake_case (e.g., `per_page`), but response metadata uses camelCase (e.g., `perPage`, `hasNext`, `hasPrev`).

---

## NextJS Integration Examples

### 1. Setup API Client with Axios

**lib/api-client.ts:**
```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Authentication Hook

**hooks/useAuth.ts:**
```typescript
import { useState } from 'react';
import apiClient from '@/lib/api-client';

interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  isActive: boolean;
  createdAt: string;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      });
      localStorage.setItem('token', response.data.access_token);
      await getMe();
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getMe = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data.data);
    } catch (err) {
      setUser(null);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return { user, loading, error, login, logout, getMe };
};
```

### 3. User Management (Admin Only)

**pages/admin/users.tsx:**
```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  isActive: boolean;
  createdAt: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, [page]);

  const fetchUsers = async () => {
    try {
      const response = await apiClient.get('/auth/users', {
        params: { page, per_page: 10 },
      });
      setUsers(response.data.data);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Delete this user?')) return;
    try {
      await apiClient.delete(`/auth/users/${userId}`);
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>User Management</h1>
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.role}</td>
              <td>{user.isActive ? 'Active' : 'Inactive'}</td>
              <td>
                <button onClick={() => handleDeleteUser(user.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 4. Change Password

**pages/auth/change-password.tsx:**
```typescript
import { useState } from 'react';
import apiClient from '@/lib/api-client';

export default function ChangePasswordPage() {
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.post('/auth/change-password', {
        old_password: formData.old_password,
        new_password: formData.new_password,
      });
      setSuccess(true);
      setFormData({ old_password: '', new_password: '' });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Change Password</h1>
      {success && <div style={{ color: 'green' }}>Password changed successfully!</div>}

      <form onSubmit={handleSubmit}>
        <div>
          <label>Old Password:</label>
          <input
            type="password"
            value={formData.old_password}
            onChange={(e) =>
              setFormData({ ...formData, old_password: e.target.value })
            }
            required
          />
        </div>

        <div>
          <label>New Password:</label>
          <input
            type="password"
            value={formData.new_password}
            onChange={(e) =>
              setFormData({ ...formData, new_password: e.target.value })
            }
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Changing...' : 'Change Password'}
        </button>
      </form>
    </div>
  );
}
```

### 5. Fetch Packages

**pages/packages.tsx:**
```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface Package {
  id: string;
  name: string;
  speed: number;
  price: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export default function PackagesPage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPackages();
  }, [page]);

  const fetchPackages = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/packages', {
        params: { page, per_page: 10 },
      });
      setPackages(response.data.data);
      setMeta(response.data.meta);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch packages');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Packages</h1>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Speed (Mbps)</th>
            <th>Price (Rp)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {packages.map((pkg) => (
            <tr key={pkg.id}>
              <td>{pkg.name}</td>
              <td>{pkg.speed}</td>
              <td>{pkg.price.toLocaleString('id-ID')}</td>
              <td>{pkg.is_active ? 'Active' : 'Inactive'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      {meta && (
        <div>
          <button
            onClick={() => setPage(page - 1)}
            disabled={!meta.has_prev}
          >
            Previous
          </button>
          <span>
            Page {meta.page} of {meta.total_pages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={!meta.has_next}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
```

### 6. Create Customer

**pages/customers/create.tsx:**
```typescript
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import apiClient from '@/lib/api-client';

interface Package {
  id: string;
  name: string;
}

export default function CreateCustomerPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    package_id: '',
    monthly_fee: '',
  });
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const response = await apiClient.get('/packages', {
        params: { per_page: 100 },
      });
      setPackages(response.data.data);
    } catch (err) {
      console.error('Failed to fetch packages:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiClient.post('/customers', {
        name: formData.name,
        package_id: formData.package_id || null,
        monthly_fee: parseInt(formData.monthly_fee),
      });
      router.push('/customers');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Create Customer</h1>
      {error && <div style={{ color: 'red' }}>{error}</div>}

      <form onSubmit={handleSubmit}>
        <div>
          <label>Name:</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
            required
          />
        </div>

        <div>
          <label>Package:</label>
          <select
            value={formData.package_id}
            onChange={(e) =>
              setFormData({ ...formData, package_id: e.target.value })
            }
          >
            <option value="">-- Select Package --</option>
            {packages.map((pkg) => (
              <option key={pkg.id} value={pkg.id}>
                {pkg.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Monthly Fee (Rp):</label>
          <input
            type="number"
            value={formData.monthly_fee}
            onChange={(e) =>
              setFormData({ ...formData, monthly_fee: e.target.value })
            }
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create'}
        </button>
      </form>
    </div>
  );
}
```

### 7. Billing Matrix View

**pages/billing/matrix.tsx:**
```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface PaymentByMonth {
  month: number;
  monthName: string;
  paid: boolean;
  amount: number | null;
  paymentDate: string | null;
}

interface CustomerInfo {
  id: string;
  name: string;
  monthlyFee: number;
  package: {
    id: string;
    name: string;
  } | null;
}

interface BillingRow {
  customer: CustomerInfo;
  payments: PaymentByMonth[];
  totalPaid: number;
  totalExpected: number;
  completionPercentage: number;
}

export default function BillingMatrixPage() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [rows, setRows] = useState<BillingRow[]>([]);
  const [monthNames, setMonthNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMatrix();
  }, [year]);

  const fetchMatrix = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/billing-matrix/${year}`, {
        params: { per_page: 100 },
      });
      setRows(response.data.data);
      setMonthNames(response.data.monthNames);
    } catch (err) {
      console.error('Failed to fetch billing matrix:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Billing Matrix {year}</h1>

      <div>
        <button onClick={() => setYear(year - 1)}>← Previous Year</button>
        <button onClick={() => setYear(year + 1)}>Next Year →</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Customer Name</th>
            <th>Monthly Fee</th>
            {monthNames.map((month, idx) => (
              <th key={idx}>{month.substring(0, 3)}</th>
            ))}
            <th>Total Paid</th>
            <th>Progress</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.customer.id}>
              <td>{row.customer.name}</td>
              <td>Rp {row.customer.monthlyFee.toLocaleString('id-ID')}</td>
              {row.payments.map((payment) => (
                <td
                  key={payment.month}
                  style={{
                    backgroundColor: payment.paid ? '#d4edda' : '#f8d7da',
                  }}
                >
                  {payment.paid ? '✓' : '✗'}
                </td>
              ))}
              <td>Rp {row.totalPaid.toLocaleString('id-ID')}</td>
              <td>
                <div style={{ width: '100px', backgroundColor: '#eee' }}>
                  <div
                    style={{
                      width: `${row.completionPercentage}%`,
                      backgroundColor: '#28a745',
                      height: '20px',
                    }}
                  />
                </div>
                {row.completionPercentage.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Environment Variables

Create `.env.local` in your NextJS project:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Important Notes for Frontend Developers

### Request vs Response Format

**This is critical for frontend integration:**

- **Request bodies and query parameters**: Use **snake_case**
  - Example: `customer_id`, `payment_date`, `per_page`, `monthly_fee`, `package_id`

- **Response bodies**: Use **camelCase**
  - Example: `customerId`, `paymentDate`, `perPage`, `monthlyFee`, `packageId`, `isActive`, `createdAt`

### Examples

**Request (send snake_case):**
```typescript
// Create customer
await apiClient.post('/customers', {
  name: 'PT Mitra Bisnis',
  package_id: 'pkg_abc123xyz',  // snake_case
  monthly_fee: 250000            // snake_case
});

// List with pagination
await apiClient.get('/packages', {
  params: {
    page: 1,
    per_page: 10,      // snake_case
    min_speed: 50,     // snake_case
    max_price: 300000  // snake_case
  }
});
```

**Response (receive camelCase):**
```json
{
  "data": {
    "id": "cust_xyz789abc",
    "monthlyFee": 250000,      // camelCase
    "packageId": "pkg_abc123xyz", // camelCase (if present)
    "createdAt": "2026-02-05T10:00:00",  // camelCase
    "updatedAt": "2026-02-05T10:00:00"   // camelCase
  },
  "meta": {
    "perPage": 10,      // camelCase
    "totalPages": 1,    // camelCase
    "hasNext": false,   // camelCase
    "hasPrev": false    // camelCase
  }
}
```

### Other Important Notes

1. **Token Storage:** Store JWT token in `localStorage`. Ensure it's cleared on logout.

2. **CORS:** Make sure the API server allows requests from your frontend domain.

3. **Nested Response Data:** All single resource responses wrap data in a `data` object. Paginated responses have a `data` array. Always access data through these keys.

4. **SQID Format:** Resource IDs use SQID format with prefixes:
   - Packages: `pkg_abc123xyz`
   - Customers: `cust_xyz789abc`
   - Payments: `pay_abc123xyz`
   - Use them as provided in API responses.

5. **Dates:** API returns dates in ISO 8601 format. Use `new Date()` to parse them in JavaScript.

6. **Error Handling:** Always check `response.data.detail` for error messages.

7. **Authentication:** Include `Authorization: Bearer <token>` header for all protected endpoints.

8. **Pagination:** Always check `hasNext` and `hasPrev` before navigating pages.

---

## Support & Questions

For issues or questions about the API, please check:
1. The error message in response
2. HTTP status code
3. Verify your token is valid and not expired
4. Check query parameters and request body format
5. **Verify request format:** Are you using snake_case in requests?
6. **Verify response parsing:** Are you accessing camelCase fields in responses?

**Last Updated:** February 14, 2026
