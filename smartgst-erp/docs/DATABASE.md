# SmartGST AI ERP - Database Schema Documentation

## Overview

The database uses PostgreSQL for data persistence. All tables are managed through SQLAlchemy ORM with proper relationships and constraints.

## Database Configuration

```
Name: smartgst_db
User: postgres (default)
Port: 5432
Driver: psycopg2
Connection String: postgresql://user:password@localhost:5432/smartgst_db
```

## Core Tables

### users

Stores user account information and authentication details.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin','manager','accountant','operator','viewer'),
    is_active BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    last_login_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Fields:**
- `id` - Primary key
- `email` - Unique email address
- `name` - User full name
- `phone` - Contact phone number
- `role` - User role (6 levels)
- `is_active` - Account status
- `is_email_verified` - Email verification flag
- `last_login` - Last login timestamp
- `last_login_ip` - Last login IP address

**Relationships:**
- One-to-many: OTP records
- One-to-many: User sessions
- One-to-many: Customers
- One-to-many: Vendors
- One-to-many: Branches
- One-to-many: Products
- One-to-many: Invoices
- One-to-many: Purchases
- One-to-many: Ledgers
- One-to-many: GST records
- One-to-many: Transactions
- One-to-many: Audit logs

---

### otp

Stores OTP records for email verification.

```sql
CREATE TABLE otp (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_otp_user_id ON otp(user_id);
CREATE INDEX idx_otp_email ON otp(email);
```

**Fields:**
- `id` - Primary key
- `user_id` - Foreign key to users
- `email` - Email address
- `code` - 6-digit OTP
- `is_used` - Used/unused flag
- `expires_at` - Expiration time

**TTL:** Default 10 minutes
**Auto-cleanup:** Old used OTPs auto-deleted after 30 days

---

### user_sessions

Manages multi-device login sessions.

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    ip_address VARCHAR(50),
    user_agent TEXT,
    token TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
```

**Features:**
- Multiple concurrent sessions per user
- Device tracking
- IP address logging
- Last activity tracking
- Automatic expiration

---

## Location Tables

### branches

Stores shop/warehouse/branch locations.

```sql
CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    gst_number VARCHAR(15) UNIQUE,
    pan_number VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_branches_user_id ON branches(user_id);
CREATE INDEX idx_branches_gst ON branches(gst_number);
```

**Features:**
- Multiple branches per user
- GST number per branch
- Independent inventory
- Branch-wise reporting

---

## Customer & Vendor Tables

### customers

Stores customer information.

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    gst_number VARCHAR(15),
    pan_number VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    credit_limit NUMERIC(15, 2) DEFAULT 0,
    outstanding_amount NUMERIC(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_gst ON customers(gst_number);
```

**Relationships:**
- Many-to-one: Invoices
- Many-to-one: Payments

---

### vendors

Stores vendor information.

```sql
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    gst_number VARCHAR(15),
    pan_number VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    payment_terms VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendors_user_id ON vendors(user_id);
CREATE INDEX idx_vendors_gst ON vendors(gst_number);
```

---

## Product & Inventory Tables

### products

Stores product master data.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    barcode VARCHAR(255) UNIQUE,
    description TEXT,
    category VARCHAR(255),
    unit VARCHAR(50) NOT NULL DEFAULT 'pieces',
    hsn_code VARCHAR(10),
    gst_rate FLOAT DEFAULT 0,
    purchase_price NUMERIC(15, 2) NOT NULL,
    selling_price NUMERIC(15, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_category ON products(category);
```

**Features:**
- SKU and barcode support
- HSN code for tax classification
- GST rate per product
- Separate purchase and selling price

---

### inventory

Tracks stock levels per product per branch.

```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity FLOAT DEFAULT 0,
    min_stock_level FLOAT DEFAULT 10,
    reorder_level FLOAT DEFAULT 20,
    reorder_quantity FLOAT DEFAULT 100,
    last_stock_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(branch_id, product_id)
);

CREATE INDEX idx_inventory_branch ON inventory(branch_id);
CREATE INDEX idx_inventory_product ON inventory(product_id);
```

**Features:**
- Real-time stock tracking
- Low stock alerts
- Reorder point management
- Per-branch inventory

---

## Transaction Tables

### invoices

Stores sales invoice headers.

```sql
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE,
    subtotal NUMERIC(15, 2) DEFAULT 0,
    cgst_amount NUMERIC(15, 2) DEFAULT 0,
    sgst_amount NUMERIC(15, 2) DEFAULT 0,
    igst_amount NUMERIC(15, 2) DEFAULT 0,
    total_tax NUMERIC(15, 2) DEFAULT 0,
    total_amount NUMERIC(15, 2) DEFAULT 0,
    paid_amount NUMERIC(15, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'unpaid',
    notes TEXT,
    file_path VARCHAR(500),
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);
```

**Status Values:**
- `unpaid` - Not yet paid
- `partially_paid` - Partial payment received
- `paid` - Fully paid
- `cancelled` - Cancelled

---

### invoice_items

Line items for invoices.

```sql
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    description VARCHAR(500) NOT NULL,
    quantity FLOAT NOT NULL,
    unit_price NUMERIC(15, 2) NOT NULL,
    subtotal NUMERIC(15, 2) NOT NULL,
    gst_rate FLOAT DEFAULT 0,
    cgst_rate FLOAT DEFAULT 0,
    sgst_rate FLOAT DEFAULT 0,
    igst_rate FLOAT DEFAULT 0,
    tax_amount NUMERIC(15, 2) DEFAULT 0,
    line_total NUMERIC(15, 2) NOT NULL
);

