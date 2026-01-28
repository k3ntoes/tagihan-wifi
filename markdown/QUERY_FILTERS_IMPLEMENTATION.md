# Query Filter Parameters - Implementation Summary

## Overview

Semua endpoint list telah dilengkapi dengan **query filter parameters** untuk memfilter data berdasarkan kriteria tertentu.

## Filter yang Diimplementasikan

### 1. **Customer Endpoint** (`GET /api/v1/customers`)

**Filter Parameters:**
- `name` (Optional[str]) - Filter berdasarkan nama customer (partial match, case-insensitive)
- `package_id` (Optional[str]) - Filter berdasarkan package ID (exact match, sqid format)

**Contoh Request:**
```bash
# Filter by name
GET /api/v1/customers?name=john

# Filter by package_id
GET /api/v1/customers?package_id=pack_UGOv07iL_6VR5dt

# Combined filters
GET /api/v1/customers?name=test&package_id=pack_UGOv07iL_6VR5dt
```

**Logika:**
- `name`: WHERE LOWER(c.name) LIKE LOWER('%{name}%')
- `package_id`: WHERE c.package_id = {decoded_id}
- Hanya dijalankan jika parameter tidak None atau empty string

---

### 2. **Package Endpoint** (`GET /api/v1/packages`)

**Filter Parameters:**
- `name` (Optional[str]) - Filter berdasarkan nama package (partial match, case-insensitive)
- `min_speed` (Optional[int]) - Filter kecepatan minimum (Mbps)
- `max_speed` (Optional[int]) - Filter kecepatan maksimum (Mbps)
- `min_price` (Optional[int]) - Filter harga minimum (Rupiah)
- `max_price` (Optional[int]) - Filter harga maksimum (Rupiah)
- `include_inactive` (bool) - Sertakan package inactive (default: False)

**Contoh Request:**
```bash
# Filter by name
GET /api/v1/packages?name=premium

# Filter by speed range
GET /api/v1/packages?min_speed=50&max_speed=100

# Filter by price range
GET /api/v1/packages?min_price=100000&max_price=250000

# Combined filters
GET /api/v1/packages?name=test&min_speed=50&max_price=200000

# Include inactive packages
GET /api/v1/packages?include_inactive=true
```

**Logika:**
- `name`: WHERE LOWER(name) LIKE LOWER('%{name}%')
- `min_speed`: WHERE speed >= {min_speed}
- `max_speed`: WHERE speed <= {max_speed}
- `min_price`: WHERE price >= {min_price}
- `max_price`: WHERE price <= {max_price}
- `include_inactive`: Tidak menambahkan WHERE is_active = true jika true

---

### 3. **Payment Endpoint** (`GET /api/v1/payments`)

**Filter Parameters (sudah ada, tidak diubah):**
- `customer_id` (Optional[str]) - Filter berdasarkan customer ID (sqid format)
- `year` (Optional[int]) - Filter berdasarkan tahun billing
- `month` (Optional[int]) - Filter berdasarkan bulan billing

**Contoh Request:**
```bash
# Filter by year
GET /api/v1/payments?year=2026

# Filter by month and year
GET /api/v1/payments?month=1&year=2026

# Filter by customer
GET /api/v1/payments?customer_id=cust_Ke58cbNm_wJjo8m
```

---

### 4. **Billing Matrix Endpoint** (`GET /api/v1/billing-matrix/{year}`)

**Filter Parameters:**
- `customer_id` (Optional[str]) - Filter customer tertentu (sqid format)
- `customer_name` (Optional[str]) - Filter berdasarkan nama customer (partial match, case-insensitive)

**Contoh Request:**
```bash
# All customers
GET /api/v1/billing-matrix/2026

# Specific customer by ID
GET /api/v1/billing-matrix/2026?customer_id=cust_Ke58cbNm_wJjo8m

# Filter by name
GET /api/v1/billing-matrix/2026?customer_name=john
```

**Logika:**
- `customer_id`: WHERE id = {decoded_id}
- `customer_name`: WHERE LOWER(name) LIKE LOWER('%{name}%')

---

## Implementasi Pattern

### Filter Logic Pattern

Semua filter mengikuti pattern yang konsisten:

```python
# Build base query
query = "SELECT ... FROM table WHERE 1=1"
params = []

# Add filters conditionally
if filter_param and filter_param.strip():  # Check not None and not empty
    query += " AND column_name = ?"
    params.append(filter_value)

# Execute with params
result = db.conn.execute(query, params).fetchall()
```

### Sqid Validation Pattern

Untuk filter yang menggunakan sqid (customer_id, package_id):

```python
if sqid_param and sqid_param.strip():
    try:
        actual_id, model = sqids_helper.decode_with_prefix(sqid_param)
        if model != 'expected_model':
            raise ValueError("Wrong model type")
        query += " AND column = ?"
        params.append(actual_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ID: {sqid_param}"
        )
```

### Case-Insensitive Pattern

Untuk filter text (name):

```python
if name and name.strip():
    query += " AND LOWER(column) LIKE LOWER(?)"
    params.append(f"%{name.strip()}%")
```

### Range Filter Pattern

Untuk filter numerik (speed, price):

```python
if min_value is not None:
    query += " AND column >= ?"
    params.append(min_value)

if max_value is not None:
    query += " AND column <= ?"
    params.append(max_value)
```

---

## Testing

### Manual Test
```bash
# Start server
python -m uvicorn main:app --reload --port 8000

# Run test script
python test_query_filters.py
```

### cURL Examples

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Test customer filter by name
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/customers?name=test"

# Test package filter by speed range
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/packages?min_speed=50&max_speed=100"

# Test billing matrix filter by customer name
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/billing-matrix/2026?customer_name=john"
```

---

## Benefits

✅ **Flexible Querying** - Frontend bisa filter data sesuai kebutuhan  
✅ **Performance** - Filter di database, bukan di aplikasi  
✅ **User Experience** - Response lebih cepat dengan data yang relevan  
✅ **API Clean** - Parameter optional, tidak mengubah behavior default  
✅ **Type Safe** - Validasi sqid dengan prefix checking  

---

## Implementation Files

- ✅ [customers.py](app/api/v1/endpoints/customers.py) - 2 filters
- ✅ [packages.py](app/api/v1/endpoints/packages.py) - 6 filters
- ✅ [payments.py](app/api/v1/endpoints/payments.py) - 3 filters (existing)
- ✅ [billing.py](app/api/v1/endpoints/billing.py) - 2 filters

---

## API Documentation

Semua filter parameters otomatis terdokumentasi di Swagger UI:

**Access:** http://localhost:8000/docs

Setiap parameter memiliki:
- Description
- Type information
- Optional/Required status
- Default values
- Validation rules

---

## Future Enhancements

Fitur filter yang bisa ditambahkan:

1. **Sort Parameters** - Sorting by column (asc/desc)
2. **Pagination** - Limit & offset for large datasets
3. **Date Range** - Filter by date range
4. **Multiple IDs** - Filter by array of IDs
5. **Full-text Search** - Advanced search capabilities

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** January 28, 2026
