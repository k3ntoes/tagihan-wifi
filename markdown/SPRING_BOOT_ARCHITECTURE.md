# Spring Boot Architecture Implementation

## Overview

Aplikasi telah direfactor mengikuti pola arsitektur Spring Boot dengan pemisahan yang jelas antara layer:
- **Controller Layer** (Endpoints)
- **Service Layer** (Business Logic)
- **Repository Layer** (Data Access)

## Struktur Direktori

```
app/
├── api/
│   └── v1/
│       └── endpoints/        # Controller Layer
│           ├── auth.py
│           ├── customers.py
│           ├── packages.py
│           ├── payments.py
│           └── billing.py
├── services/                 # Service Layer
│   ├── __init__.py
│   ├── customer_service.py
│   ├── package_service.py
│   ├── payment_service.py
│   └── billing_service.py
├── repositories/             # Repository Layer
│   ├── __init__.py
│   ├── base_repository.py
│   ├── customer_repository.py
│   ├── package_repository.py
│   ├── payment_repository.py
│   └── billing_repository.py
├── core/
├── db/
├── schemas/
└── utils/
```

## Layer Responsibilities

### 1. Controller Layer (Endpoints)

**Lokasi:** `app/api/v1/endpoints/`

**Tanggung Jawab:**
- Menerima HTTP requests
- Validasi input dari request
- Memanggil service layer untuk business logic
- Mengembalikan HTTP responses

**Karakteristik:**
- Tipis (thin) - tidak ada business logic
- Hanya fokus pada HTTP handling
- Dependency injection untuk Database dan auth

**Contoh:**
```python
@router.post("", response_model=SingleCustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = CustomerService(db)
    customer = service.create_customer(customer_data)
    return SingleCustomerResponse(data=customer)
```

### 2. Service Layer

**Lokasi:** `app/services/`

**Tanggung Jawab:**
- Business logic dan validasi bisnis
- Koordinasi antara multiple repositories
- Transaction management
- Data transformation (DB row -> Response model)

**Karakteristik:**
- Tebal (fat) - mengandung semua business logic
- Independen dari HTTP layer
- Dapat digunakan ulang di berbagai endpoints
- Menangani error handling dan exception

**Contoh:**
```python
class CustomerService:
    def __init__(self, db: Database):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.package_repo = PackageRepository(db)
        self.sqids_helper = get_sqids_helper()

    def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        # Business validation
        if customer_data.package_id:
            actual_package_id = self._decode_package_id(customer_data.package_id)
            if not self.package_repo.exists_by_id(actual_package_id):
                raise HTTPException(...)
        
        # Create via repository
        customer_row = self.customer_repo.create(...)
        self.db.conn.commit()
        
        # Transform to response
        return self._build_customer_response(customer_row)
```

### 3. Repository Layer

**Lokasi:** `app/repositories/`

**Tanggung Jawab:**
- Data access operations (CRUD)
- Query building
- Database interaction
- No business logic

**Karakteristik:**
- Hanya fokus pada database operations
- Mengembalikan raw data (tuples)
- Reusable query methods
- Generic operations di BaseRepository

**Contoh:**
```python
class CustomerRepository(BaseRepository):
    def create(self, name: str, package_id: Optional[int], monthly_fee: int) -> Optional[tuple]:
        query = """
            INSERT INTO customers (name, package_id, monthly_fee)
            VALUES (?, ?, ?)
            RETURNING id, name, package_id, monthly_fee, created_at, updated_at
        """
        result = self.execute_insert(query, [name, package_id, monthly_fee])
        return result[0] if result else None

    def find_by_id(self, customer_id: int) -> Optional[tuple]:
        query = """
            SELECT c.id, c.name, c.package_id, p.name as package_name, 
                   c.monthly_fee, c.created_at, c.updated_at
            FROM customers c
            LEFT JOIN packages p ON c.package_id = p.id
            WHERE c.id = ? AND c.is_active = true
        """
        return self.execute_one(query, [customer_id])
```

## Data Flow

```
HTTP Request
    ↓
Controller (endpoints)
    ↓
Service (business logic)
    ↓
Repository (data access)
    ↓
Database
```

Response flow adalah kebalikannya:
```
Database (raw tuples)
    ↓
Repository (return tuples)
    ↓
Service (transform to Response models)
    ↓
Controller (return HTTP response)
    ↓
HTTP Response
```

## Benefits

### 1. Separation of Concerns
- Setiap layer memiliki tanggung jawab yang jelas
- Mudah untuk menemukan dan memperbaiki bugs
- Testing lebih mudah karena isolation

### 2. Reusability
- Service methods dapat digunakan di multiple endpoints
- Repository methods dapat digunakan di multiple services
- BaseRepository menyediakan common operations

