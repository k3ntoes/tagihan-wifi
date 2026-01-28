# Frontend API Integration Guide

Complete technical documentation for integrating the Tagihan WiFi API with frontend applications.

## Table of Contents

- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [API Base Configuration](#api-base-configuration)
- [Data Models & TypeScript Interfaces](#data-models--typescript-interfaces)
- [API Endpoints Reference](#api-endpoints-reference)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Example Code](#example-code)

---

## Overview

### Base URL
```
Production: https://your-domain.com/api/v1
Development: http://localhost:8000/api/v1
```

### Authentication
- **Type:** JWT Bearer Token
- **Header:** `Authorization: Bearer {token}`
- **Token Expiry:** 24 hours (1440 minutes)
- **Storage:** Store in localStorage, sessionStorage, or secure cookie

### Content Type
- **Request:** `application/json`
- **Response:** `application/json`

### Date & Time Formats
- **Date:** ISO 8601 format `YYYY-MM-DD` (e.g., `2026-01-28`)
- **DateTime:** ISO 8601 with timezone (e.g., `2026-01-28T10:30:00`)

---

## Authentication Flow

### 1. User Registration (Admin Setup)

```typescript
// POST /api/v1/auth/register
interface RegisterRequest {
  username: string;  // min 3 chars
  password: string;  // min 6 chars
  role: "admin" | "user";
}

interface RegisterResponse {
  id: number;
  username: string;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;  // ISO datetime
}
```

**Example Request:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'securepass123',
    role: 'admin'
  })
});

const user = await response.json();
```

### 2. User Login

```typescript
// POST /api/v1/auth/login
interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;  // "bearer"
  expires_in: number;  // 86400 (24 hours in seconds)
}
```

**Example Request:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'securepass123'
  })
});

const { access_token, expires_in } = await response.json();

// Store token
localStorage.setItem('access_token', access_token);
localStorage.setItem('token_expiry', Date.now() + expires_in * 1000);
```

### 3. Get Current User

```typescript
// GET /api/v1/auth/me
interface UserResponse {
  id: number;
  username: string;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
}
```

**Example Request:**
```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: { 
    'Authorization': `Bearer ${token}`
  }
});

const user = await response.json();
```

### 4. Token Management

```javascript
// Check if token is expired
function isTokenExpired() {
  const expiry = localStorage.getItem('token_expiry');
  if (!expiry) return true;
  return Date.now() > parseInt(expiry);
}

// Logout
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token_expiry');
  // Redirect to login page
}

// Auto-refresh or redirect
if (isTokenExpired()) {
  logout();
  // Redirect to login
}
```

---

## API Base Configuration

### Axios Setup (Recommended)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor - Add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Fetch API Setup

```javascript
class ApiClient {
  constructor(baseURL = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  get(endpoint) {
    return this.request(endpoint);
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }

  delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }
}

export const api = new ApiClient();
```

---

## Data Models & TypeScript Interfaces

### User Models

```typescript
type UserRole = "admin" | "user";

interface User {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;  // ISO datetime
}

interface UserCreate {
  username: string;
  password: string;
  role: UserRole;
}

interface UserLogin {
  username: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}
```

### Package Models

```typescript
interface Package {
  id: string;             // sqid string (URL-safe)
  name: string;
  speed: number;          // Speed in Mbps
  price: number;          // Price in Rupiah
  is_active: boolean;
  created_at: string;     // ISO datetime
  updated_at: string;     // ISO datetime
}

interface PackageCreate {
  name: string;           // min 1 char, max 100 chars
  speed: number;          // must be > 0
  price: number;          // must be > 0
}

interface PackageUpdate {
  name?: string;          // optional
  speed?: number;         // optional, must be > 0 if provided
  price?: number;         // optional, must be > 0 if provided
}
```

### Customer Models

```typescript
interface Customer {
  id: string;             // sqid string (URL-safe)
  name: string;
  package_id: string | null;      // sqid of assigned package
  package_name: string | null;    // name of assigned package
  monthly_fee: number;    // In Rupiah
  created_at: string;     // ISO datetime
  updated_at: string;     // ISO datetime
}

interface CustomerCreate {
  name: string;           // min 1 char, max 100 chars
  package_id?: string;    // optional, sqid of package
  monthly_fee: number;    // must be > 0
}

interface CustomerUpdate {
  name?: string;          // optional
  package_id?: string;    // optional, sqid of package
  monthly_fee?: number;   // optional, must be > 0 if provided
}
```

