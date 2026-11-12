from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Index, JSON, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.OPERATOR)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    otp_records = relationship("OTP", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="user", cascade="all, delete-orphan")
    gst_records = relationship("GSTRecord", back_populates="user", cascade="all, delete-orphan")
    ledgers = relationship("Ledger", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class OTP(Base):
    """OTP model for email verification"""
    __tablename__ = "otp"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False, default="")
    code_hash = Column(String(64), nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", back_populates="otp_records")


class UserSession(Base):
    """User session management"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    token = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", back_populates="sessions")


class Branch(Base):
    """Branch/Shop model"""
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    state_code = Column(String(10), nullable=True)
    zip_code = Column(String(20), nullable=True)
    gst_number = Column(String(15), unique=True, nullable=True, index=True)
    pan_number = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="branches")
    customers = relationship("Customer", back_populates="branch", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="branch", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="branch", cascade="all, delete-orphan")


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False)
    gst_number = Column(String(15), nullable=True, index=True)
    pan_number = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    credit_limit = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="customers")
    branch = relationship("Branch", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")


class Vendor(Base):
    """Vendor model"""
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False)
    gst_number = Column(String(15), nullable=True, index=True)
    pan_number = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    payment_terms = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="vendors")
    purchases = relationship("Purchase", back_populates="vendor", cascade="all, delete-orphan")
    vendor_payments = relationship("VendorPayment", back_populates="vendor", cascade="all, delete-orphan")


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    __table_args__ = (
        Index("uq_products_user_sku", "user_id", "sku", unique=True),
        Index("uq_products_user_barcode", "user_id", "barcode", unique=True),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True)
    barcode = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=False, default="pieces")
    hsn_code = Column(String(10), nullable=True)
    gst_rate = Column(Float, default=0)
    purchase_price = Column(Numeric(15, 2), nullable=False)
    selling_price = Column(Numeric(15, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="product", cascade="all, delete-orphan")
    purchase_items = relationship("PurchaseItem", back_populates="product", cascade="all, delete-orphan")

    @property
    def quantity(self):
        if self.inventory:
            inventory_entry = self.inventory[0] if isinstance(self.inventory, list) else self.inventory
            return float(inventory_entry.quantity or 0)
        return 0


class Inventory(Base):
    """Inventory/Stock model"""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Float, default=0)
    min_stock_level = Column(Float, default=10)
    reorder_level = Column(Float, default=20)
    reorder_quantity = Column(Float, default=100)
    last_stock_check = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    branch = relationship("Branch", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")


class Invoice(Base):
    """Invoice model"""
    __tablename__ = "invoices"
    __table_args__ = (
        Index("uq_invoices_user_invoice_number", "user_id", "invoice_number", unique=True),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(100), nullable=False)
    shop_name = Column(String(255), nullable=True)
    discount_amount = Column(Numeric(15, 2), default=0)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(15, 2), default=0)
    cgst_amount = Column(Numeric(15, 2), default=0)
    sgst_amount = Column(Numeric(15, 2), default=0)
    igst_amount = Column(Numeric(15, 2), default=0)
    total_tax = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    paid_amount = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="unpaid")  # unpaid, partially_paid, paid, cancelled
    notes = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="invoices")
    branch = relationship("Branch", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    gst_records = relationship("GSTRecord", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """Invoice items model"""
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    gst_rate = Column(Float, default=0)
    cgst_rate = Column(Float, default=0)
    sgst_rate = Column(Float, default=0)
    igst_rate = Column(Float, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")


class Purchase(Base):
    """Purchase order model"""
    __tablename__ = "purchases"
    __table_args__ = (
        Index("uq_purchases_user_purchase_number", "user_id", "purchase_number", unique=True),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    purchase_number = Column(String(100), nullable=False)
    purchase_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(15, 2), default=0)
    cgst_amount = Column(Numeric(15, 2), default=0)
    sgst_amount = Column(Numeric(15, 2), default=0)
    igst_amount = Column(Numeric(15, 2), default=0)
    total_tax = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    paid_amount = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="pending")  # pending, received, partial, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="purchases", foreign_keys=[user_id])
    vendor = relationship("Vendor", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    vendor_payments = relationship("VendorPayment", back_populates="purchase", cascade="all, delete-orphan")


# Add this relationship to User model after defining Purchase
User.purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan", foreign_keys=[Purchase.user_id])


class PurchaseItem(Base):
    """Purchase items model"""
    __tablename__ = "purchase_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    gst_rate = Column(Float, default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)
    received_quantity = Column(Float, default=0)
    
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")


class Payment(Base):
    """Customer payment model"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, bank_transfer, cheque, credit_card, upi
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")


class VendorPayment(Base):
    """Vendor payment model"""
    __tablename__ = "vendor_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    purchase = relationship("Purchase", back_populates="vendor_payments")
    vendor = relationship("Vendor", back_populates="vendor_payments")


class GSTRecord(Base):
    """GST record model"""
    __tablename__ = "gst_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    transaction_type = Column(String(20), nullable=False)  # sales, purchase
    transaction_date = Column(Date, nullable=False)
    gst_number = Column(String(15), nullable=False)
    cgst_amount = Column(Numeric(15, 2), default=0)
    sgst_amount = Column(Numeric(15, 2), default=0)
    igst_amount = Column(Numeric(15, 2), default=0)
    itc_cgst = Column(Numeric(15, 2), default=0)
    itc_sgst = Column(Numeric(15, 2), default=0)
    itc_igst = Column(Numeric(15, 2), default=0)
    net_tax = Column(Numeric(15, 2), default=0)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="gst_records")
    invoice = relationship("Invoice", back_populates="gst_records")


class Ledger(Base):
    """Ledger model"""
    __tablename__ = "ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset, liability, equity, income, expense
    opening_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="ledgers")
    transactions = relationship("Transaction", back_populates="ledger", cascade="all, delete-orphan")


class Transaction(Base):
    """Transaction model"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ledger_id = Column(Integer, ForeignKey("ledgers.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    reference_id = Column(String(100), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # invoice, purchase, payment, journal entry
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    ledger = relationship("Ledger", back_populates="transactions")


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False)  # payment_due, low_stock, payment_alert, report_ready
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