### 3. Maintainability
- Perubahan business logic hanya di service layer
- Perubahan query hanya di repository layer
- Perubahan HTTP handling hanya di controller layer

### 4. Testability
- Unit test untuk repository (mock database)
- Unit test untuk service (mock repository)
- Integration test untuk controller (mock service)

## Migration from Old Code

### Before (Monolithic Controller):
```python
@router.post("")
async def create_customer(customer_data: CustomerCreate, db: Database = Depends(get_db)):
    # Validation
    if customer_data.package_id:
        package_check = db.conn.execute("SELECT...").fetchone()
        if not package_check:
            raise HTTPException(...)
    
    # Insert
    result = db.conn.execute("INSERT...").fetchall()
    db.conn.commit()
    
    # Transform
    customer_sqid = sqids_helper.encode(...)
    return SingleCustomerResponse(data=CustomerResponse(...))
```

### After (Layered Architecture):
```python
# Controller
@router.post("")
async def create_customer(customer_data: CustomerCreate, db: Database = Depends(get_db)):
    service = CustomerService(db)
    customer = service.create_customer(customer_data)
    return SingleCustomerResponse(data=customer)

# Service
class CustomerService:
    def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
        # Validation
        if customer_data.package_id:
            if not self.package_repo.exists_by_id(...):
                raise HTTPException(...)
        
        # Create
        customer_row = self.customer_repo.create(...)
        self.db.conn.commit()
        
        # Transform
        return self._build_customer_response(customer_row)

# Repository
class CustomerRepository:
    def create(self, name, package_id, monthly_fee) -> Optional[tuple]:
        query = "INSERT INTO customers..."
        return self.execute_insert(query, [name, package_id, monthly_fee])[0]
```

## Best Practices

### 1. Controller Layer
- ✅ Thin controllers
- ✅ Only HTTP handling
- ✅ Delegate to services
- ❌ No business logic
- ❌ No direct database access

### 2. Service Layer
- ✅ All business logic here
- ✅ Coordinate multiple repositories
- ✅ Handle transactions
- ✅ Transform data to response models
- ❌ No HTTP-specific code
- ❌ No direct SQL queries

### 3. Repository Layer
- ✅ Only database operations
- ✅ Return raw data (tuples)
- ✅ Reusable query methods
- ❌ No business logic
- ❌ No response model creation

## Example: Complete Flow

### Request: Create Customer

1. **Controller** (`customers.py`):
```python
@router.post("", response_model=SingleCustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    service = CustomerService(db)
    customer = service.create_customer(customer_data)
    return SingleCustomerResponse(data=customer)
```

2. **Service** (`customer_service.py`):
```python
def create_customer(self, customer_data: CustomerCreate) -> CustomerResponse:
    # Decode package_id from sqid
    actual_package_id = None
    if customer_data.package_id:
        actual_package_id, _ = self.sqids_helper.decode_with_prefix(customer_data.package_id)
        
        # Validate package exists
        if not self.package_repo.exists_by_id(actual_package_id):
            raise HTTPException(status_code=400, detail="Package not found")
    
    # Create customer via repository
    customer_row = self.customer_repo.create(
        customer_data.name, 
        actual_package_id, 
        customer_data.monthly_fee
    )
    
    # Commit transaction
    self.db.conn.commit()
    
    # Build response
    return self._build_customer_response(customer_row)
```

3. **Repository** (`customer_repository.py`):
```python
def create(self, name: str, package_id: Optional[int], monthly_fee: int) -> Optional[tuple]:
    query = """
        INSERT INTO customers (name, package_id, monthly_fee)
        VALUES (?, ?, ?)
        RETURNING id, name, package_id, monthly_fee, created_at, updated_at
    """
    result = self.execute_insert(query, [name, package_id, monthly_fee])
    return result[0] if result else None
```

## Testing Strategy

### Repository Tests
```python
def test_customer_repository_create():
    repo = CustomerRepository(mock_db)
    result = repo.create("John Doe", 1, 50000)
    assert result is not None
    assert result[1] == "John Doe"
```

### Service Tests
```python
def test_customer_service_create():
    mock_repo = Mock()
    mock_repo.create.return_value = (1, "John", 1, 50000, "2025-01-01", "2025-01-01")
    
    service = CustomerService(mock_db)
    service.customer_repo = mock_repo
    
    result = service.create_customer(customer_data)
    assert result.name == "John"
```

### Controller Tests
```python
async def test_create_customer_endpoint():
    response = await client.post("/api/v1/customers", json={...})
    assert response.status_code == 201
```

## Conclusion

Refactoring ini mengubah aplikasi dari monolithic controller menjadi layered architecture yang clean dan maintainable, mengikuti best practices dari Spring Boot framework.
