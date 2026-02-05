# Tagihan WiFi - Frontend Generation Prompt

## Project Overview

Generate a **static Next.js frontend application** for the Tagihan WiFi billing management system. The frontend must be compatible with **static export** (no Node.js runtime dependency) using `next export` for deployment as pure HTML/CSS/JS.

### Backend API Reference
- **Base URL:** `https://be-tagihan-wifi.kentoes.my.id/api/v1` (development) or environment-configurable
- **Authentication:** JWT Bearer tokens
- **API Schema:** See sections below for all endpoints and models

---

## Technical Requirements

### Core Stack
- **Framework:** Next.js 16+ with App Router
- **UI Library:** shadcn/ui components
- **State Management & Data Fetching:** TanStack Query (React Query)
- **Table Library:** TanStack Table (React Table)
- **Styling:** Tailwind CSS with shadcn/ui presets
- **HTTP Client:** Axios or Fetch API
- **Environment:** Node.js 22+
<!-- - **Routing:** TanStack Router (for client-side routing in static export) -->

### Static Export Configuration
```javascript
// next.config.js requirements
const nextConfig = {
  output : 'export' // Static export mode
  railingSlash : true; // For proper routing
// ISR not available - only static generation
// No dynamic route parameters in [brackets]
}
```

### Authentication & Storage
- **Local Storage:** JWT token persistence (`auth_token`, `user_role`)
- **Protected Routes:** Client-side protection with TanStack Router guards
- **Token Refresh:** Implement token refresh strategy or session-based auth
- **Logout:** Clear token and redirect to login

---

## Application Structure

### Directory Layout
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                    # Landing/Login page
│   │   ├── dashboard/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                # Dashboard overview
│   │   │   ├── customers/
│   │   │   │   ├── page.tsx            # Customer list
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx        # Customer detail
│   │   │   │   └── create/
│   │   │   │       └── page.tsx        # Create customer
│   │   │   ├── packages/
│   │   │   │   ├── page.tsx            # Package list
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx        # Package detail
│   │   │   │   └── create/
│   │   │   │       └── page.tsx        # Create package
│   │   │   ├── payments/
│   │   │   │   ├── page.tsx            # Payment list
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx        # Payment detail
│   │   │   │   └── create/
│   │   │   │       └── page.tsx        # Record payment
│   │   │   ├── billing/
│   │   │   │   └── page.tsx            # Billing matrix annual view
│   │   │   └── admin/
│   │   │       └── users/
│   │   │           └── page.tsx        # User management (admin only)
│   │   └── error.tsx                   # Error boundary
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── DashboardLayout.tsx
│   │   │   └── Footer.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── LogoutButton.tsx
│   │   ├── customers/
│   │   │   ├── CustomerTable.tsx
│   │   │   ├── CustomerForm.tsx
│   │   │   ├── CustomerDetail.tsx
│   │   │   └── CustomerFilters.tsx
│   │   ├── packages/
│   │   │   ├── PackageTable.tsx
│   │   │   ├── PackageForm.tsx
│   │   │   ├── PackageDetail.tsx
│   │   │   └── PackageFilters.tsx
│   │   ├── payments/
│   │   │   ├── PaymentTable.tsx
│   │   │   ├── PaymentForm.tsx
│   │   │   ├── PaymentDetail.tsx
│   │   │   └── PaymentFilters.tsx
│   │   ├── billing/
│   │   │   ├── BillingMatrix.tsx
│   │   │   ├── BillingStats.tsx
│   │   │   ├── BillingFilters.tsx
│   │   │   └── BillingExport.tsx
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── EmptyState.tsx
│   │       └── ConfirmDialog.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useCustomers.ts
│   │   ├── usePackages.ts
│   │   ├── usePayments.ts
│   │   ├── useBilling.ts
│   │   └── useLocalStorage.ts
│   ├── services/
│   │   ├── api/
│   │   │   ├── client.ts               # Axios instance with interceptors
│   │   │   ├── auth.ts                 # Auth API calls
│   │   │   ├── customers.ts
│   │   │   ├── packages.ts
│   │   │   ├── payments.ts
│   │   │   └── billing.ts
│   │   └── auth/
│   │       ├── tokenManager.ts         # Token persistence & refresh
│   │       └── authStorage.ts          # LocalStorage wrapper
│   ├── lib/
│   │   ├── utils.ts                    # Utility functions
│   │   ├── queryClient.ts              # TanStack Query config
│   │   ├── tanstackRouter.tsx          # Router config
│   │   └── formatters.ts               # Date/number formatting
│   ├── types/
│   │   ├── api.ts                      # API response types
│   │   ├── auth.ts
│   │   ├── customer.ts
│   │   ├── package.ts
│   │   ├── payment.ts
│   │   ├── billing.ts
│   │   └── common.ts
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   └── ThemeContext.tsx
│   ├── constants/
│   │   ├── api.ts                      # API endpoints
│   │   ├── roles.ts
│   │   └── messages.ts
│   └── styles/
│       └── globals.css                 # Global Tailwind styles
├── public/
│   ├── favicon.ico
│   └── logo.png
├── .env.example
├── .env.local
├── next.config.mjs                     # Static export config
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── package.json
└── README.md
```

---

## API Endpoints & Models

### 1. Authentication Endpoints

#### POST `/auth/login`
**Request:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### POST `/auth/register`
**Request:**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "user"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "newuser",
  "role": "user",
  "is_active": true,
  "created_at": "2026-01-30T10:00:00Z"
}
```

