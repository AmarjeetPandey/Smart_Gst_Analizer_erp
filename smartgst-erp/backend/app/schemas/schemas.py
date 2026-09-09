from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ========================
# User Schemas
# ========================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# Authentication Schemas
# ========================

class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    code: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ========================
# Branch Schemas
# ========================

class BranchBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# Customer Schemas
# ========================

class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(default=0)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    credit_limit: Optional[Decimal] = None


class CustomerResponse(CustomerBase):
    id: int
    user_id: int
    branch_id: Optional[int]
    outstanding_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# Product Schemas
# ========================

class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str = "pieces"
    hsn_code: Optional[str] = None
    gst_rate: float = 0
    purchase_price: Decimal
    selling_price: Decimal
    quantity: Optional[float] = Field(default=0)
    sales_quantity: Optional[float] = Field(default=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    quantity: Optional[float] = None
    sales_quantity: Optional[float] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# Invoice Schemas
# ========================

class InvoiceItemCreate(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float
    unit_price: Decimal
    gst_rate: float = 0
    cgst_rate: float = 0
    sgst_rate: float = 0
    igst_rate: float = 0


class InvoiceCreate(BaseModel):
    customer_id: Optional[int] = None
    branch_id: Optional[int] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    items: List[InvoiceItemCreate]
    notes: Optional[str] = None
    paid_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    sku: Optional[str] = None
    payment_proof_data: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    subtotal: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    status: str
    notes: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    total_sales: Decimal
    outstanding: Decimal
    total_purchases: Decimal
    total_profit_loss: Decimal
    total_products: int
    total_customers: int
    recent_invoices: List[InvoiceResponse]


# ========================
# Payment Schemas
# ========================

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    customer_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# GST Schemas
# ========================

class GSTRecordResponse(BaseModel):
    id: int
    transaction_type: str
    transaction_date: date
    gst_number: str
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    net_tax: Decimal
    month: int
    year: int
    
    class Config:
        from_attributes = True


# ========================
# Pagination
# ========================

class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List
