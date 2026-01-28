# Tagihan WiFi - Backend API

A FastAPI-based backend system for managing WiFi billing with customer management, payment tracking, and annual billing matrix views.

## Features

- **Authentication & Authorization**
  - JWT-based authentication with role-based access control (RBAC)
  - Two roles: `admin` (full access) and `user` (read-only access)
  - Secure password hashing with bcrypt
  - 24-hour token expiration

- **Customer Management**
  - Create, read, update, and delete customers (admin only)
  - Track monthly fees per customer
  - Sqids-encoded customer IDs for URL-safe references
  - Soft delete with `is_active` flag

- **Payment Processing**
  - Record individual payments with billing month and year (admin only)
  - Parse manual payment logs (format: `DD-MM-YYYY customer_name`)
  - Prevent duplicate payments for the same month/year via unique constraint
  - Track payment dates and amounts
  - Filter payments by customer, year, or month

- **Billing Matrix**
  - View annual payment status for all customers
  - See all 12 months in one matrix view
  - Track total paid vs expected amount per customer
  - Calculate completion percentage
  - Summary endpoint with overall statistics

- **Database**
  - DuckDB for lightweight but powerful relational storage
  - Persistent storage in `.db` file
  - Automatic schema initialization on startup
  - Optimized indexes for performance

## Tech Stack

- **Framework:** FastAPI 0.128.0+
- **Server:** Uvicorn 0.40.0+
- **Database:** DuckDB 1.0.0+
- **Validation:** Pydantic 2.5.0+ with Pydantic Settings
- **Authentication:** PyJWT 2.8.0+
- **Password Hashing:** bcrypt 4.0.0+
- **ID Encoding:** Sqids 0.4.0+
- **Python:** 3.12+

## Installation

### Prerequisites
- Python 3.12 or higher
- pip or uv (UV package manager recommended)

### Setup

1. **Clone the repository and navigate to project:**
   ```bash
   cd tagihan-wifi
   ```

2. **Install dependencies using UV (recommended):**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```bash
   # Application
   APP_NAME=tagihan-wifi-api
   APP_VERSION=1.0.0
   APP_ENV=development
   APP_DEBUG=False
   APP_HOST=127.0.0.1
   APP_PORT=8000

   # Database
   DATABASE_PATH=./tagihan-wifi.db
   DB_THREADS=4
   DB_MEMORY_LIMIT=2GB
   DB_MAX_MEMORY=4GB

   # Authentication
   SECRET_KEY=your-secret-key-change-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=1440

   # Sqids
   SQIDS_ALPHABET=QnUpaur6msw2E9zF4lMvAhfbtBDS0R1NoVdxXT3qWyOkZjYPig8JK7GCIeLcH5
   ```

   **Important:** Update `SECRET_KEY` with a strong random string for production:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Run the application:**
   ```bash
   # With uvicorn directly
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload

   # Or with uv
   uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

   # Or using Python module
   python main.py
   ```

5. **Access the API:**
   - **API Documentation (Swagger):** http://localhost:8000/docs
   - **Alternative docs (ReDoc):** http://localhost:8000/redoc
   - **Health check:** http://localhost:8000/health
   - **OpenAPI Schema:** http://localhost:8000/openapi.json

## API Endpoints