CREATE INDEX idx_invoice_items_invoice ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_product ON invoice_items(product_id);
```

---

### purchases

Purchase order headers.

```sql
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
    purchase_number VARCHAR(100) UNIQUE NOT NULL,
    purchase_date DATE NOT NULL,
    due_date DATE,
    subtotal NUMERIC(15, 2) DEFAULT 0,
    cgst_amount NUMERIC(15, 2) DEFAULT 0,
    sgst_amount NUMERIC(15, 2) DEFAULT 0,
    igst_amount NUMERIC(15, 2) DEFAULT 0,
    total_tax NUMERIC(15, 2) DEFAULT 0,
    total_amount NUMERIC(15, 2) DEFAULT 0,
    paid_amount NUMERIC(15, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_purchases_user_id ON purchases(user_id);
CREATE INDEX idx_purchases_vendor ON purchases(vendor_id);
CREATE INDEX idx_purchases_status ON purchases(status);
```

---

## Financial Tables

### ledgers

Chart of accounts.

```sql
CREATE TABLE ledgers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    opening_balance NUMERIC(15, 2) DEFAULT 0,
    current_balance NUMERIC(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ledgers_user_id ON ledgers(user_id);
```

**Account Types:**
- `asset` - Assets
- `liability` - Liabilities
- `equity` - Equity
- `income` - Income
- `expense` - Expenses

---

### transactions

Journal entries and ledger postings.

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ledger_id INTEGER NOT NULL REFERENCES ledgers(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    debit NUMERIC(15, 2) DEFAULT 0,
    credit NUMERIC(15, 2) DEFAULT 0,
    balance NUMERIC(15, 2) DEFAULT 0,
    reference_id VARCHAR(100),
    transaction_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_ledger ON transactions(ledger_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
```

---

## GST Tables

### gst_records

GST tracking and compliance.

```sql
CREATE TABLE gst_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
    transaction_type VARCHAR(20) NOT NULL,
    transaction_date DATE NOT NULL,
    gst_number VARCHAR(15) NOT NULL,
    cgst_amount NUMERIC(15, 2) DEFAULT 0,
    sgst_amount NUMERIC(15, 2) DEFAULT 0,
    igst_amount NUMERIC(15, 2) DEFAULT 0,
    itc_cgst NUMERIC(15, 2) DEFAULT 0,
    itc_sgst NUMERIC(15, 2) DEFAULT 0,
    itc_igst NUMERIC(15, 2) DEFAULT 0,
    net_tax NUMERIC(15, 2) DEFAULT 0,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gst_records_user_id ON gst_records(user_id);
CREATE INDEX idx_gst_records_month_year ON gst_records(month, year);
CREATE INDEX idx_gst_records_gst ON gst_records(gst_number);
```

---

## Audit & Logging

### audit_logs

Complete audit trail.

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);
```

---

### notifications

System notifications.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    reference_id INTEGER,
    reference_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
```

---

## Relationships Diagram

```
users (1) ─── (M) otp
       │
       ├─── (M) user_sessions
       ├─── (M) branches ─── (M) customers
       ├─── (M) customers ─── (M) invoices
       ├─── (M) invoices ─── (M) invoice_items ─── products
       ├─── (M) vendors ─── (M) purchases
       ├─── (M) purchases ─── (M) purchase_items
       ├─── (M) ledgers ─── (M) transactions
       ├─── (M) gst_records
       ├─── (M) payments
       ├─── (M) audit_logs
       └─── (M) notifications
```

---

## Constraints & Rules

1. **Email Unique** - One email per user
2. **Cascading Deletes** - Delete user deletes all related data
3. **GST Number Unique** - One GST number per branch
4. **Invoice Number Unique** - One invoice number per user
5. **Product SKU Unique** - One SKU per product
6. **Not Null Constraints** - On critical fields
7. **Default Values** - Automatic values for timestamps
8. **Indexes** - On frequently queried columns

---

## Performance Optimization

1. **Composite Indexes** - On (user_id, created_at)
2. **Partial Indexes** - On active/status fields
3. **Partitioning** - By user_id for large tables
4. **Query Optimization** - Lazy loading relationships
5. **Connection Pooling** - SQLAlchemy pool_size=20

---

## Backup & Recovery

**Recommended Backup Strategy:**

```bash
# Full backup
pg_dump smartgst_db > backup_$(date +%Y%m%d).sql

# Incremental backup
pg_dump --incremental smartgst_db

# Restore
psql smartgst_db < backup_20240115.sql
```

**Backup Schedule:**
- Daily incremental backups
- Weekly full backups
- Monthly archive backups
- Store in multiple locations

---

For more information, see [README.md](../README.md) and [API.md](./API.md).
