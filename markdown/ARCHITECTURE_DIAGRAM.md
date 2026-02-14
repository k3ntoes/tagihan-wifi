# Architecture Diagram

## Layered Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP Request                             │
│                    (FastAPI Routing)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTROLLER LAYER                              │
│                  (app/api/v1/endpoints/)                         │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐        │
│  │customers │  │packages  │  │payments  │  │ billing │        │
│  │   .py    │  │   .py    │  │   .py    │  │   .py   │        │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘        │
│                                                                   │
│  Responsibilities:                                                │
│  • HTTP request/response handling                                │
│  • Input validation (Pydantic)                                   │
│  • Authentication/Authorization                                  │
│  • Delegate to Service Layer                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
│                    (app/services/)                               │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Customer   │  │  Package   │  │  Payment   │  │ Billing  │ │
│  │  Service   │  │  Service   │  │  Service   │  │ Service  │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
│                                                                   │
│  Responsibilities:                                                │
│  • Business logic & validation                                   │
│  • Coordinate multiple repositories                              │
│  • Transaction management                                        │
│  • Data transformation (DB → Response Model)                     │
│  • SQID encoding/decoding                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                               │
│                   (app/repositories/)                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Customer   │  │   Package    │  │   Payment    │         │
│  │  Repository  │  │  Repository  │  │  Repository  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────────────────────────────┐   │
│  │   Billing    │  │     BaseRepository                    │   │
│  │  Repository  │  │  (Common DB operations)               │   │
│  └──────────────┘  └──────────────────────────────────────┘   │
│                                                                   │
│  Responsibilities:                                                │
│  • Database queries (CRUD)                                       │
│  • Return raw data (tuples)                                      │
│  • No business logic                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE                                   │
│                    (SQLite / duckdb)                             │
│                                                                   │
│  Tables: users, customers, packages, payments                    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Create Customer

```
1. HTTP POST /api/v1/customers
   ↓
   {
     "name": "John Doe",
     "package_id": "pkg_abc123",
     "monthly_fee": 50000
   }

2. CONTROLLER (customers.py)
   ┌─────────────────────────────────────────┐
   │ @router.post("")                        │
   │ async def create_customer():            │
   │   service = CustomerService(db)         │
   │   customer = service.create_customer()  │ ◄── Thin: Just delegates
   │   return SingleCustomerResponse(...)    │
   └──────────────┬──────────────────────────┘
                  │
                  ▼
3. SERVICE (customer_service.py)
   ┌─────────────────────────────────────────┐
   │ class CustomerService:                   │
   │   def create_customer(self, data):       │
   │     # 1. Decode package_id sqid          │
   │     actual_id = decode(data.package_id)  │
   │                                           │
   │     # 2. Business validation             │ ◄── Business Logic
   │     if not package_exists(actual_id):    │
   │       raise HTTPException(...)           │
   │                                           │
   │     # 3. Call repository                 │
   │     row = self.customer_repo.create(...) │
   │     self.db.commit()                     │
   │                                           │
   │     # 4. Transform to response           │
   │     return self._build_response(row)     │
   └──────────────┬──────────────────────────┘
                  │
                  ▼
4. REPOSITORY (customer_repository.py)
   ┌─────────────────────────────────────────┐
   │ class CustomerRepository:                │
   │   def create(self, name, pkg_id, fee):   │
   │     query = """                           │
   │       INSERT INTO customers              │ ◄── Pure SQL
   │       (name, package_id, monthly_fee)    │
   │       VALUES (?, ?, ?)                   │
   │       RETURNING *                        │
   │     """                                   │
   │     result = execute_insert(query, [...])│
   │     return result[0]  # Raw tuple        │
   └──────────────┬──────────────────────────┘
                  │
                  ▼
5. DATABASE
   ┌─────────────────────────────────────────┐
   │ INSERT INTO customers                    │
   │ VALUES (1, 'John Doe', 1, 50000)         │
   │                                           │
   │ RETURNING 1, 'John Doe', 1, 50000, ...   │ ◄── Raw data
   └──────────────┬──────────────────────────┘
                  │
                  ▼ (Return path)
6. SERVICE transforms raw data
   ┌─────────────────────────────────────────┐
   │ row = (1, 'John Doe', 1, 50000, ...)     │
   │                                           │
   │ return CustomerResponse(                 │
   │   id='cust_xyz789',  # Encoded SQID      │ ◄── Transformation
   │   name='John Doe',                       │
   │   package=PackageInfo(...),              │
   │   monthly_fee=50000,                     │
   │   ...                                     │
   │ )                                         │
   └──────────────┬──────────────────────────┘
                  │
                  ▼
7. CONTROLLER returns HTTP response
   ┌─────────────────────────────────────────┐
   │ HTTP 201 Created                         │
   │ {                                         │
   │   "data": {                               │
   │     "id": "cust_xyz789",                  │ ◄── Clean Response
   │     "name": "John Doe",                   │
   │     "package": {...},                     │
   │     "monthly_fee": 50000                  │
   │   }                                        │
   │ }                                          │
   └───────────────────────────────────────────┘
```

