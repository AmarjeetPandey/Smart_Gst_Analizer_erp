from datetime import date, timedelta
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models.database import AuditLog, Branch, Customer, GSTRecord, Inventory, Invoice, InvoiceItem, Notification, Payment, Product, Purchase, PurchaseItem, User, Vendor, VendorPayment, Ledger, Transaction
from app.schemas.schemas import (
    BranchResponse,
    CustomerResponse,
    CustomerUpdate,
    InvoiceResponse,
    ProductResponse,
    ProductUpdate,
    PurchaseCreate,
    PurchaseResponse,
    ReportSummaryResponse,
    VendorResponse,
    VendorUpdate,
    InventoryAdjustmentCreate,
    VendorPaymentCreate,
    VendorPaymentResponse,
)
from app.services.accounting_service import post_entry
from app.services.gst_service import calculate_tax
from app.services.audit_service import record_audit

router = APIRouter()


class HistoryClearRequest(BaseModel):
    confirmation: str


def _owned(query, model, user_id: int):
    return query.filter(model.user_id == user_id)


def _refresh_customer_balance(db: Session, customer: Customer) -> None:
    customer.outstanding_amount = (
        db.query(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0))
        .filter(Invoice.customer_id == customer.id, Invoice.user_id == customer.user_id, Invoice.status != "paid")
        .scalar()
        or 0
    )