All API endpoints are prefixed with `/api/v1`.

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "admin",
  "password": "securepassword",
  "role": "admin"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-28T10:30:00"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "securepassword"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-28T10:30:00"
}
```

---

### Customer Management

#### Create Customer (Admin only)
```http
POST /api/v1/customers
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Opi",
  "monthly_fee": 150000
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "sqid": "abc123",
  "name": "Opi",
  "monthly_fee": 150000,
  "created_at": "2026-01-28T10:30:00",
  "updated_at": "2026-01-28T10:30:00"
}
```

#### List All Customers
```http
GET /api/v1/customers
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "sqid": "abc123",
    "name": "Opi",
    "monthly_fee": 150000,
    "created_at": "2026-01-28T10:30:00",
    "updated_at": "2026-01-28T10:30:00"
  }
]
```

#### Get Customer by Sqid
```http
GET /api/v1/customers/{sqid}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "sqid": "abc123",
  "name": "Opi",
  "monthly_fee": 150000,
  "created_at": "2026-01-28T10:30:00",
  "updated_at": "2026-01-28T10:30:00"
}
```

#### Update Customer (Admin only)
```http
PATCH /api/v1/customers/{sqid}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Opi Updated",
  "monthly_fee": 175000
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "sqid": "abc123",
  "name": "Opi Updated",
  "monthly_fee": 175000,
  "created_at": "2026-01-28T10:30:00",
  "updated_at": "2026-01-28T11:00:00"
}
```

#### Delete Customer (Admin only)
```http
DELETE /api/v1/customers/{sqid}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Customer deleted successfully",
  "sqid": "abc123"
}
```

---

### Payment Management

#### Record Payment (Admin only)
```http
POST /api/v1/payments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer_sqid": "abc123",
  "payment_date": "2026-01-15",
  "billing_month": 1,
  "billing_year": 2026,
  "amount": 150000
}
```

**Alternative (using customer_id):**
```json
{
  "customer_id": 1,
  "payment_date": "2026-01-15",
  "billing_month": 1,
  "billing_year": 2026,
  "amount": 150000
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "customer_id": 1,
  "payment_date": "2026-01-15",
  "billing_month": 1,
  "billing_year": 2026,
  "amount": 150000,
  "created_at": "2026-01-28T10:30:00",
  "updated_at": "2026-01-28T10:30:00"
}
```

#### Parse Manual Payment Log (Admin only)
```http
POST /api/v1/payments/parse-log
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "log_entry": "15-01-2026 opi"
}
```

The system will:
1. Parse the date as 15 January 2026
2. Find customer named "opi" (case-insensitive)
3. Record payment with customer's monthly_fee as amount
4. Use payment month/year from the date

**Response (201 Created):**
```json
{
  "id": 1,
  "customer_id": 1,
  "payment_date": "2026-01-15",
  "billing_month": 1,
  "billing_year": 2026,
  "amount": 150000,
  "created_at": "2026-01-28T10:30:00",
  "updated_at": "2026-01-28T10:30:00"
}
```

#### List Payments
```http
GET /api/v1/payments
Authorization: Bearer {access_token}

# Optional filters:
GET /api/v1/payments?customer_sqid=abc123&year=2026&month=1
```

**Query Parameters:**
- `customer_sqid` (optional): Filter by customer sqid
- `customer_id` (optional): Filter by customer ID
- `year` (optional): Filter by billing year
- `month` (optional): Filter by billing month (1-12)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "customer_id": 1,
    "payment_date": "2026-01-15",
    "billing_month": 1,
    "billing_year": 2026,
    "amount": 150000,
    "created_at": "2026-01-28T10:30:00",
    "updated_at": "2026-01-28T10:30:00"
  }
]
```

---

### Billing Matrix

#### Get Annual Billing Matrix
```http
GET /api/v1/billing-matrix/{year}
Authorization: Bearer {access_token}
```

**Example:** `GET /api/v1/billing-matrix/2026`

**Response (200 OK):**
```json
{
  "year": 2026,
  "month_names": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  "rows": [
    {
      "customer_id": 1,
      "customer_sqid": "abc123",
      "customer_name": "Opi",
      "monthly_fee": 150000,
      "payments": [
        {
          "month": 1,
          "month_name": "January",
          "paid": true,
          "amount": 150000,
          "payment_date": "2026-01-15"
        },
        {
          "month": 2,
          "month_name": "February",
          "paid": false,
          "amount": null,
          "payment_date": null
        }
        // ... months 3-12
      ],
      "total_paid": 150000,
      "total_expected": 1800000,
      "completion_percentage": 8.33
    }
  ]
}
```

#### Get Billing Summary
```http
GET /api/v1/billing-matrix/{year}/summary
Authorization: Bearer {access_token}
```

**Example:** `GET /api/v1/billing-matrix/2026/summary`

**Response (200 OK):**
```json
{
  "year": 2026,
  "total_customers": 5,
  "total_expected": 9000000,
  "total_collected": 2250000,
  "pending": 6750000,
  "completion_percentage": 25.0
}
```

---

## Data Models

### Customer
- `id`: Integer (auto-generated)
- `sqid`: String (unique, auto-generated Sqids encoding)
- `name`: String (customer name)
- `monthly_fee`: Integer (monthly payment amount)
- `created_at`: DateTime
- `updated_at`: DateTime

### Payment
- `id`: Integer (auto-generated)
- `customer_id`: Integer (foreign key to Customer)
- `payment_date`: Date
- `billing_month`: Integer (1-12)
- `billing_year`: Integer
- `amount`: Integer (payment amount)
- `created_at`: DateTime
- `updated_at`: DateTime

### User
- `id`: Integer (auto-generated)
- `username`: String (unique)
- `password_hash`: String (bcrypt hash)
- `role`: String (admin | user)
- `is_active`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

---

## Security Considerations

1. **JWT Secret Key**: Change `SECRET_KEY` in `.env` to a strong random value in production
2. **CORS**: Currently allows all origins. Update in `main.py` for production
3. **Password Hashing**: Uses bcrypt with 12 rounds of salt
4. **Role-Based Access Control**: Admin-only endpoints enforce role verification
5. **Input Validation**: All inputs validated with Pydantic
6. **Database**: Use file permissions to protect `.db` file in production

---

