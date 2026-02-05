# Plan: Standardize Response Wrapping Across Schemas

Wrap single resource responses (Package, Payment, optionally User) in nested objects with a `data` field, following the existing `SingleCustomerResponse` pattern for consistency and predictable API responses.

## Steps

1. Create `SinglePackageResponse` wrapper class in `app/schemas/__init__.py` wrapping `PackageResponse` with `data` field. ✅

2. Create `SinglePaymentResponse` wrapper class in `app/schemas/__init__.py` wrapping `PaymentResponse` with `data` field. ✅

3. Update `app/api/v1/endpoints/packages.py` to return `SinglePackageResponse` for `POST /packages`, `GET /packages/{id}`, and `PUT /packages/{id}` endpoints. ✅

4. Update `app/api/v1/endpoints/payments.py` to return `SinglePaymentResponse` for `POST /payments` and `POST /payments/parse-log` endpoints. ✅

5. (Optional) Create `SingleUserResponse` in `app/schemas/__init__.py` and update auth endpoints for complete consistency. ✅ (class added; endpoints not updated)

## Implementation Status

- Wrappers added: `SinglePackageResponse`, `SinglePaymentResponse`, `SingleUserResponse`.
- Packages endpoints now return nested data object for single-item responses.
- Payments endpoints now return nested data object for single-item responses.

## Example Response (Post-change)

Single resource responses now return:

{ "data": { ...resource fields... } }

Example for POST /packages:

{ "data": { "id": "pkg_abc123", "name": "Basic", "speed": 10, "price": 50000, "is_active": true, "created_at": "2026-02-05T10:00:00", "updated_at": "2026-02-05T10:00:00" } }

## Further Considerations

1. **Scope of change:** Should auth endpoints (`POST /auth/register`, `GET /auth/me`) also wrap `UserResponse`? Or keep auth responses separate following different patterns?

2. **Error responses:** Verify that error responses don't need similar wrapping adjustments.

## Reference Pattern: SingleCustomerResponse

```python
class SingleCustomerResponse(BaseModel):
    """Single customer response wrapper"""
    data: CustomerResponse
```

## Summary: Response Wrapping Pattern Analysis

### Response Classes That Should Be Wrapped in Nested Pattern

| Response Class | Should Wrap? | Current Direct Usage | Wrapper Name Needed | Notes |
|---|---|---|---|---|
| **PackageResponse** | ✅ YES | `POST /packages` (create), `GET /packages/{id}` (get single), `PUT /packages/{id}` (update) | `SinglePackageResponse` | Currently returns raw PackageResponse for single item endpoints |
| **PaymentResponse** | ✅ YES | `POST /payments` (create), `POST /payments/parse-log` (create) | `SinglePaymentResponse` | Currently returns raw PaymentResponse for single item creation |
| **BillingMatrixResponse** | ❌ NO | `GET /billing/matrix` (get matrix) | Already wrapped | Returns with data wrapper, but BillingMatrixResponse itself is not used directly |
| **CustomerResponse** | ✅ PARTIAL | `POST /customers` (create) - **WRAPPED**, `GET /customers/{id}` (get single) - **WRAPPED** | Already has `SingleCustomerResponse` | ✅ GOOD: Already follows pattern consistently |
| **UserResponse** | ⚠️ MAYBE | `POST /auth/register` (create), `GET /auth/me` (get user) | `SingleUserResponse` | Could be wrapped for consistency, but auth endpoints may have different pattern |

### Detailed Usage by Endpoint

#### Auth Endpoints (`app/api/v1/endpoints/auth.py`)
- `POST /auth/login` → Returns `TokenResponse` directly
- `POST /auth/register` → Returns `UserResponse` directly (**SHOULD BE WRAPPED**)
- `GET /auth/me` → Returns `UserResponse` directly (**SHOULD BE WRAPPED**)

#### Packages Endpoints (`app/api/v1/endpoints/packages.py`)
- `POST /packages` → Returns `PackageResponse` **SHOULD BE WRAPPED**
- `GET /packages` → Returns `PaginatedPackageResponse` (already paginated with data wrapper) ✅
- `GET /packages/{id}` → Returns `PackageResponse` **SHOULD BE WRAPPED**
- `PUT /packages/{id}` → Returns `PackageResponse` **SHOULD BE WRAPPED**

#### Customers Endpoints (`app/api/v1/endpoints/customers.py`)
- `POST /customers` → Returns `SingleCustomerResponse` ✅ (wrapped)
- `GET /customers` → Returns `PaginatedCustomerResponse` (already paginated with data wrapper) ✅
- `GET /customers/{id}` → Returns `SingleCustomerResponse` ✅ (wrapped)
- `PUT /customers/{id}` → Returns `SingleCustomerResponse` ✅ (wrapped)

#### Payments Endpoints (`app/api/v1/endpoints/payments.py`)
- `POST /payments` → Returns `PaymentResponse` **SHOULD BE WRAPPED**
- `GET /payments` → Returns `PaginatedPaymentResponse` (already paginated with data wrapper) ✅
- `POST /payments/parse-log` → Returns `PaymentResponse` **SHOULD BE WRAPPED**

#### Billing Endpoints (`app/api/v1/endpoints/billing.py`)
- `GET /billing/matrix` → Returns `PaginatedBillingMatrixResponse` (already paginated with data wrapper) ✅

### Consistency Updates Needed

**Create new wrapper classes in schemas:**

1. **`SinglePackageResponse`** - Wrap `PackageResponse`
   ```python
   class SinglePackageResponse(BaseModel):
       data: PackageResponse
   ```

2. **`SinglePaymentResponse`** - Wrap `PaymentResponse`
   ```python
   class SinglePaymentResponse(BaseModel):
       data: PaymentResponse
   ```

3. **`SingleUserResponse`** (Optional, for consistency with auth pattern)
   ```python
   class SingleUserResponse(BaseModel):
       data: UserResponse
   ```

**Update endpoints:**
- `packages.py`: Change `POST /packages`, `GET /packages/{id}`, `PUT /packages/{id}` to use `SinglePackageResponse`
- `payments.py`: Change `POST /payments`, `POST /payments/parse-log` to use `SinglePaymentResponse`
- `auth.py`: (Optional) Change `POST /auth/register`, `GET /auth/me` to use `SingleUserResponse`

### Pattern Summary

✅ **Already Good:** 
- `CustomerResponse` consistently wrapped in `SingleCustomerResponse` for all single-item endpoints
- Paginated responses already use `data` wrapper

⚠️ **Inconsistent:**
- `PackageResponse` - direct return for single items, needs wrapper
- `PaymentResponse` - direct return for single items, needs wrapper
- `UserResponse` - direct return for single items, could add wrapper for consistency

❌ **No Action Needed:**
- `BillingMatrixResponse` - already paginated wrapper
- `PaginatedResponses` - already have `data` field