@router.post("/history/clear", tags=["Business History"])
def clear_business_history(
    payload: HistoryClearRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.confirmation != "CLEAR":
        raise HTTPException(status_code=400, detail='Type "CLEAR" to confirm history deletion')

    user_id = current_user.id
    invoice_ids = [row[0] for row in db.query(Invoice.id).filter(Invoice.user_id == user_id).all()]
    purchase_ids = [row[0] for row in db.query(Purchase.id).filter(Purchase.user_id == user_id).all()]
    product_ids = [row[0] for row in db.query(Product.id).filter(Product.user_id == user_id).all()]
    customer_ids = [row[0] for row in db.query(Customer.id).filter(Customer.user_id == user_id).all()]
    vendor_ids = [row[0] for row in db.query(Vendor.id).filter(Vendor.user_id == user_id).all()]
    branch_ids = [row[0] for row in db.query(Branch.id).filter(Branch.user_id == user_id).all()]
    ledger_ids = [row[0] for row in db.query(Ledger.id).filter(Ledger.user_id == user_id).all()]

    deleted = {}

    def delete_rows(model, query):
        count = query.delete(synchronize_session=False)
        deleted[model.__tablename__] = count

    delete_rows(Payment, db.query(Payment).filter(Payment.invoice_id.in_(invoice_ids)) if invoice_ids else db.query(Payment).filter(False))
    delete_rows(InvoiceItem, db.query(InvoiceItem).filter(InvoiceItem.invoice_id.in_(invoice_ids)) if invoice_ids else db.query(InvoiceItem).filter(False))
    delete_rows(VendorPayment, db.query(VendorPayment).filter(VendorPayment.purchase_id.in_(purchase_ids)) if purchase_ids else db.query(VendorPayment).filter(False))
    delete_rows(PurchaseItem, db.query(PurchaseItem).filter(PurchaseItem.purchase_id.in_(purchase_ids)) if purchase_ids else db.query(PurchaseItem).filter(False))
    inventory_filters = []
    if product_ids:
        inventory_filters.append(Inventory.product_id.in_(product_ids))
    if branch_ids:
        inventory_filters.append(Inventory.branch_id.in_(branch_ids))
    inventory_query = db.query(Inventory).filter(or_(*inventory_filters)) if inventory_filters else db.query(Inventory).filter(False)
    delete_rows(Inventory, inventory_query)
    delete_rows(GSTRecord, db.query(GSTRecord).filter(GSTRecord.user_id == user_id))
    delete_rows(Transaction, db.query(Transaction).filter((Transaction.user_id == user_id) | Transaction.ledger_id.in_(ledger_ids)))
    delete_rows(AuditLog, db.query(AuditLog).filter(AuditLog.user_id == user_id))
    delete_rows(Notification, db.query(Notification).filter(Notification.user_id == user_id))
    delete_rows(Invoice, db.query(Invoice).filter(Invoice.user_id == user_id))
    delete_rows(Purchase, db.query(Purchase).filter(Purchase.user_id == user_id))
    delete_rows(Product, db.query(Product).filter(Product.user_id == user_id))
    delete_rows(Customer, db.query(Customer).filter(Customer.user_id == user_id))
    delete_rows(Vendor, db.query(Vendor).filter(Vendor.user_id == user_id))
    delete_rows(Branch, db.query(Branch).filter(Branch.user_id == user_id))
    delete_rows(Ledger, db.query(Ledger).filter(Ledger.user_id == user_id))

    db.commit()
    return {"message": "Business history cleared successfully", "deleted": deleted}


@router.get("/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def get_customer(customer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == current_user.id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    _refresh_customer_balance(db, customer)
    db.commit()
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Customers"])
def delete_customer(customer_id: int, current_user: User = Depends(require_roles("admin", "manager", "accountant")), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == current_user.id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()


@router.put("/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def update_customer(customer_id: int, payload: CustomerUpdate, current_user: User = Depends(require_roles("admin", "manager", "operator")), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == current_user.id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def update_product(product_id: int, payload: ProductUpdate, current_user: User = Depends(require_roles("admin", "manager", "operator")), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    allowed = {"name", "sku", "barcode", "description", "category", "unit", "hsn_code", "gst_rate", "purchase_price", "selling_price", "is_active"}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key in allowed:
            setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.put("/branches/{branch_id}", response_model=BranchResponse, tags=["Branches"])
def update_branch(branch_id: int, payload: dict, current_user: User = Depends(require_roles("admin", "manager")), db: Session = Depends(get_db)):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.user_id == current_user.id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    allowed = {"name", "email", "phone", "address", "city", "state", "zip_code", "gst_number", "pan_number", "is_active"}
    for key, value in payload.items():
        if key in allowed:
            setattr(branch, key, value)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product(product_id: int, current_user: User = Depends(require_roles("admin", "manager")), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()


@router.put("/vendors/{vendor_id}", response_model=VendorResponse, tags=["Vendors"])
def update_vendor(vendor_id: int, payload: VendorUpdate, current_user: User = Depends(require_roles("admin", "manager", "accountant")), db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.user_id == current_user.id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vendor, key, value)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/purchases", response_model=List[PurchaseResponse], tags=["Purchases"])
def list_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Purchase).filter(Purchase.user_id == current_user.id).order_by(Purchase.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/vendor-payments", response_model=List[VendorPaymentResponse], tags=["Payments"])
def list_vendor_payments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(VendorPayment).join(Purchase).filter(Purchase.user_id == current_user.id).order_by(VendorPayment.created_at.desc()).all()


@router.post("/vendor-payments", response_model=VendorPaymentResponse, status_code=status.HTTP_201_CREATED, tags=["Payments"])
def record_vendor_payment(payload: VendorPaymentCreate, current_user: User = Depends(require_roles("admin", "manager", "accountant")), db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(Purchase.id == payload.purchase_id, Purchase.user_id == current_user.id).first()
    if not purchase or not purchase.vendor_id:
        raise HTTPException(status_code=404, detail="Purchase with vendor not found")
    remaining = Decimal(str(purchase.total_amount or 0)) - Decimal(str(purchase.paid_amount or 0))
    if payload.amount > remaining:
        raise HTTPException(status_code=422, detail="Payment exceeds purchase balance")
    payment = VendorPayment(purchase_id=purchase.id, vendor_id=purchase.vendor_id, amount=payload.amount, payment_date=payload.payment_date, payment_method=payload.payment_method, reference_number=payload.reference_number, notes=payload.notes)
    purchase.paid_amount = Decimal(str(purchase.paid_amount or 0)) + payload.amount
    purchase.status = "paid" if purchase.paid_amount >= purchase.total_amount else "partial"
    db.add(payment)
    db.flush()
    post_entry(db, current_user, payload.payment_date, f"Payment for purchase {purchase.purchase_number}", f"vendor-payment:{payment.id}", "vendor_payment", [
        ("Accounts Payable", "liability", payload.amount, Decimal("0")),
        ("Cash", "asset", Decimal("0"), payload.amount),
    ])
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/purchases", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED, tags=["Purchases"])
def create_purchase(
    payload: PurchaseCreate,
    current_user: User = Depends(require_roles("admin", "manager", "accountant", "operator")),
    db: Session = Depends(get_db),
):
    purchase_number = payload.purchase_number.strip()
    if not purchase_number:
        raise HTTPException(status_code=422, detail="Purchase number is required")
    if db.query(Purchase).filter(Purchase.user_id == current_user.id, Purchase.purchase_number == purchase_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Purchase number already exists")

    if payload.vendor_id is not None and not db.query(Vendor).filter(Vendor.id == payload.vendor_id, Vendor.user_id == current_user.id).first():
        raise HTTPException(status_code=404, detail="Vendor not found")

    subtotal = Decimal("0")
    total_tax = Decimal("0")
    purchase = Purchase(
        user_id=current_user.id,
        vendor_id=payload.vendor_id,
        purchase_number=purchase_number,
        purchase_date=payload.purchase_date,
        due_date=payload.due_date,
        notes=payload.notes,
        status="received",
    )
    db.add(purchase)
    db.flush()

    for item in payload.items:
        product = None
        if item.product_id is not None:
            product = db.query(Product).filter(Product.id == item.product_id, Product.user_id == current_user.id).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
        line_subtotal = Decimal(str(item.quantity)) * item.unit_price
        tax_breakdown = calculate_tax(line_subtotal, item.gst_rate, payload.seller_state, payload.place_of_supply)
        tax = tax_breakdown.total - line_subtotal
        subtotal += line_subtotal
        total_tax += tax
        db.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id if product else None,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=line_subtotal,
            gst_rate=item.gst_rate,
            tax_amount=tax,
            line_total=line_subtotal + tax,
            received_quantity=item.quantity,
        ))
        if product:
            inventory = db.query(Inventory).join(Branch).filter(
                Inventory.product_id == product.id,
                Branch.user_id == current_user.id,
            ).first()
            if not inventory:
                branch = db.query(Branch).filter(Branch.user_id == current_user.id).order_by(Branch.created_at.asc()).first()
                if not branch:
                    branch = Branch(user_id=current_user.id, name="Main Branch")
                    db.add(branch)
                    db.flush()
                inventory = Inventory(branch_id=branch.id, product_id=product.id, quantity=0)
                db.add(inventory)
            inventory.quantity += item.quantity
            product.purchase_price = item.unit_price

    purchase.subtotal = subtotal
    purchase.total_tax = total_tax
    purchase.cgst_amount = sum((calculate_tax(Decimal(str(item.quantity)) * item.unit_price, item.gst_rate, payload.seller_state, payload.place_of_supply).cgst for item in payload.items), Decimal("0"))
    purchase.sgst_amount = sum((calculate_tax(Decimal(str(item.quantity)) * item.unit_price, item.gst_rate, payload.seller_state, payload.place_of_supply).sgst for item in payload.items), Decimal("0"))
    purchase.igst_amount = sum((calculate_tax(Decimal(str(item.quantity)) * item.unit_price, item.gst_rate, payload.seller_state, payload.place_of_supply).igst for item in payload.items), Decimal("0"))
    purchase.total_amount = subtotal + total_tax
    post_entry(db, current_user, purchase.purchase_date, f"Purchase {purchase.purchase_number}", f"purchase:{purchase.id}", "purchase", [
        ("Inventory", "asset", subtotal, Decimal("0")),
        ("Input GST", "asset", total_tax, Decimal("0")),
        ("Accounts Payable", "liability", Decimal("0"), purchase.total_amount),
    ])
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/reports/summary", response_model=ReportSummaryResponse, tags=["Reports"])
def report_summary(
    period_start: date | None = None,
    period_end: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    end = period_end or date.today()
    start = period_start or (end - timedelta(days=30))
    sales = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(Invoice.user_id == current_user.id, Invoice.invoice_date.between(start, end)).scalar() or 0
    purchases = db.query(func.coalesce(func.sum(Purchase.total_amount), 0)).filter(Purchase.user_id == current_user.id, Purchase.purchase_date.between(start, end)).scalar() or 0
    tax = db.query(func.coalesce(func.sum(Invoice.total_tax), 0)).filter(Invoice.user_id == current_user.id, Invoice.invoice_date.between(start, end)).scalar() or 0
    payments = db.query(func.coalesce(func.sum(Invoice.paid_amount), 0)).filter(Invoice.user_id == current_user.id, Invoice.invoice_date.between(start, end)).scalar() or 0
    outstanding = db.query(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0)).filter(Invoice.user_id == current_user.id, Invoice.status != "paid").scalar() or 0
    return {
        "period_start": start,
        "period_end": end,
        "sales": sales,
        "purchases": purchases,
        "tax_collected": tax,
        "payments_received": payments,
        "outstanding": outstanding,
        "net_result": sales - purchases,
    }


@router.get("/reports/gst-summary", tags=["GST"])
def gst_summary(
    month: int = Query(date.today().month, ge=1, le=12),
    year: int = Query(date.today().year, ge=2000, le=2200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(
        func.coalesce(func.sum(Invoice.subtotal), 0),
        func.coalesce(func.sum(Invoice.cgst_amount), 0),
        func.coalesce(func.sum(Invoice.sgst_amount), 0),
        func.coalesce(func.sum(Invoice.igst_amount), 0),
        func.coalesce(func.sum(Invoice.total_tax), 0),
    ).filter(
        Invoice.user_id == current_user.id,
        func.extract("month", Invoice.invoice_date) == month,
        func.extract("year", Invoice.invoice_date) == year,
    ).first()
    return {"month": month, "year": year, "sales": rows[0], "cgst": rows[1], "sgst": rows[2], "igst": rows[3], "total_tax": rows[4]}


@router.get("/accounting/ledgers", tags=["Accounting"])
def list_ledgers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Ledger).filter(Ledger.user_id == current_user.id).order_by(Ledger.account_name.asc()).all()


@router.get("/accounting/trial-balance", tags=["Accounting"])
def trial_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(
        Ledger.account_name,
        Ledger.account_type,
        func.coalesce(func.sum(Transaction.debit), 0),
        func.coalesce(func.sum(Transaction.credit), 0),
    ).join(Transaction).filter(Ledger.user_id == current_user.id).group_by(Ledger.id).order_by(Ledger.account_name.asc()).all()
    total_debit = sum((Decimal(row[2]) for row in rows), Decimal("0"))
    total_credit = sum((Decimal(row[3]) for row in rows), Decimal("0"))
    return {"accounts": [{"account_name": row[0], "account_type": row[1], "debit": row[2], "credit": row[3]} for row in rows], "total_debit": total_debit, "total_credit": total_credit, "balanced": total_debit == total_credit}


@router.post("/inventory/adjust", tags=["Inventory"])
def adjust_inventory(payload: InventoryAdjustmentCreate, current_user: User = Depends(require_roles("admin", "manager", "operator")), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.user_id == current_user.id, Product.is_active.is_(True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    branch = db.query(Branch).filter(Branch.user_id == current_user.id, Branch.is_active.is_(True)).order_by(Branch.created_at.asc()).first()
    if not branch:
        branch = Branch(user_id=current_user.id, name="Main Branch")
        db.add(branch)
        db.flush()
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id, Inventory.branch_id == branch.id).first()
    if not inventory:
        inventory = Inventory(branch_id=branch.id, product_id=product.id, quantity=0)
        db.add(inventory)
        db.flush()
    new_quantity = inventory.quantity + payload.quantity_delta
    if new_quantity < 0:
        raise HTTPException(status_code=422, detail="Inventory cannot become negative")
    old_quantity = inventory.quantity
    inventory.quantity = new_quantity
    record_audit(db, current_user, "adjust", "inventory", inventory.id, {"quantity": old_quantity}, {"quantity": new_quantity, "reason": payload.reason})
    db.commit()
    return {"product_id": product.id, "branch_id": branch.id, "quantity": inventory.quantity, "reason": payload.reason}


@router.post("/invoices/{invoice_id}/cancel", response_model=InvoiceResponse, tags=["Invoices"])
def cancel_invoice(invoice_id: int, current_user: User = Depends(require_roles("admin", "manager", "accountant")), db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "cancelled":
        return invoice
    if invoice.paid_amount and invoice.paid_amount > 0:
        raise HTTPException(status_code=409, detail="Paid invoices must be refunded before cancellation")
    for item in invoice.items:
        if item.product_id:
            inventory = db.query(Inventory).join(Branch).filter(Inventory.product_id == item.product_id, Branch.user_id == current_user.id).first()
            if inventory:
                inventory.quantity += item.quantity
    previous_status = invoice.status
    invoice.status = "cancelled"
    record_audit(db, current_user, "cancel", "invoice", invoice.id, {"status": previous_status}, {"status": "cancelled"})
    post_entry(db, current_user, invoice.invoice_date, f"Cancel invoice {invoice.invoice_number}", f"invoice-reversal:{invoice.id}", "invoice_reversal", [
        ("Sales", "income", invoice.subtotal, Decimal("0")),
        ("Output CGST", "liability", invoice.cgst_amount, Decimal("0")),
        ("Output SGST", "liability", invoice.sgst_amount, Decimal("0")),
        ("Output IGST", "liability", invoice.igst_amount, Decimal("0")),
        ("Accounts Receivable", "asset", Decimal("0"), invoice.total_amount),
    ])
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/analyzer/insights", tags=["Analyzer"])
def analyzer_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.user_id == current_user.id, Invoice.status != "cancelled").all()
    products = db.query(Product).filter(Product.user_id == current_user.id, Product.is_active.is_(True)).all()
    insights = []
    outstanding = sum((Decimal(i.total_amount or 0) - Decimal(i.paid_amount or 0) for i in invoices), Decimal("0"))
    tax = sum((Decimal(i.total_tax or 0) for i in invoices), Decimal("0"))
    sales = sum((Decimal(i.total_amount or 0) for i in invoices), Decimal("0"))
    if outstanding > 0:
        insights.append({"type": "receivables", "severity": "warning", "title": "Outstanding payments need attention", "value": float(outstanding), "message": "Review customer balances and send reminders."})
    low_stock = [product.name for product in products if product.quantity <= 10]
    if low_stock:
        insights.append({"type": "inventory", "severity": "warning", "title": "Low stock detected", "value": len(low_stock), "message": f"Review reorder levels for: {', '.join(low_stock[:5])}."})
    if sales and tax / sales > Decimal("0.18"):
        insights.append({"type": "tax", "severity": "info", "title": "Tax ratio is elevated", "value": float(tax / sales), "message": "Review GST rates and place-of-supply classifications."})
    if not insights:
        insights.append({"type": "healthy", "severity": "success", "title": "Business signals look healthy", "value": 0, "message": "No immediate receivable, stock, or tax anomalies were detected."})
    return {"insights": insights, "sales": float(sales), "tax": float(tax), "outstanding": float(outstanding)}