## Component Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                        IMPORTS                                │
└──────────────────────────────────────────────────────────────┘

Controller (customers.py)
  ↓
  ├─ Import: FastAPI (APIRouter, Depends, status)
  ├─ Import: Database (get_db)
  ├─ Import: Auth (require_role, get_current_user)
  ├─ Import: Schemas (CustomerCreate, CustomerResponse, ...)
  └─ Import: CustomerService ◄────┐
                                    │
Service (customer_service.py)      │
  ↓                                 │
  ├─ Import: Database               │
  ├─ Import: CustomerRepository ◄──┼───┐
  ├─ Import: PackageRepository      │   │
  ├─ Import: Schemas                │   │
  └─ Import: sqids_helper           │   │
                                    │   │
Repository (customer_repository.py)│   │
  ↓                                 │   │
  ├─ Import: BaseRepository ◄──────┘   │
  └─ Import: Database                   │
                                        │
BaseRepository (base_repository.py)    │
  ↓                                     │
  └─ Import: Database ◄─────────────────┘
```

## Transaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Transaction Management                     │
└─────────────────────────────────────────────────────────────┘

Controller
  │
  ├─ Get database connection (via Depends)
  │
  ▼
Service
  │
  ├─ Begin transaction (implicit)
  ├─ Call Repository method(s)
  ├─ Business validation
  │
  ├─ SUCCESS? → self.db.conn.commit()    ✓
  │       or
  └─ ERROR?   → self.db.conn.rollback()  ✗
        │
        └─ Raise HTTPException
```

## Error Handling Flow

```
Database Error
  ↓
Repository
  │ (No handling, let it bubble up)
  ↓
Service
  │ try:
  │   ... repository calls ...
  │ except Exception:
  │   self.db.rollback()
  │   raise HTTPException(500, "Database error")
  ↓
Controller
  │ (Service raises HTTPException)
  │
  ↓
FastAPI
  └─ Returns HTTP error response
```

## Architecture Benefits

```
┌─────────────────────────────────────────────────────────────┐
│                         BENEFITS                             │
└─────────────────────────────────────────────────────────────┘

1. Separation of Concerns
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  Controller  │   │   Service    │   │  Repository  │
   │              │   │              │   │              │
   │ HTTP Only    │ → │ Business     │ → │ SQL Only     │
   │              │   │ Logic Only   │   │              │
   └──────────────┘   └──────────────┘   └──────────────┘

2. Testability
   Unit Test       Unit Test         Unit Test
   Controller  →   Service      →    Repository
   (mock service)  (mock repo)       (mock db)

3. Reusability
   Multiple Controllers
        ↓
      Service  ← Can be reused by different controllers
        ↓
   Multiple Repositories

4. Maintainability
   Change SQL?        → Only edit Repository
   Change business?   → Only edit Service
   Change HTTP?       → Only edit Controller
```

## File Structure

```
tagihan-wifi/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/           ← CONTROLLER LAYER
│   │           ├── customers.py     (Thin)
│   │           ├── packages.py      (Thin)
│   │           ├── payments.py      (Thin)
│   │           └── billing.py       (Thin)
│   │
│   ├── services/                    ← SERVICE LAYER
│   │   ├── customer_service.py      (Fat - Business Logic)
│   │   ├── package_service.py       (Fat - Business Logic)
│   │   ├── payment_service.py       (Fat - Business Logic)
│   │   └── billing_service.py       (Fat - Business Logic)
│   │
│   ├── repositories/                ← REPOSITORY LAYER
│   │   ├── base_repository.py       (Common operations)
│   │   ├── customer_repository.py   (SQL queries)
│   │   ├── package_repository.py    (SQL queries)
│   │   ├── payment_repository.py    (SQL queries)
│   │   └── billing_repository.py    (SQL queries)
│   │
│   ├── core/                        ← Shared utilities
│   ├── db/                          ← Database connection
│   ├── schemas/                     ← Pydantic models
│   └── utils/                       ← Helper functions
│
└── markdown/                        ← Documentation
    ├── SPRING_BOOT_ARCHITECTURE.md
    ├── REFACTORING_SUMMARY.md
    ├── LAYERED_ARCHITECTURE_GUIDE.md
    └── ARCHITECTURE_DIAGRAM.md      (This file)
```
