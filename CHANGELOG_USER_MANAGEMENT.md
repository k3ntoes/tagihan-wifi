# User Management & Password Change API - Changelog

**Date:** February 14, 2026  
**Version:** 2.0.0

## New Features

### 1. Change Password Endpoint
**Endpoint:** `POST /auth/change-password`

Allows authenticated users to change their own password. The endpoint requires:
- Current password for verification
- New password

**Response:**
- Returns updated user information
- 400 Bad Request: If old password is incorrect
- 404 Not Found: If user not found

### 2. User Management (Admin Only)

#### List All Users
**Endpoint:** `GET /auth/users`

List all users with pagination support.

**Features:**
- Pagination with `page` and `per_page` parameters
- Response includes user metadata (role, status, created_at)

**Response:**
- 200 OK with paginated user list
- 403 Forbidden: If user is not admin

#### Get Specific User
**Endpoint:** `GET /auth/users/{user_id}`

Get detailed information about a specific user.

**Response:**
- 200 OK with user details
- 404 Not Found: If user does not exist
- 403 Forbidden: If user is not admin

#### Update User
**Endpoint:** `PATCH /auth/users/{user_id}`

Update user information (admin only). Allows updating:
- Username (must be unique)
- Password (will be hashed)
- Role (admin or user)
- Active status (is_active)

**Request Format:**
```json
{
  "username": "new_username",
  "password": "new_password",
  "role": "admin",
  "is_active": true
}
```

**Response:**
- 200 OK with updated user
- 400 Bad Request: If username already exists
- 404 Not Found: If user does not exist
- 403 Forbidden: If user is not admin

#### Delete User
**Endpoint:** `DELETE /auth/users/{user_id}`

Delete/remove a user from the system (admin only).

**Restrictions:**
- Admin cannot delete their own account
- Only admin users can delete users

**Response:**
- 204 No Content: Success
- 400 Bad Request: If trying to delete own account
- 404 Not Found: If user does not exist
- 403 Forbidden: If user is not admin

## Technical Changes

### New Schemas Added

1. **PasswordChange** - Request schema for password change
   - old_password: str (min 6 chars)
   - new_password: str (min 6 chars)

2. **UserUpdateAdmin** - Request schema for user updates
   - username: Optional[str]
   - password: Optional[str]
   - role: Optional[RoleEnum]
   - is_active: Optional[bool]

3. **PaginatedUserResponse** - Response wrapper for user list
   - data: List[UserResponse]
   - meta: PaginationMeta

### Core Auth Service Methods

Added helper methods to `AuthService`:
- `hash_password(password: str) -> str` - Hash password with bcrypt
- `verify_password(password: str, hash: str) -> bool` - Verify password against hash

These methods are already available through `PasswordManager` but are now exposed through `AuthService` for convenience.

## API Response Format

All endpoints follow the established response format:

**Single Resource:**
```json
{
  "data": { ...user_object... }
}
```

**Paginated Response:**
```json
{
  "data": [ ...users... ],
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

**Error Response:**
```json
{
  "detail": "Error message"
}
```

## Important Notes

### Request vs Response Format
- **Requests use snake_case:** `old_password`, `new_password`, `is_active`, `per_page`
- **Responses use camelCase:** `isActive`, `createdAt`, `perPage`, `hasNext`

### Authentication
- All user management endpoints require `Authorization: Bearer <token>` header
- Only admin users can access user management endpoints
- Users can only change their own password (no admin override)

### Security
- Passwords are hashed using bcrypt (12 rounds)
- Old password verification is required before changing password
- Admins cannot delete their own account (prevents lockout)

## Database

No database schema changes required. The API uses existing `users` table with columns:
- `id` (integer, primary key)
- `username` (string, unique)
- `password_hash` (string) or `password` (depending on implementation)
- `role` (string: 'admin' or 'user')
- `is_active` (boolean)
- `created_at` (datetime)

## Example Usage

### Change Password (Any User)
```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "oldpass123",
    "new_password": "newpass456"
  }'
```

### List Users (Admin Only)
```bash
curl http://localhost:8000/api/v1/auth/users?page=1&per_page=10 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Update User Role (Admin Only)
```bash
curl -X PATCH http://localhost:8000/api/v1/auth/users/2 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

### Delete User (Admin Only)
```bash
curl -X DELETE http://localhost:8000/api/v1/auth/users/2 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Testing

All new endpoints have been implemented and tested for syntax correctness. To test the API:

1. Start the application:
   ```bash
   python3 main.py
   ```

2. Login to get token:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   ```

3. Use the token for subsequent requests

## Files Modified

1. **app/api/v1/endpoints/auth.py** - Added new endpoints
   - POST /auth/change-password
   - GET /auth/users
   - GET /auth/users/{user_id}
   - PATCH /auth/users/{user_id}
   - DELETE /auth/users/{user_id}

2. **app/schemas/__init__.py** - Added new schemas
   - PasswordChange
   - UserUpdateAdmin
   - PaginatedUserResponse

3. **app/core/auth.py** - Added helper methods
   - hash_password()
   - verify_password()

4. **API_DOCUMENTATION.md** - Updated documentation
   - Added endpoint details
   - Added NextJS integration examples
   - Added cURL examples

## Backward Compatibility

All existing endpoints remain unchanged. New endpoints are additions and do not affect existing functionality.

## Future Improvements

- [ ] Email verification for password changes
- [ ] Password change history/audit log
- [ ] Bulk user import/export
- [ ] User role templates
- [ ] Two-factor authentication
- [ ] API key management for programmatic access

---

**Status:** ✅ Complete and Ready for Testing