### Payment Models

```typescript
interface Payment {
  id: string;                // sqid string (URL-safe)
  customer_id: string;       // sqid string
  payment_date: string;      // ISO date (YYYY-MM-DD)
  billing_month: number;     // 1-12
  billing_year: number;      // 2020-2099
  amount: number;
  created_at: string;        // ISO datetime
  updated_at: string;        // ISO datetime
}

interface PaymentCreate {
  customer_id?: string;      // sqid string (preferred)
  customer_sqid?: string;    // Deprecated, use customer_id instead
  payment_date: string;      // ISO date (YYYY-MM-DD)
  billing_month: number;     // 1-12
  billing_year: number;      // 2020-2099
  amount: number;            // must be > 0
}

interface PaymentLogParser {
  log_entry: string;         // Format: "DD-MM-YYYY customer_name"
}
```

### Billing Matrix Models

```typescript
interface PaymentByMonth {
  month: number;             // 1-12
  month_name: string;        // "January", "February", etc.
  paid: boolean;
  amount: number | null;
  payment_date: string | null;  // ISO date or null
}

interface BillingMatrixRow {
  customer_id: string;       // sqid string
  customer_name: string;
  monthly_fee: number;
  payments: PaymentByMonth[];  // Array of 12 months
  total_paid: number;
  total_expected: number;
  completion_percentage: number;  // 0-100
}

interface BillingMatrixResponse {
  year: number;
  month_names: string[];     // Array of 12 month names
  data: BillingMatrixRow[];  // Changed from 'rows' to 'data'
  meta: PaginationMeta;
}

interface BillingSummary {
  year: number;
  total_customers: number;
  total_expected: number;
  total_collected: number;
  pending: number;
  completion_percentage: number;  // 0-100
}
```

### Pagination Models

```typescript
interface PaginationMeta {
  total: number;           // Total number of items
  page: number;            // Current page number (1-indexed)
  per_page: number;        // Items per page
  total_pages: number;     // Total number of pages
  has_next: boolean;       // Whether there's a next page
  has_prev: boolean;       // Whether there's a previous page
}

interface PaginatedResponse<T> {
  data: T[];               // Array of items
  meta: PaginationMeta;    // Pagination metadata
}

// Specific paginated response types
type PaginatedPackages = PaginatedResponse<Package>;
type PaginatedCustomers = PaginatedResponse<Customer>;
type PaginatedPayments = PaginatedResponse<Payment>;
```

### Error Response

```typescript
interface ErrorResponse {
  detail: string;
  code?: string;
}
```

---

## API Endpoints Reference

### Authentication Endpoints

#### Register User
```typescript
POST /api/v1/auth/register
Body: UserCreate
Response: User (201 Created)
Auth: No
```

#### Login
```typescript
POST /api/v1/auth/login
Body: UserLogin
Response: TokenResponse (200 OK)
Auth: No
```

#### Get Current User
```typescript
GET /api/v1/auth/me
Response: User (200 OK)
Auth: Required
```

---

### Package Endpoints

#### Create Package
```typescript
POST /api/v1/packages
Body: PackageCreate
Response: Package (201 Created)
Auth: Required (Admin only)
```

#### List Packages
```typescript
GET /api/v1/packages
Query Parameters:
  - page (optional): Page number (default: 1)
  - per_page (optional): Items per page, max 100 (default: 10)
  - name (optional): Filter by name (partial match)
  - min_speed (optional): Filter by minimum speed (Mbps)
  - max_speed (optional): Filter by maximum speed (Mbps)
  - min_price (optional): Filter by minimum price
  - max_price (optional): Filter by maximum price
  - include_inactive (optional): Include inactive packages (default: false)
Response: PaginatedPackages (200 OK)
Auth: Required
```

#### Get Package by ID
```typescript
GET /api/v1/packages/{id}
Response: Package (200 OK)
Auth: Required
Errors: 404 if not found
```