---

### 2. Packages Endpoints

#### GET `/packages`
**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 10, max: 100)
- `name` (filter by name)
- `min_speed` (filter minimum speed in Mbps)
- `max_speed` (filter maximum speed in Mbps)
- `min_price` (filter minimum price in Rupiah)
- `max_price` (filter maximum price in Rupiah)

**Response (200):**
```json
{
  "data": [
    {
      "id": "package_abc123",
      "name": "Basic",
      "speed": 10,
      "price": 150000,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "per_page": 10,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET `/packages/{id}`
**Response (200):** Single package object

#### POST `/packages` (Admin only)
**Request:**
```json
{
  "name": "Premium",
  "speed": 50,
  "price": 350000
}
```

**Response (201):** Created package object

#### PUT `/packages/{id}` (Admin only)
**Request:**
```json
{
  "name": "Premium Plus",
  "speed": 100,
  "price": 450000
}
```

**Response (200):** Updated package object

#### DELETE `/packages/{id}` (Admin only)
**Response (204):** No content

---

### 3. Customers Endpoints

#### GET `/customers`
**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 10, max: 100)
- `name` (filter by name)
- `package_id` (filter by package sqid)

**Response (200):**
```json
{
  "data": [
    {
      "id": "customer_xyz789",
      "name": "Budi",
      "package_id": "package_abc123",
      "package_name": "Basic",
      "monthly_fee": 150000,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET `/customers/{id}`
**Response (200):** Single customer object with package details

#### POST `/customers` (Admin only)
**Request:**
```json
{
  "name": "Ahmad",
  "package_id": "package_abc123",
  "monthly_fee": 150000
}
```

**Response (201):** Created customer object

#### PUT `/customers/{id}` (Admin only)
**Request:**
```json
{
  "name": "Ahmad Updated",
  "monthly_fee": 175000
}
```

**Response (200):** Updated customer object

#### DELETE `/customers/{id}` (Admin only)
**Response (204):** No content

---

### 4. Payments Endpoints

#### GET `/payments`
**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 10, max: 100)
- `customer_id` (filter by customer sqid)
- `billing_year` (filter by year)
- `billing_month` (filter by month, 1-12)

**Response (200):**
```json
{
  "data": [
    {
      "id": "payment_def456",
      "customer_id": "customer_xyz789",
      "payment_date": "2026-01-15",
      "billing_month": 1,
      "billing_year": 2026,
      "amount": 150000,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z"
    }
  ],
  "meta": {
    "total": 500,
    "page": 1,
    "per_page": 10,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET `/payments/{id}`
**Response (200):** Single payment object

#### POST `/payments` (Admin only)
**Request:**
```json
{
  "customer_id": "customer_xyz789",
  "payment_date": "2026-01-15",
  "billing_month": 1,
  "billing_year": 2026,
  "amount": 150000
}
```

**Response (201):** Created payment object

#### POST `/payments/parse-log` (Admin only)
**Request:**
```json
{
  "log_entry": "15-01-2026 Budi"
}
```

**Response (200):** Parsed and recorded payment

#### DELETE `/payments/{id}` (Admin only)
**Response (204):** No content

---

### 5. Billing Matrix Endpoints

#### GET `/billing/matrix`
**Query Parameters:**
- `year` (default: current year)
- `page` (default: 1)
- `per_page` (default: 10, max: 100)
- `customer_id` (optional, filter by customer sqid)
- `customer_name` (optional, filter by name)

**Response (200):**
```json
{
  "year": 2026,
  "month_names": ["January", "February", ..., "December"],
  "data": [
    {
      "customer_id": "customer_xyz789",
      "customer_name": "Budi",
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
      ],
      "total_paid": 450000,
      "total_expected": 1800000,
      "completion_percentage": 25.0
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

#### GET `/billing/summary`
**Query Parameters:**
- `year` (default: current year)

**Response (200):**
```json
{
  "year": 2026,
  "total_customers": 100,
  "total_monthly_fee": 15000000,
  "total_expected": 180000000,
  "total_paid": 45000000,
  "completion_percentage": 25.0,
  "avg_completion_percentage": 25.0,
  "customers_fully_paid": 10,
  "customers_no_payment": 30,
  "customers_partial_payment": 60
}
```

---

## UI/UX Requirements

### Design System
- **Color Scheme:** Use shadcn/ui default (light/dark mode support)
- **Responsive:** Mobile-first, support tablets and desktops
- **Accessibility:** WCAG 2.1 AA compliance, keyboard navigation

### Pages & Components

#### 1. **Login Page**
- Simple login form with username/password fields
- Remember me checkbox (token in localStorage for 7 days)
- Error message display
- Loading state during authentication
- Redirect to dashboard on successful login

#### 2. **Dashboard**
- Overview cards: total customers, total packages, total paid, expected revenue
- Recent payments chart/table
- Quick actions: add customer, record payment, view billing
- User role indicator (admin/user)

#### 3. **Customers Management**
- **List View:**
  - TanStack Table with sorting/filtering
  - Columns: ID, Name, Package, Monthly Fee, Status, Actions
  - Advanced filters: name, package
  - Pagination (10 items default)
  - Add/Edit/Delete actions (admin only)
  - Row click to view detail

- **Detail View:**
  - Customer information with payment history
  - Associate/change package
  - View all payments for customer
  - Total paid vs expected

- **Create/Edit Form:**
  - Fields: name, package selection, monthly fee
  - Form validation with error display
  - Submit/Cancel buttons
  - Success/error notifications

#### 4. **Packages Management**
- **List View:**
  - TanStack Table with sorting/filtering
  - Columns: ID, Name, Speed (Mbps), Price (Rp), Status, Actions
  - Advanced filters: name, speed range, price range
  - Pagination
  - Add/Edit/Delete actions (admin only)

- **Create/Edit Form:**
  - Fields: name, speed, price
  - Validation (speed & price > 0)
  - Currency display (Rupiah formatting)

#### 5. **Payments Management**
- **List View:**
  - TanStack Table with sorting/filtering
  - Columns: ID, Customer, Month/Year, Amount, Payment Date, Actions
  - Filters: customer, billing year, billing month
  - Pagination
  - Record/Delete payment (admin only)
  - Export to CSV button

- **Record Payment Form:**
  - Customer selection (dropdown with search)
  - Payment date picker
  - Billing month/year dropdowns
  - Amount field
  - Parse log option (paste from manual log)

#### 6. **Billing Matrix**
- **Annual View:**
  - Customer rows with monthly payment status columns
  - 12 month columns (Jan-Dec) showing:
    - Green checkmark if paid
    - Red X if not paid
    - Amount on hover
  - Total paid column
  - Completion percentage bar
  - Filter by customer/year
  - Export to Excel/PDF button
  - Print-friendly layout

- **Summary Stats:**
  - Cards: Total Customers, Total Monthly Fee, Revenue, Completion %
  - Charts: Monthly completion trend, Customer payment distribution

#### 7. **Admin - User Management** (Admin only)
- List of users with role and status
- Add/Edit/Delete user
- Role assignment (admin/user)
- Activate/deactivate users

---

## Required Features

### Authentication & Authorization
- [ ] JWT token management (store in localStorage)
- [ ] Login/logout functionality
- [ ] Protected routes based on user role
- [ ] Automatic token refresh or re-login on expiration
- [ ] Clear error messages for auth failures

### Data Management
- [ ] Pagination support for all list views
- [ ] Sorting by column headers
- [ ] Advanced filtering (multiple criteria)
- [ ] Search functionality where applicable
- [ ] Batch operations (select multiple, delete)

### User Experience
- [ ] Loading spinners during data fetching
- [ ] Error handling with user-friendly messages
- [ ] Toast notifications for CRUD operations
- [ ] Confirmation dialogs for destructive actions
- [ ] Responsive design for mobile/tablet/desktop
- [ ] Keyboard navigation support

### Performance
- [ ] TanStack Query for efficient caching
- [ ] Debounced search/filter inputs
- [ ] Lazy loading where applicable
- [ ] Optimized images and assets
- [ ] Static export capability (no Node.js runtime)

### Developer Experience
- [ ] TypeScript for type safety
- [ ] ESLint & Prettier configuration
- [ ] Consistent code structure
- [ ] Environment variable configuration
- [ ] API endpoint constants
- [ ] Custom hooks for common operations

---

## Static Export Configuration

### Next.js Config
```typescript
// next.config.mjs
import withBundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzerConfig = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default withBundleAnalyzerConfig({
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // No server-side APIs, use external backend only
  eslint: {
    ignoreDuringBuilds: true,
  },
});
```

### Build & Deploy
- Build: `next build` → generates `out/` directory
- Deploy: Static files in `out/` can be served by any web server
- No Node.js required for serving (Nginx, Apache, S3, GitHub Pages, Vercel, etc.)

---

## Environment Variables

### `.env.local`
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Tagihan WiFi
NEXT_PUBLIC_APP_VERSION=1.0.0
```

---

## Installation & Development

### Setup
```bash
# Create Next.js project
npx create-next-app@latest tagihan-wifi-frontend \
  --typescript \
  --tailwind \
  --app \
  --no-eslint \
  --no-git

cd tagihan-wifi-frontend

# Install additional dependencies
npm install \
  @tanstack/react-query \
  @tanstack/react-table \
  @tanstack/react-router \
  shadcn-ui \
  axios \
  date-fns \
  clsx \
  tailwind-merge

# Install dev dependencies
npm install -D \
  @types/node \
  typescript \
  eslint \
  prettier

# Add shadcn/ui components
npx shadcn-ui@latest init
```

### Development
```bash
npm run dev
# Open http://localhost:3000
```

### Build Static Export
```bash
npm run build
# Output in `out/` directory - ready to deploy
```

---

## Additional Notes

- **No Dynamic Routes:** Avoid `[id]` segments; use query params instead for static export
- **No API Routes:** All APIs call external backend
- **No Server Components:** Keep components in `use client` boundary for interactivity
- **Token Management:** Implement refresh token rotation or session-based auth
- **Error Boundaries:** Use React error boundaries for graceful error handling
- **Analytics:** Consider adding Vercel Analytics or similar for usage monitoring
