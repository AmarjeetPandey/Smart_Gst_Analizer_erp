import base64
import os
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.database import Branch, Customer, Inventory, Invoice, InvoiceItem, Product, Purchase, PurchaseItem, User
from app.schemas.schemas import (
    CustomerCreate,
    CustomerResponse,
    DashboardSummaryResponse,
    InvoiceCreate,
    InvoiceResponse,
    ProductCreate,
    ProductResponse,
)
from app.services.email_service import EmailService
from app.utils.invoice_pdf import generate_invoice_pdf

router = APIRouter()


def _get_or_create_branch(db: Session, current_user: User) -> Branch:
    branch = (
        db.query(Branch)
        .filter(Branch.user_id == current_user.id)
        .order_by(Branch.created_at.asc())
        .first()
    )
    if branch:
        return branch

    branch = Branch(user_id=current_user.id, name="Main Branch")
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def _get_or_create_inventory(db: Session, current_user: User, product: Product, branch_id: int | None) -> Inventory:
    branch = None
    if branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == branch_id, Branch.user_id == current_user.id).first()

    if branch is None:
        branch = _get_or_create_branch(db, current_user)

    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.id, Inventory.branch_id == branch.id)
        .first()
    )
    if inventory is None:
        inventory = Inventory(branch_id=branch.id, product_id=product.id, quantity=0)
        db.add(inventory)
        db.flush()

    return inventory


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse, tags=["Dashboard"])
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_sales = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
        .filter(Invoice.user_id == current_user.id)
        .scalar()
        or 0
    )

    outstanding = (
        db.query(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0))
        .filter(Invoice.user_id == current_user.id)
        .filter(Invoice.status != "paid")
        .scalar()
        or 0
    )

    total_purchases = (
        db.query(func.coalesce(func.sum(Purchase.total_amount), 0))
        .filter(Purchase.user_id == current_user.id)
        .scalar()
        or 0
    )

    total_profit_loss = total_sales - total_purchases

    total_products = db.query(Product).filter(Product.user_id == current_user.id).count()
    total_customers = db.query(Customer).filter(Customer.user_id == current_user.id).count()

    recent_invoices = (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_sales": float(total_sales),
        "outstanding": float(outstanding),
        "total_purchases": float(total_purchases),
        "total_profit_loss": float(total_profit_loss),
        "total_products": total_products,
        "total_customers": total_customers,
        "recent_invoices": recent_invoices,
    }


@router.get("/customers", response_model=List[CustomerResponse], tags=["Customers"])
def list_customers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .order_by(Customer.created_at.desc())
        .all()
    )


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, tags=["Customers"])
def create_customer(
    payload: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = Customer(
        user_id=current_user.id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        gst_number=payload.gst_number,
        pan_number=payload.pan_number,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        zip_code=payload.zip_code,
        credit_limit=payload.credit_limit or 0,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/products", response_model=List[ProductResponse], tags=["Products"])
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )

    for product in products:
        sales_quantity = (
            db.query(func.coalesce(func.sum(InvoiceItem.quantity), 0))
            .join(Invoice)
            .filter(InvoiceItem.product_id == product.id, Invoice.user_id == current_user.id)
            .scalar()
            or 0
        )
        setattr(product, "sales_quantity", float(sales_quantity))

    return products


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = Product(
        user_id=current_user.id,
        name=payload.name,
        sku=payload.sku,
        barcode=payload.barcode,
        description=payload.description,
        category=payload.category,
        unit=payload.unit,
        hsn_code=payload.hsn_code,
        gst_rate=payload.gst_rate,
        purchase_price=payload.purchase_price,
        selling_price=payload.selling_price,
    )
    db.add(product)
    db.flush()

    inventory = _get_or_create_inventory(db, current_user, product, None)
    inventory.quantity = float(payload.quantity or 0)

    db.commit()
    db.refresh(product)
    return product


@router.get("/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
def list_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
def create_invoice(
    payload: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.user_id == current_user.id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    subtotal = 0
    cgst_amount = 0
    sgst_amount = 0
    igst_amount = 0
    total_tax = 0

    for item in payload.items:
        line_subtotal = item.quantity * float(item.unit_price)
        subtotal += line_subtotal
        tax_amount = line_subtotal * (item.gst_rate / 100)
        total_tax += tax_amount
        cgst_amount += tax_amount / 2
        sgst_amount += tax_amount / 2

    total_amount = subtotal + total_tax
    paid_amount = payload.paid_amount if payload.paid_amount is not None else 0
    remaining_amount = payload.remaining_amount if payload.remaining_amount is not None else max(total_amount - paid_amount, 0)
    if remaining_amount < 0:
        remaining_amount = 0

    status = "paid" if remaining_amount <= 0 else "partially_paid" if paid_amount > 0 else "unpaid"

    invoice = Invoice(
        user_id=current_user.id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=subtotal,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        total_tax=total_tax,
        total_amount=total_amount,
        paid_amount=paid_amount,
        status=status,
        notes=payload.notes,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    for item in payload.items:
        resolved_product = None
        if item.product_id is not None:
            resolved_product = (
                db.query(Product)
                .filter(Product.id == item.product_id, Product.user_id == current_user.id)
                .first()
            )
        elif payload.sku:
            resolved_product = (
                db.query(Product)
                .filter(Product.user_id == current_user.id, Product.sku == payload.sku)
                .first()
            )

        if resolved_product is not None:
            inventory = _get_or_create_inventory(db, current_user, resolved_product, payload.branch_id)
            if inventory.quantity < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient stock for {resolved_product.name}")
            inventory.quantity -= item.quantity

        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=resolved_product.id if resolved_product is not None else None,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.quantity * float(item.unit_price),
            gst_rate=item.gst_rate,
            cgst_rate=item.gst_rate / 2,
            sgst_rate=item.gst_rate / 2,
            igst_rate=0,
            tax_amount=(item.quantity * float(item.unit_price)) * (item.gst_rate / 100),
            line_total=(item.quantity * float(item.unit_price)) * (1 + (item.gst_rate / 100)),
        )
        db.add(invoice_item)

    uploads_dir = Path("./uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if payload.payment_proof_data:
        file_name = f"invoice_{invoice.invoice_number}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
        file_path = uploads_dir / file_name
        proof_bytes = base64.b64decode(payload.payment_proof_data.split(",", 1)[1])
        file_path.write_bytes(proof_bytes)
        invoice.file_path = f"/uploads/{file_name}"

    if payload.sku or payload.items:
        first_item = payload.items[0] if payload.items else None
        item_description = first_item.description if first_item else "Invoice Item"
        customer_name = ""
        customer = None
        if payload.customer_id is not None:
            customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.user_id == current_user.id).first()
            if customer:
                customer_name = customer.name
        invoice_pdf_path = generate_invoice_pdf(
            str(uploads_dir / f"invoice_{invoice.invoice_number}.pdf"),
            invoice.invoice_number,
            customer_name,
            str(invoice.invoice_date),
            str(invoice.due_date) if invoice.due_date else None,
            item_description,
            payload.sku,
            first_item.quantity if first_item else 0,
            first_item.unit_price if first_item else 0,
            first_item.gst_rate if first_item else 0,
            invoice.subtotal,
            invoice.total_tax,
            invoice.total_amount,
            invoice.paid_amount,
            remaining_amount,
        )
        invoice.file_path = str(uploads_dir / f"invoice_{invoice.invoice_number}.pdf")

        if customer and customer.email:
            EmailService.send_invoice_pdf_email(customer.email, customer.name, invoice.invoice_number, invoice_pdf_path)

    db.commit()
    db.refresh(invoice)
    return invoice