#### Update Package
```typescript
PUT /api/v1/packages/{id}
Body: PackageUpdate
Response: Package (200 OK)
Auth: Required (Admin only)
Errors: 404 if not found, 400 if name already exists
```

#### Delete Package
```typescript
DELETE /api/v1/packages/{id}
Response: 204 No Content
Auth: Required (Admin only)
Errors: 404 if not found, 400 if package in use
```

---

### Customer Endpoints

#### Create Customer
```typescript
POST /api/v1/customers
Body: CustomerCreate
Response: Customer (201 Created)
Auth: Required (Admin only)
```

#### List Customers
```typescript
GET /api/v1/customers
Query Parameters:
  - page (optional): Page number (default: 1)
  - per_page (optional): Items per page, max 100 (default: 10)
  - name (optional): Filter by name (partial match)
  - package_id (optional): Filter by package ID (sqid)
Response: PaginatedCustomers (200 OK)
Auth: Required
```

#### Get Customer by ID
```typescript
GET /api/v1/customers/{id}
Response: Customer (200 OK)
Auth: Required
Errors: 404 if not found
```

#### Update Customer
```typescript
PATCH /api/v1/customers/{id}
Body: CustomerUpdate
Response: Customer (200 OK)
Auth: Required (Admin only)
Errors: 404 if not found, 400 if invalid package_id
```

#### Delete Customer
```typescript
DELETE /api/v1/customers/{id}
Response: 204 No Content
Auth: Required (Admin only)
Errors: 404 if not found
```

---

### Payment Endpoints

#### Create Payment
```typescript
POST /api/v1/payments
Body: PaymentCreate
Response: Payment (201 Created)
Auth: Required (Admin only)
Errors: 
  - 400 if invalid data
  - 404 if customer not found
  - 409 if payment already exists for month/year
```

#### List Payments
```typescript
GET /api/v1/payments
Query Parameters:
  - page (optional): Page number (default: 1)
  - per_page (optional): Items per page, max 100 (default: 10)
  - customer_id (optional): Filter by customer ID (sqid)
  - customer_sqid (optional): Deprecated, use customer_id
  - year (optional): Filter by billing year
  - month (optional): Filter by billing month (1-12)
Response: PaginatedPayments (200 OK)
Auth: Required
```

#### Parse Payment Log
```typescript
POST /api/v1/payments/parse-log
Body: PaymentLogParser
Response: Payment (201 Created)
Auth: Required (Admin only)
Errors:
  - 400 if invalid format or customer not found
  - 409 if payment already exists
```

---

### Billing Matrix Endpoints

#### Get Billing Matrix
```typescript
GET /api/v1/billing-matrix/{year}
Path Parameters:
  - year: 2020-2100
Query Parameters:
  - page (optional): Page number (default: 1)
  - per_page (optional): Items per page, max 100 (default: 10)
  - customer_id (optional): Filter by customer ID (sqid)
  - customer_name (optional): Filter by customer name (partial match)
Response: BillingMatrixResponse (200 OK)
Auth: Required
```

#### Get Billing Summary
```typescript
GET /api/v1/billing-matrix/{year}/summary
Path Parameters:
  - year: 2020-2100
Response: BillingSummary (200 OK)
Auth: Required
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid input data, validation error |
| 401 | Unauthorized | Missing/invalid token, expired token |
| 403 | Forbidden | User lacks required permissions (not admin) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate entry (e.g., payment already exists) |
| 422 | Unprocessable Entity | Validation error (Pydantic) |
| 500 | Internal Server Error | Server error, database error |

### Error Response Format

All errors return JSON with `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Error Handling Examples

#### React/TypeScript Example

```typescript
async function createCustomer(data: CustomerCreate): Promise<Customer> {
  try {
    const response = await api.post('/customers', data);
    return response;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const message = error.response?.data?.detail || 'Unknown error';
      
      switch (status) {
        case 400:
          throw new Error(`Invalid input: ${message}`);
        case 401:
          // Redirect to login
          window.location.href = '/login';
          throw new Error('Session expired');
        case 403:
          throw new Error('You do not have permission to perform this action');
        case 404:
          throw new Error('Customer not found');
        case 409:
          throw new Error('Customer already exists');
        default:
          throw new Error(`Request failed: ${message}`);
      }
    }
    throw error;
  }
}
```

