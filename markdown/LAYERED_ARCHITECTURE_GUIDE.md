# Layered Architecture - Quick Reference

## Architecture Pattern: Controller → Service → Repository

```
HTTP Request
    ↓
Controller (Thin - HTTP handling only)
    ↓
Service (Fat - Business logic)
    ↓
Repository (Data access)
    ↓
Database
```

## Quick Examples

### 1. Creating a New Feature

#### Step 1: Repository (Data Access)
```python
# app/repositories/item_repository.py
class ItemRepository(BaseRepository):
    def create(self, name: str, price: int) -> Optional[tuple]:
        query = "INSERT INTO items (name, price) VALUES (?, ?) RETURNING *"
        result = self.execute_insert(query, [name, price])
        return result[0] if result else None
    
    def find_by_id(self, item_id: int) -> Optional[tuple]:
        query = "SELECT * FROM items WHERE id = ? AND is_active = true"
        return self.execute_one(query, [item_id])
```

#### Step 2: Service (Business Logic)
```python
# app/services/item_service.py
from app.repositories import ItemRepository
from app.utils.sqids_helper import get_sqids_helper

class ItemService:
    def __init__(self, db: Database):
        self.db = db
        self.item_repo = ItemRepository(db)
        self.sqids_helper = get_sqids_helper()
    
    def create_item(self, item_data: ItemCreate) -> ItemResponse:
        # Business validation
        if item_data.price < 0:
            raise HTTPException(status_code=400, detail="Price must be positive")
        
        # Create via repository
        item_row = self.item_repo.create(item_data.name, item_data.price)
        self.db.conn.commit()
        
        # Transform to response
        return ItemResponse(
            id=self.sqids_helper.encode_with_prefix(item_row[0], 'item'),
            name=item_row[1],
            price=item_row[2],
            created_at=item_row[3]
        )
```

#### Step 3: Controller (HTTP Handling)
```python
# app/api/v1/endpoints/items.py
from app.services import ItemService

@router.post("", response_model=SingleItemResponse)
async def create_item(
    item_data: ItemCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    service = ItemService(db)
    item = service.create_item(item_data)
    return SingleItemResponse(data=item)
```

## Layer Responsibilities

### ❌ DON'T

```python
# DON'T: Business logic in controller
@router.post("")
async def create_item(item_data: ItemCreate, db: Database = Depends(get_db)):
    if item_data.price < 0:  # ❌ Business logic in controller
        raise HTTPException(...)
    result = db.conn.execute("INSERT...")  # ❌ Direct DB access in controller
```

```python
# DON'T: Response transformation in repository
class ItemRepository:
    def find_by_id(self, id: int) -> ItemResponse:  # ❌ Repository returns Response model
        row = self.execute_one(...)
        return ItemResponse(...)  # ❌ Transformation in repository
```

### ✅ DO

```python
# ✅ Controller: Thin, only HTTP handling
@router.post("")
async def create_item(item_data: ItemCreate, db: Database = Depends(get_db)):
    service = ItemService(db)
    item = service.create_item(item_data)
    return SingleItemResponse(data=item)

# ✅ Service: Business logic and transformation
class ItemService:
    def create_item(self, item_data: ItemCreate) -> ItemResponse:
        # Business validation
        if item_data.price < 0:
            raise HTTPException(...)
        
        # Repository call
        item_row = self.item_repo.create(...)
        
        # Transform to response
        return ItemResponse(...)

# ✅ Repository: Only data access
class ItemRepository:
    def create(self, name: str, price: int) -> Optional[tuple]:
        query = "INSERT..."
        return self.execute_insert(query, [name, price])[0]
```

## Common Patterns

