# SmartGST AI ERP - API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/send-otp` and `/auth/verify-otp`) require Bearer token authentication:

```
Authorization: Bearer {access_token}
```

## Rate Limiting

Default: 100 requests per hour per IP

## Response Format

All responses are JSON:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful"
}
```

---

## Authentication Endpoints

### 1. Send OTP

Send OTP to email address.

```
POST /auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200)**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "email": "user@example.com"
}
```

**Errors**
- `400` - Invalid email format
- `500` - Failed to send email

---

### 2. Verify OTP

Verify OTP and login user.

```
POST /auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "phone": "+91-9999999999",
    "role": "operator",
    "is_active": true,
    "is_email_verified": true,
    "last_login": "2024-01-15T10:30:00",
    "created_at": "2024-01-01T00:00:00"
  },
  "expires_in": 1800
}
```

**Errors**
- `401` - Invalid or expired OTP

---

### 3. Refresh Token

Get new access token using refresh token.

```
POST /auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors**
- `401` - Invalid or expired refresh token

---

## User Endpoints

### 4. Get Current User

Get authenticated user profile.

```
GET /users/me
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "User Name",
  "phone": "+91-9999999999",
  "role": "operator",
  "is_active": true,
  "is_email_verified": true,
  "created_at": "2024-01-01T00:00:00"
}
```

---

### 5. Update User Profile

Update current user profile.

```
PUT /users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Name",
  "phone": "+91-9999999999"
}
```

**Response (200)**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Updated Name",
  "phone": "+91-9999999999",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

## Branch Endpoints

### 6. List Branches

Get all branches for user.