#### Vue.js Example

```javascript
async function handleCreatePayment(paymentData) {
  try {
    const payment = await api.post('/payments', paymentData);
    // Success
    showSuccessNotification('Payment recorded successfully');
    return payment;
  } catch (error) {
    // Error handling
    if (error.response?.status === 409) {
      showErrorNotification('Payment already exists for this month');
    } else if (error.response?.status === 404) {
      showErrorNotification('Customer not found');
    } else {
      showErrorNotification(error.response?.data?.detail || 'Failed to record payment');
    }
    throw error;
  }
}
```

---

## Best Practices

### 1. Authentication

```typescript
// Store token securely
function storeToken(token: string, expiresIn: number) {
  const expiryTime = Date.now() + expiresIn * 1000;
  localStorage.setItem('access_token', token);
  localStorage.setItem('token_expiry', expiryTime.toString());
}

// Check auth before protected actions
function isAuthenticated(): boolean {
  const token = localStorage.getItem('access_token');
  const expiry = localStorage.getItem('token_expiry');
  
  if (!token || !expiry) return false;
  if (Date.now() > parseInt(expiry)) {
    logout();
    return false;
  }
  
  return true;
}

// Check admin role
function isAdmin(user: User): boolean {
  return user.role === 'admin';
}
```

### 2. Customer Management

```typescript
// Use the id field (which contains sqid) for URLs
function navigateToCustomer(customer: Customer) {
  router.push(`/customers/${customer.id}`);  // ✅ Correct (id is sqid)
}

// Display customer name and monthly fee
function formatMonthlyFee(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR'
  }).format(amount);
}

// When assigning package to customer
function assignPackage(customerId: string, packageId: string) {
  return api.patch(`/customers/${customerId}`, {
    package_id: packageId  // Use sqid string
  });
}
```

### 3. Payment Recording

```typescript
// Use customer_id (which is sqid) from UI
async function recordPayment(customerId: string, date: Date, amount: number) {
  const paymentData: PaymentCreate = {
    customer_id: customerId,  // sqid string
    payment_date: date.toISOString().split('T')[0],  // YYYY-MM-DD
    billing_month: date.getMonth() + 1,  // 1-12
    billing_year: date.getFullYear(),
    amount: amount
  };
  
  return await api.post('/payments', paymentData);
}

// Handle duplicate payment error
try {
  await recordPayment(customerId, new Date(), 150000);
} catch (error) {
  if (error.response?.status === 409) {
    // Show message: "Payment for this month already exists"
    // Offer to view/edit existing payment
  }
}
```

### 4. Billing Matrix Display

```typescript
// Render billing matrix with pagination
function BillingMatrixTable({ year }: { year: number }) {
  const [matrix, setMatrix] = useState<BillingMatrixResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    setLoading(true);
    api.get(`/billing-matrix/${year}?page=${page}&per_page=10`)
      .then(setMatrix)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [year, page]);
  
  if (loading || !matrix) return <Loading />;
  
  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            {matrix.month_names.map(month => (
              <th key={month}>{month.substring(0, 3)}</th>
            ))}
            <th>Total</th>
            <th>%</th>
          </tr>
        </thead>
        <tbody>
          {matrix.data.map(row => (
            <tr key={row.customer_id}>
              <td>{row.customer_name}</td>
              {row.payments.map(payment => (
                <td key={payment.month} className={payment.paid ? 'paid' : 'unpaid'}>
                  {payment.paid ? '✓' : '✗'}
                </td>
              ))}
              <td>{formatCurrency(row.total_paid)}</td>
              <td>{row.completion_percentage.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Pagination controls */}
      <div className="pagination">
        <button 
          onClick={() => setPage(p => p - 1)} 
          disabled={!matrix.meta.has_prev}
        >
          Previous
        </button>
        <span>Page {matrix.meta.page} of {matrix.meta.total_pages}</span>
        <button 
          onClick={() => setPage(p => p + 1)} 
          disabled={!matrix.meta.has_next}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

### 5. Date Handling

```typescript
// Always use ISO format for dates
function formatDateForAPI(date: Date): string {
  return date.toISOString().split('T')[0];  // YYYY-MM-DD
}