### 1. List with Pagination
```python
# Repository
def find_all_with_filters(self, page: int, per_page: int, name: str = None):
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    
    total = self.count("SELECT COUNT(*) FROM items WHERE 1=1", params)
    
    paginated_query, offset = self.build_pagination_query(query, page, per_page, "name ASC")
    params.extend([per_page, offset])
    
    items = self.execute_query(paginated_query, params)
    return items, total

# Service
def list_items(self, page: int, per_page: int, name: str = None):
    items, total = self.item_repo.find_all_with_filters(page, per_page, name)
    
    data = [self._build_item_response(row) for row in items]
    
    total_pages = (total + per_page - 1) // per_page
    meta = PaginationMeta(total=total, page=page, per_page=per_page, ...)
    
    return data, meta

# Controller
@router.get("")
async def list_items(page: int = 1, per_page: int = 10, name: str = None, db = Depends(get_db)):
    service = ItemService(db)
    data, meta = service.list_items(page, per_page, name)
    return PaginatedItemResponse(data=data, meta=meta)
```

### 2. Update with Validation
```python
# Repository
def update(self, item_id: int, name: str = None, price: int = None):
    updates = []
    params = []
    
    if name:
        updates.append("name = ?")
        params.append(name)
    if price is not None:
        updates.append("price = ?")
        params.append(price)
    
    if not updates:
        return None
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(item_id)
    
    query = f"UPDATE items SET {', '.join(updates)} WHERE id = ? RETURNING *"
    result = self.execute_insert(query, params)
    return result[0] if result else None

# Service
def update_item(self, item_sqid: str, item_data: ItemUpdate) -> ItemResponse:
    # Decode sqid
    actual_id, _ = self.sqids_helper.decode_with_prefix(item_sqid)
    
    # Business validation
    if not self.item_repo.exists_by_id(actual_id):
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item_data.price is not None and item_data.price < 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    
    # Update
    updated_row = self.item_repo.update(actual_id, item_data.name, item_data.price)
    self.db.conn.commit()
    
    return self._build_item_response(updated_row)
```

### 3. Soft Delete
```python
# Repository
def soft_delete(self, item_id: int) -> int:
    query = "UPDATE items SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    return self.execute_update(query, [item_id])

# Service
def delete_item(self, item_sqid: str) -> None:
    actual_id, _ = self.sqids_helper.decode_with_prefix(item_sqid)
    
    affected = self.item_repo.soft_delete(actual_id)
    if affected == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    self.db.conn.commit()

# Controller
@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: str, db = Depends(get_db)):
    service = ItemService(db)
    service.delete_item(item_id)
    return None
```

## BaseRepository Methods

```python
# Execute queries
results = self.execute_query("SELECT * FROM table", [params])
result = self.execute_one("SELECT * FROM table WHERE id = ?", [id])

# Modify data
row = self.execute_insert("INSERT ... RETURNING *", [params])
affected = self.execute_update("UPDATE table SET ...", [params])
affected = self.execute_delete("DELETE FROM table WHERE ...", [params])

# Transaction
self.commit()
self.rollback()

# Count
total = self.count("SELECT COUNT(*) FROM table", [params])

# Pagination
query, offset = self.build_pagination_query(base_query, page, per_page, "name ASC")
```

## Testing

```python
# Test Repository (mock database)
def test_create_item():
    mock_db = Mock()
    repo = ItemRepository(mock_db)
    result = repo.create("Item", 1000)
    assert result is not None

# Test Service (mock repository)
def test_create_item_service():
    mock_repo = Mock()
    mock_repo.create.return_value = (1, "Item", 1000, "2025-01-01")
    
    service = ItemService(mock_db)
    service.item_repo = mock_repo
    
    result = service.create_item(ItemCreate(name="Item", price=1000))
    assert result.name == "Item"

# Test Controller (integration)
async def test_create_item_endpoint():
    response = await client.post("/items", json={"name": "Item", "price": 1000})
    assert response.status_code == 201
```

## Documentation References

- Full architecture guide: [SPRING_BOOT_ARCHITECTURE.md](SPRING_BOOT_ARCHITECTURE.md)
- Complete refactoring summary: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