## File Structure

```
tagihan-wifi/
├── main.py                          # FastAPI application entry point
├── pyproject.toml                   # Project configuration and dependencies
├── setup.py                         # Setup script
├── .env                             # Environment variables (local, not in git)
├── tagihan-wifi.db                  # DuckDB database file (auto-created)
├── README.md                        # This file
├── FRONTEND_API_GUIDE.md            # Frontend development guide
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py               # Main API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py          # Authentication endpoints
│   │           ├── customers.py     # Customer CRUD endpoints
│   │           ├── payments.py      # Payment management endpoints
│   │           └── billing.py       # Billing matrix endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Application settings
│   │   ├── auth.py                  # JWT and RBAC logic
│   │   └── logging_config.py        # Logging configuration
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py              # DuckDB connection and schema
│   ├── schemas/
│   │   ├── __init__.py              # Pydantic models
│   └── utils/
│       ├── __init__.py
│       ├── sqids_helper.py          # Sqids encoding/decoding
│       └── payment_parser.py        # Payment log parser
└── tests/
    └── (test files)
```

---

## Development Workflow

### Initialize Database
The database and schema are automatically created on first application startup.

### Create Initial Admin User
```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword", "role": "admin"}'

# Using httpie
http POST http://localhost:8000/api/v1/auth/register \
  username=admin password=yourpassword role=admin
```

### Add Sample Data
```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}' \
  | jq -r '.access_token')

# Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Opi", "monthly_fee": 150000}'

# Record payment
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_sqid": "abc123", "payment_date": "2026-01-15", "billing_month": 1, "billing_year": 2026, "amount": 150000}'
```

---

## Troubleshooting

### Database Lock Issues
If you encounter database lock errors, ensure only one instance is accessing the database at a time. DuckDB does not support concurrent writes.

### Authentication Errors
- Check that token is provided in `Authorization: Bearer {token}` format
- Verify token hasn't expired (24-hour expiry by default)
- Ensure username/password are correct
- Check that the user is active (`is_active = true`)

### Payment Duplicate Errors (409 Conflict)
Payments are unique per (customer_id, billing_month, billing_year). If you need to update a payment, contact the administrator.

### CORS Errors
If frontend requests are blocked, update `CORS_ORIGINS` in [config.py](app/core/config.py) or add allowed origins to `.env`:
```bash
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

### Port Already in Use
If port 8000 is already in use:
```bash
# Use a different port
uvicorn main:app --host 127.0.0.1 --port 8080

# Or set in .env
APP_PORT=8080
```

---

## Frontend Development

For detailed frontend integration guide, see [FRONTEND_API_GUIDE.md](FRONTEND_API_GUIDE.md).

**Quick Reference:**
- **Base URL:** `http://localhost:8000/api/v1`
- **Auth:** JWT Bearer token in `Authorization` header
- **Date Format:** ISO 8601 (`YYYY-MM-DD`)
- **Datetime Format:** ISO 8601 with timezone
- **Customer ID:** Use `sqid` (string) for URLs, `id` (int) for internal references

---

## Future Enhancements

- [ ] Payment update/edit endpoints (PUT/PATCH)
- [ ] Payment deletion with audit trail
- [ ] Batch payment import (CSV/Excel)
- [ ] Email notifications for payment reminders
- [ ] SMS notifications integration
- [ ] Advanced filtering and search
- [ ] Data export (PDF, Excel, CSV)
- [ ] Dashboard/statistics endpoints
- [ ] Audit logging for all operations
- [ ] Webhooks for payment events
- [ ] Multi-tenancy support
- [ ] Payment history and analytics

---

## API Documentation

For interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Security Considerations

1. **JWT Secret Key**: Always change `SECRET_KEY` in `.env` to a strong random value in production
2. **CORS**: Currently allows all origins (`*`). Update in [config.py](app/core/config.py) for production
3. **Password Hashing**: Uses bcrypt with automatic salt rounds
4. **Role-Based Access Control**: Admin-only endpoints enforce role verification via dependency injection
5. **Input Validation**: All inputs validated with Pydantic models
6. **Database**: Use file permissions to protect `.db` file in production (chmod 600)
7. **HTTPS**: Always use HTTPS in production (configure reverse proxy like nginx)
8. **Rate Limiting**: Consider adding rate limiting for production (e.g., slowapi)

---

## License

Proprietary - All rights reserved

---

## Support

For issues or questions:
- Check the [FRONTEND_API_GUIDE.md](FRONTEND_API_GUIDE.md) for frontend integration
- Review API documentation at http://localhost:8000/docs
- Contact the development team

---

## Version History

### v1.0.0 (2026-01-28)
- Initial release
- Authentication with JWT
- Customer management
- Payment tracking
- Billing matrix view
- DuckDB integration