```
GET /branches?skip=0&limit=20
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "name": "Main Branch",
      "email": "main@example.com",
      "phone": "+91-9999999999",
      "address": "123 Main Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "zip_code": "400001",
      "gst_number": "27AAFCT5055K1Z0",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

### 7. Create Branch

Create new branch.

```
POST /branches
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "New Branch",
  "email": "branch@example.com",
  "phone": "+91-9999999999",
  "address": "456 Branch Road",
  "city": "Delhi",
  "state": "Delhi",
  "zip_code": "110001",
  "gst_number": "07AAFCT5055K1Z0",
  "pan_number": "AAFCT5055K"
}
```

**Response (201)**
```json
{
  "id": 2,
  "name": "New Branch",
  "gst_number": "07AAFCT5055K1Z0",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 8. Get Branch Details

Get specific branch.

```
GET /branches/{id}
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "id": 1,
  "name": "Main Branch",
  "email": "main@example.com",
  "phone": "+91-9999999999",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "zip_code": "400001",
  "gst_number": "27AAFCT5055K1Z0",
  "pan_number": "AAFCT5055K",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### 9. Update Branch

Update branch details.

```
PUT /branches/{id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Branch Name",
  "email": "updated@example.com",
  "is_active": true
}
```

**Response (200)**
```json
{
  "id": 1,
  "name": "Updated Branch Name",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### 10. Delete Branch

Delete branch.

```
DELETE /branches/{id}
Authorization: Bearer {access_token}
```

**Response (204)** - No content

---

## Customer Endpoints

### 11. List Customers

Get all customers.

```
GET /customers?skip=0&limit=20&branch_id=1
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "total": 50,
  "items": [
    {
      "id": 1,
      "name": "Customer Name",
      "email": "customer@example.com",
      "phone": "+91-9999999999",
      "gst_number": "27AAFCT5055K1Z0",
      "address": "123 Customer Street",
      "city": "Mumbai",
      "outstanding_amount": 5000,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

### 12. Create Customer

Add new customer.

```
POST /customers
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "New Customer",
  "email": "new@example.com",
  "phone": "+91-9999999999",
  "gst_number": "27AAFCT5055K1Z0",
  "address": "Customer Address",
  "city": "Mumbai",
  "state": "Maharashtra",
  "zip_code": "400001",
  "branch_id": 1
}
```

**Response (201)**
```json
{
  "id": 2,
  "name": "New Customer",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Product Endpoints

### 13. List Products

Get all products.

```
GET /products?skip=0&limit=20&category=Electronics
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "name": "Product Name",
      "sku": "SKU001",
      "barcode": "1234567890123",
      "category": "Electronics",
      "unit": "pieces",
      "hsn_code": "8504.40",
      "gst_rate": 5,
      "purchase_price": 100,
      "selling_price": 150,
      "is_active": true
    }
  ]
}
```

---

### 14. Create Product

Add new product.

```
POST /products
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "New Product",
  "sku": "SKU002",
  "barcode": "9876543210987",
  "category": "Electronics",
  "unit": "pieces",
  "hsn_code": "8504.40",
  "gst_rate": 5,
  "purchase_price": 100,
  "selling_price": 150
}
```

---

## Invoice Endpoints

### 15. List Invoices

Get all invoices.

```
GET /invoices?skip=0&limit=20&status=unpaid
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "invoice_number": "INV-2024-001",
      "invoice_date": "2024-01-15",
      "customer_id": 1,
      "subtotal": 1000,
      "cgst_amount": 90,
      "sgst_amount": 90,
      "igst_amount": 0,
      "total_tax": 180,
      "total_amount": 1180,
      "status": "unpaid",
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

---

### 16. Create Invoice

Create new invoice.

```
POST /invoices
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer_id": 1,
  "branch_id": 1,
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "due_date": "2024-02-15",
  "items": [
    {
      "product_id": 1,
      "description": "Product 1",
      "quantity": 10,
      "unit_price": 100,
      "gst_rate": 0,
      "cgst_rate": 9,
      "sgst_rate": 9,
      "igst_rate": 0
    }
  ],
  "notes": "Payment terms: 30 days"
}
```

**Response (201)**
```json
{
  "id": 1,
  "invoice_number": "INV-2024-001",
  "total_amount": 1180,
  "status": "unpaid",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 17. Get Invoice Details

Get specific invoice.

```
GET /invoices/{id}
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "id": 1,
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "due_date": "2024-02-15",
  "customer": {
    "id": 1,
    "name": "Customer Name"
  },
  "items": [
    {
      "id": 1,
      "description": "Product 1",
      "quantity": 10,
      "unit_price": 100,
      "line_total": 1000
    }
  ],
  "total_amount": 1180,
  "status": "unpaid"
}
```

---

## GST Endpoints

### 18. Get GST Summary

Get GST summary for period.

```
GET /gst/summary?month=1&year=2024
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "month": 1,
  "year": 2024,
  "sales_cgst": 50000,
  "sales_sgst": 50000,
  "sales_igst": 0,
  "purchase_cgst": 30000,
  "purchase_sgst": 30000,
  "purchase_igst": 0,
  "itc_cgst": 30000,
  "itc_sgst": 30000,
  "itc_igst": 0,
  "net_cgst": 20000,
  "net_sgst": 20000,
  "total_gst_due": 40000
}
```

---

### 19. Get GSTR-1 Report

Get sales register (GSTR-1).

```
GET /gst/gstr-1?month=1&year=2024
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "month": 1,
  "year": 2024,
  "total_sales": 1000000,
  "cgst": 90000,
  "sgst": 90000,
  "igst": 0,
  "total_tax": 180000,
  "transactions": [...]
}
```

---

## Report Endpoints

### 20. Generate Profit & Loss Report

Get P&L statement.

```
GET /reports/profit-loss?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "revenue": 100000,
  "cost_of_goods_sold": 60000,
  "gross_profit": 40000,
  "operating_expenses": 15000,
  "net_profit": 25000
}
```

---

### 21. Generate Balance Sheet

Get balance sheet.

```
GET /reports/balance-sheet?date=2024-01-31
Authorization: Bearer {access_token}
```

**Response (200)**
```json
{
  "date": "2024-01-31",
  "assets": {
    "current_assets": 500000,
    "fixed_assets": 1000000,
    "total_assets": 1500000
  },
  "liabilities": {
    "current_liabilities": 200000,
    "long_term_liabilities": 500000,
    "total_liabilities": 700000
  },
  "equity": {
    "capital": 800000
  },
  "total_liabilities_and_equity": 1500000
}
```

---

## Payment Endpoints

### 22. Record Payment

Record customer payment.

```
POST /payments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "invoice_id": 1,
  "amount": 1180,
  "payment_date": "2024-01-20",
  "payment_method": "bank_transfer",
  "reference_number": "REF123456"
}
```

**Response (201)**
```json
{
  "id": 1,
  "invoice_id": 1,
  "amount": 1180,
  "payment_date": "2024-01-20",
  "created_at": "2024-01-20T10:30:00"
}
```

---

## Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

---

## Example: Complete Invoice Creation Flow

```bash
# 1. Send OTP
curl -X POST http://localhost:8000/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# 2. Verify OTP and get tokens
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}'

# 3. Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Customer","phone":"+91-9999999999"}'

# 4. Create product
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Product","selling_price":100}'

# 5. Create invoice
curl -X POST http://localhost:8000/api/v1/invoices \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{...invoice data...}'

# 6. Record payment
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{...payment data...}'
```

---

For more information, see the [README.md](../README.md) and [SETUP_GUIDE.md](../SETUP_GUIDE.md).