// Parse date from API
function parseAPIDate(dateString: string): Date {
  return new Date(dateString);
}

// Display formatted date
function formatDateForDisplay(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('id-ID', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date);
}
```

### 6. Pagination Handling

```typescript
// Track pagination state
const [data, setData] = useState([]);
const [meta, setMeta] = useState<PaginationMeta | null>(null);
const [page, setPage] = useState(1);
const [perPage, setPerPage] = useState(10);

async function loadData() {
  const response = await api.get(`/customers?page=${page}&per_page=${perPage}`);
  setData(response.data);
  setMeta(response.meta);
}

// Pagination controls
function PaginationControls() {
  return (
    <div>
      <button 
        onClick={() => setPage(p => p - 1)} 
        disabled={!meta?.has_prev}
      >
        Previous
      </button>
      <span>{meta?.page} / {meta?.total_pages} ({meta?.total} items)</span>
      <button 
        onClick={() => setPage(p => p + 1)} 
        disabled={!meta?.has_next}
      >
        Next
      </button>
    </div>
  );
}
```

### 7. Loading States

```typescript
// Track loading state
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

async function loadCustomers() {
  setLoading(true);
  setError(null);
  
  try {
    const response = await api.get('/customers');
    setCustomers(response.data);  // Access data field
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}
```

---

## Example Code

### Complete React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import { api } from './api-client';

interface Customer {
  id: string;             // sqid
  name: string;
  package_id: string | null;
  package_name: string | null;
  monthly_fee: number;
  created_at: string;
  updated_at: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

function CustomerList() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCustomers();
  }, [page]);

  async function loadCustomers() {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/customers?page=${page}&per_page=10`);
      setCustomers(response.data);
      setMeta(response.meta);
    } catch (err: any) {
      setError(err.message || 'Failed to load customers');
    } finally {
      setLoading(false);
    }
  }

  async function deleteCustomer(id: string) {
    if (!confirm('Are you sure you want to delete this customer?')) {
      return;
    }

    try {
      await api.delete(`/customers/${id}`);
      await loadCustomers(); // Reload list
    } catch (err: any) {
      alert(`Failed to delete customer: ${err.message}`);
    }
  }

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Customers</h1>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Package</th>
            <th>Monthly Fee</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {customers.map(customer => (
            <tr key={customer.id}>
              <td>{customer.name}</td>
              <td>{customer.package_name || '-'}</td>
              <td>
                {new Intl.NumberFormat('id-ID', {
                  style: 'currency',
                  currency: 'IDR'
                }).format(customer.monthly_fee)}
              </td>
              <td>
                <button onClick={() => {
                  window.location.href = `/customers/${customer.id}`;
                }}>
                  View
                </button>
                <button onClick={() => deleteCustomer(customer.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Pagination */}
      {meta && (
        <div className="pagination">
          <button 
            onClick={() => setPage(p => p - 1)} 
            disabled={!meta.has_prev}
          >
            Previous
          </button>
          <span>Page {meta.page} of {meta.total_pages} ({meta.total} total)</span>
          <button 
            onClick={() => setPage(p => p + 1)} 
            disabled={!meta.has_next}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default CustomerList;
```

### Vue 3 Composition API Example

```vue
<template>
  <div>
    <h1>Billing Matrix {{ year }}</h1>
    
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    
    <div v-else>
      <table class="billing-matrix">
        <thead>
          <tr>
            <th>Customer</th>
            <th v-for="month in matrix?.month_names" :key="month">
              {{ month.substring(0, 3) }}
            </th>
            <th>Total</th>
            <th>%</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in matrix?.data" :key="row.customer_id">
            <td>{{ row.customer_name }}</td>
            <td 
              v-for="payment in row.payments" 
              :key="payment.month"
              :class="{ paid: payment.paid, unpaid: !payment.paid }"
            >
              {{ payment.paid ? '✓' : '✗' }}
            </td>
            <td>{{ formatCurrency(row.total_paid) }}</td>
            <td>{{ row.completion_percentage.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
      
      <!-- Pagination -->
      <div v-if="matrix?.meta" class="pagination">
        <button @click="page--" :disabled="!matrix.meta.has_prev">Previous</button>
        <span>Page {{ matrix.meta.page }} of {{ matrix.meta.total_pages }}</span>
        <button @click="page++" :disabled="!matrix.meta.has_next">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from './api-client';

interface BillingMatrixResponse {
  year: number;
  month_names: string[];
  data: any[];
  meta: PaginationMeta;
}

interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

const props = defineProps<{ year: number }>();

const matrix = ref<BillingMatrixResponse | null>(null);
const page = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);

watch([() => props.year, page], async () => {
  try {
    loading.value = true;
    error.value = null;
    matrix.value = await api.get(
      `/billing-matrix/${props.year}?page=${page.value}&per_page=10`
    );
  } catch (err: any) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}, { immediate: true });

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR'
  }).format(amount);
}
</script>

<style scoped>
.billing-matrix {
  width: 100%;
  border-collapse: collapse;
}

.billing-matrix th,
.billing-matrix td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.paid {
  background-color: #d4edda;
  color: #155724;
}

.unpaid {
  background-color: #f8d7da;
  color: #721c24;
}
</style>
```

### Payment Form Example (React)

```typescript
import React, { useState, useEffect } from 'react';
import { api } from './api-client';

interface PaymentFormProps {
  onSuccess?: () => void;
}

function PaymentForm({ onSuccess }: PaymentFormProps) {
  const [customers, setCustomers] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    customer_id: '',
    payment_date: new Date().toISOString().split('T')[0],
    billing_month: new Date().getMonth() + 1,
    billing_year: new Date().getFullYear(),
    amount: 0
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/customers').then(setCustomers);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await api.post('/payments', formData);
      alert('Payment recorded successfully');
      onSuccess?.();
      // Reset form
      setFormData({
        ...formData,
        amount: 0
      });
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('Payment already exists for this customer and month');
      } else {
        setError(err.message || 'Failed to record payment');
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleCustomerChange(id: string) {
    const customer = customers.find(c => c.id === id);
    setFormData({
      ...formData,
      customer_id: id,
      amount: customer?.monthly_fee || 0
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Record Payment</h2>
      
      {error && <div className="error">{error}</div>}
      
      <div>
        <label>Customer:</label>
        <select
          value={formData.customer_id}
          onChange={(e) => handleCustomerChange(e.target.value)}
          required
        >
          <option value="">Select customer</option>
          {customers.map(customer => (
            <option key={customer.id} value={customer.id}>
              {customer.name} - Rp {customer.monthly_fee.toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Payment Date:</label>
        <input
          type="date"
          value={formData.payment_date}
          onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
          required
        />
      </div>

      <div>
        <label>Billing Month:</label>
        <select
          value={formData.billing_month}
          onChange={(e) => setFormData({ ...formData, billing_month: parseInt(e.target.value) })}
          required
        >
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i + 1} value={i + 1}>
              {new Date(2000, i).toLocaleString('default', { month: 'long' })}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Billing Year:</label>
        <input
          type="number"
          value={formData.billing_year}
          onChange={(e) => setFormData({ ...formData, billing_year: parseInt(e.target.value) })}
          min={2020}
          max={2100}
          required
        />
      </div>

      <div>
        <label>Amount:</label>
        <input
          type="number"
          value={formData.amount}
          onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value) })}
          min={1}
          required
        />
      </div>

      <button type="submit" disabled={submitting}>
        {submitting ? 'Recording...' : 'Record Payment'}
      </button>
    </form>
  );
}

export default PaymentForm;
```

---

## Testing the API

### Using cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# List customers
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/customers

# Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","monthly_fee":150000}'

# Get billing matrix
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/billing-matrix/2026
```

### Using HTTPie

```bash
# Login
http POST localhost:8000/api/v1/auth/login username=admin password=admin123

# Save token
TOKEN="your-token-here"

# List customers
http localhost:8000/api/v1/customers "Authorization: Bearer $TOKEN"

# Create payment
http POST localhost:8000/api/v1/payments \
  "Authorization: Bearer $TOKEN" \
  customer_sqid=abc123 \
  payment_date=2026-01-28 \
  billing_month:=1 \
  billing_year:=2026 \
  amount:=150000
```

---

## Additional Resources

- **Interactive API Docs:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **ReDoc:** http://localhost:8000/redoc

For backend setup and configuration, see [README.md](README.md).
