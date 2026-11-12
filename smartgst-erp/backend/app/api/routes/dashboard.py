import base64
import binascii
import mimetypes
import re
from decimal import Decimal
from pathlib import Path
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.core.config import get_settings
from app.models.database import Branch, Customer, Inventory, Invoice, InvoiceItem, Payment, Product, Purchase, PurchaseItem, User, Vendor
from app.schemas.schemas import (
    CustomerCreate,
    CustomerResponse,
    DashboardSummaryResponse,
    BranchCreate,
    BranchResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    ProductCreate,
    ProductResponse,
    VendorCreate,
    VendorResponse,
)
from app.services.email_service import EmailService
from app.services.accounting_service import post_entry
from app.services.gst_service import calculate_tax
from app.utils.invoice_pdf import generate_invoice_pdf
from app.utils.invoice_excel import generate_invoice_excel

router = APIRouter()
settings = get_settings()


class InvoiceEmailRequest(BaseModel):
    recipient_email: EmailStr | None = None
    payment_proof_expected: bool = False


def _next_invoice_number(db: Session, user_id: int) -> str | None:
    first_invoice = (
        db.query(Invoice)
        .filter(Invoice.user_id == user_id)
        .order_by(Invoice.created_at.asc(), Invoice.id.asc())
        .first()
    )
    if not first_invoice:
        return None
    match = re.match(r"^(.*?)(\d+)$", first_invoice.invoice_number)
    if not match:
        return None
    prefix, first_number = match.groups()
    width = len(first_number)
    series_numbers = []
    for invoice in db.query(Invoice.invoice_number).filter(Invoice.user_id == user_id).all():
        series_match = re.match(rf"^{re.escape(prefix)}(\d+)$", invoice[0])
        if series_match:
            series_numbers.append(int(series_match.group(1)))
    next_number = max(series_numbers or [int(first_number)]) + 1
    return f"{prefix}{next_number:0{width}d}"


def _calculate_invoice_tax(subtotal: Decimal, item, seller_state: str | None, place_of_supply: str | None):
    explicit_rates = any(rate is not None for rate in (item.cgst_rate, item.sgst_rate, item.igst_rate))
    if not explicit_rates:
        return calculate_tax(subtotal, item.gst_rate, seller_state, place_of_supply)
    cgst = subtotal * Decimal(str(item.cgst_rate or 0)) / Decimal("100")
    sgst = subtotal * Decimal(str(item.sgst_rate or 0)) / Decimal("100")
    igst = subtotal * Decimal(str(item.igst_rate or 0)) / Decimal("100")
    total = subtotal + cgst + sgst + igst
    return type("TaxBreakdown", (), {"subtotal": subtotal, "cgst": cgst, "sgst": sgst, "igst": igst, "total": total})()


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

    paid_amount = (
        db.query(func.coalesce(func.sum(Invoice.paid_amount), 0))
        .filter(Invoice.user_id == current_user.id)
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
        "paid_amount": float(paid_amount),
        "outstanding": float(outstanding),
        "total_purchases": float(total_purchases),
        "total_profit_loss": float(total_profit_loss),
        "total_products": total_products,
        "total_customers": total_customers,
        "recent_invoices": recent_invoices,
    }


@router.get("/customers", response_model=List[CustomerResponse], tags=["Customers"])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .order_by(Customer.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/branches", response_model=List[BranchResponse], tags=["Branches"])
def list_branches(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Branch).filter(Branch.user_id == current_user.id).order_by(Branch.created_at.asc()).offset(skip).limit(limit).all()


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED, tags=["Branches"])
def create_branch(payload: BranchCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    branch = Branch(user_id=current_user.id, **payload.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/vendors", response_model=List[VendorResponse], tags=["Vendors"])
def list_vendors(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Vendor).filter(Vendor.user_id == current_user.id).order_by(Vendor.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED, tags=["Vendors"])
def create_vendor(payload: VendorCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vendor = Vendor(user_id=current_user.id, **payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/inventory", tags=["Inventory"])
def list_inventory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .filter(Product.user_id == current_user.id, Branch.user_id == current_user.id)
        .all()
    )
    return [
        {
            "id": row.id,
            "branch_id": row.branch_id,
            "product_id": row.product_id,
            "product_name": row.product.name,
            "quantity": row.quantity,
            "min_stock_level": row.min_stock_level,
            "reorder_level": row.reorder_level,
        }
        for row in rows
    ]


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
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
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
    sku = payload.sku.strip() if payload.sku else None
    barcode = payload.barcode.strip() if payload.barcode else None
    sku = sku or None
    barcode = barcode or None

    if sku and db.query(Product).filter(Product.user_id == current_user.id, Product.sku == sku).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU is already in use")
    if barcode and db.query(Product).filter(Product.user_id == current_user.id, Product.barcode == barcode).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode is already in use")

    product = Product(
        user_id=current_user.id,
        name=payload.name,
        sku=sku,
        barcode=barcode,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/company-profile", tags=["Invoices"])
def get_company_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    branch = _get_or_create_branch(db, current_user)
    return {
        "shop_name": branch.name or "",
        "company_gstin": branch.gst_number or "",
        "company_address": branch.address or "",
        "company_state": branch.state or "",
        "company_state_code": branch.state_code or "",
        "company_phone": branch.phone or "",
        "company_email": branch.email or "",
        "next_invoice_number": _next_invoice_number(db, current_user.id) or "",
    }


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
def create_invoice(
    payload: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice_number = payload.invoice_number
    if invoice_number is None or not invoice_number.strip():
        invoice_number = _next_invoice_number(db, current_user.id)
        if invoice_number is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Enter the first invoice number with a numeric ending, for example INV-001")
    elif db.query(Invoice).filter(Invoice.user_id == current_user.id).count() > 0:
        invoice_number = _next_invoice_number(db, current_user.id)
        if invoice_number is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Your first invoice number must end with a number so automatic numbering can continue")

    if db.query(Invoice).filter(Invoice.user_id == current_user.id, Invoice.invoice_number == invoice_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice number already exists")

    branch = None
    if payload.branch_id is not None:
        branch = db.query(Branch).filter(
            Branch.id == payload.branch_id,
            Branch.user_id == current_user.id,
            Branch.is_active.is_(True),
        ).first()
        if not branch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    if branch is None:
        branch = _get_or_create_branch(db, current_user)

    company_values = {
        "name": payload.shop_name,
        "gst_number": payload.company_gstin,
        "address": payload.company_address,
        "state": payload.company_state,
        "state_code": payload.company_state_code,
        "phone": payload.company_phone,
        "email": payload.company_email,
    }
    for field, value in company_values.items():
        if value is not None and value != "":
            setattr(branch, field, value)
    db.flush()

    if payload.customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.user_id == current_user.id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice must contain at least one item")

    gross_subtotal = Decimal("0")
    cgst_amount = Decimal("0")
    sgst_amount = Decimal("0")
    igst_amount = Decimal("0")
    total_tax = Decimal("0")

    for item in payload.items:
        if item.quantity <= 0 or item.unit_price < 0 or item.gst_rate < 0 or any(rate is not None and (rate < 0 or rate > 100) for rate in (item.cgst_rate, item.sgst_rate, item.igst_rate)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid invoice item values")
        line_subtotal = Decimal(str(item.quantity)) * item.unit_price
        gross_subtotal += line_subtotal

    discount_percentage = payload.discount_percentage or Decimal("0")
    if discount_percentage < 0 or discount_percentage > 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Discount percentage must be between zero and 100")
    discount_amount = (
        gross_subtotal * discount_percentage / Decimal("100")
        if discount_percentage
        else payload.discount_amount or Decimal("0")
    )
    if discount_amount < 0 or discount_amount > gross_subtotal:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Discount must be between zero and subtotal")
    subtotal = gross_subtotal - discount_amount
    for item in payload.items:
        line_subtotal = Decimal(str(item.quantity)) * item.unit_price
        line_discount = (discount_amount * line_subtotal / gross_subtotal) if gross_subtotal else Decimal("0")
        taxable_line = line_subtotal - line_discount
        tax = _calculate_invoice_tax(taxable_line, item, payload.seller_state or branch.state, payload.place_of_supply)
        total_tax += tax.total - tax.subtotal
        cgst_amount += tax.cgst
        sgst_amount += tax.sgst
        igst_amount += tax.igst

    total_amount = subtotal + total_tax
    paid_amount = payload.paid_amount if payload.paid_amount is not None else Decimal("0")
    if paid_amount < 0 or paid_amount > total_amount:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Paid amount must be between zero and invoice total")
    remaining_amount = total_amount - paid_amount

    invoice_status = "paid" if remaining_amount <= 0 else "partially_paid" if paid_amount > 0 else "unpaid"

    invoice = Invoice(
        user_id=current_user.id,
        customer_id=payload.customer_id,
        invoice_number=invoice_number,
        branch_id=branch.id,
        shop_name=branch.name,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=subtotal,
        discount_amount=discount_amount,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        total_tax=total_tax,
        total_amount=total_amount,
        paid_amount=paid_amount,
        status=invoice_status,
        notes=payload.notes,
    )
    db.add(invoice)
    db.flush()

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

        line_subtotal = Decimal(str(item.quantity)) * item.unit_price
        line_discount = (discount_amount * line_subtotal / gross_subtotal) if gross_subtotal else Decimal("0")
        taxable_line = line_subtotal - line_discount
        line_tax = _calculate_invoice_tax(taxable_line, item, payload.seller_state or branch.state, payload.place_of_supply)
        interstate = bool(payload.seller_state and payload.place_of_supply and payload.seller_state.lower() != payload.place_of_supply.lower())
        explicit_rates = any(rate is not None for rate in (item.cgst_rate, item.sgst_rate, item.igst_rate))
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=resolved_product.id if resolved_product is not None else None,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=Decimal(str(item.quantity)) * item.unit_price,
            gst_rate=item.gst_rate,
            cgst_rate=item.cgst_rate if explicit_rates else (0 if interstate else item.gst_rate / 2),
            sgst_rate=item.sgst_rate if explicit_rates else (0 if interstate else item.gst_rate / 2),
            igst_rate=item.igst_rate if explicit_rates else (item.gst_rate if interstate else 0),
            tax_amount=line_tax.total - taxable_line,
            line_total=line_tax.total,
        )
        db.add(invoice_item)

    uploads_dir = Path("./uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    payment_proof_path = None
    payment_proof_is_image = False

    if payload.payment_proof_data:
        try:
            encoded_proof = payload.payment_proof_data.split(",", 1)[1]
            proof_bytes = base64.b64decode(encoded_proof, validate=True)
        except (IndexError, ValueError, binascii.Error) as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid payment proof") from exc
        if len(proof_bytes) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payment proof is too large")
        proof_content_type = payload.payment_proof_data.split(",", 1)[0][5:].split(";", 1)[0]
        payment_proof_is_image = proof_content_type.startswith("image/")
        proof_extension = mimetypes.guess_extension(proof_content_type, strict=False) or ".bin"
        file_name = f"payment_proof_{invoice.id}{proof_extension}"
        file_path = uploads_dir / file_name
        file_path.write_bytes(proof_bytes)
        payment_proof_path = file_path

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
            str(uploads_dir / f"invoice_{uuid4().hex}.pdf"),
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
            branch.name,
            branch.gst_number,
            branch.address,
            branch.state,
            branch.state_code,
            branch.phone,
            branch.email,
            invoice.discount_amount,
            invoice.cgst_amount,
            invoice.sgst_amount,
            invoice.igst_amount,
            str(payment_proof_path) if payment_proof_path and payment_proof_is_image else None,
        )
        invoice.file_path = invoice_pdf_path

    post_entry(db, current_user, invoice.invoice_date, f"Invoice {invoice.invoice_number}", f"invoice:{invoice.id}", "invoice", [
        ("Accounts Receivable", "asset", remaining_amount, Decimal("0")),
        ("Cash", "asset", paid_amount, Decimal("0")),
        ("Sales", "income", Decimal("0"), invoice.subtotal),
        ("Output CGST", "liability", Decimal("0"), invoice.cgst_amount),
        ("Output SGST", "liability", Decimal("0"), invoice.sgst_amount),
        ("Output IGST", "liability", Decimal("0"), invoice.igst_amount),
    ])
    db.commit()
    db.refresh(invoice)
    return invoice


def _get_invoice_for_user(invoice_id: int, current_user: User, db: Session) -> Invoice:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.get("/invoices/{invoice_id}/pdf", tags=["Invoices"])
def download_invoice_pdf(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = _get_invoice_for_user(invoice_id, current_user, db)
    if not invoice.file_path or not Path(invoice.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice PDF is not available")
    return FileResponse(invoice.file_path, media_type="application/pdf", filename=f"invoice-{invoice.invoice_number}.pdf")


@router.get("/invoices/{invoice_id}/excel", tags=["Invoices"])
def download_invoice_excel(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = _get_invoice_for_user(invoice_id, current_user, db)
    item = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).order_by(InvoiceItem.id.asc()).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice items not found")
    customer_name = invoice.customer.name if invoice.customer else "Customer"
    workbook = generate_invoice_excel(invoice, customer_name, item, invoice.shop_name)
    return StreamingResponse(workbook, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="invoice-{invoice.invoice_number}.xlsx"'})


@router.post("/invoices/{invoice_id}/send", tags=["Invoices"])
def send_invoice_email(invoice_id: int, payload: InvoiceEmailRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = _get_invoice_for_user(invoice_id, current_user, db)
    recipient = payload.recipient_email or (invoice.customer.email if invoice.customer else None)
    if not recipient:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Customer email is required")
    if not invoice.file_path or not Path(invoice.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice PDF is not available")
    payment_proof_path = next(
        Path(invoice.file_path).resolve().parent.glob(f"payment_proof_{invoice.id}.*"),
        None,
    )
    if payload.payment_proof_expected and payment_proof_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected attachment is missing. Please recreate the invoice and try again.",
        )
    sent = EmailService.send_invoice_pdf_email(
        recipient,
        invoice.customer.name if invoice.customer else "Customer",
        invoice.invoice_number,
        invoice.file_path,
    )
    if not sent:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Invoice email could not be sent. Check SMTP settings or uploaded attachment.")
    return {"message": "Invoice sent successfully", "recipient_email": recipient}


@router.get("/payments", response_model=List[PaymentResponse], tags=["Payments"])
def list_payments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Payment)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, tags=["Payments"])
def record_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment amount must be positive")

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == payload.invoice_id, Invoice.user_id == current_user.id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if not invoice.customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice has no customer for payment allocation")

    remaining = Decimal(str(invoice.total_amount or 0)) - Decimal(str(invoice.paid_amount or 0))
    if payload.amount > remaining:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment exceeds invoice balance")

    payment = Payment(
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount=payload.amount,
        payment_date=payload.payment_date,
        payment_method=payload.payment_method,
        reference_number=payload.reference_number,
        notes=payload.notes,
    )
    invoice.paid_amount = Decimal(str(invoice.paid_amount or 0)) + payload.amount
    invoice.status = "paid" if invoice.paid_amount >= invoice.total_amount else "partially_paid"
    db.add(payment)
    db.flush()

    customer_balance = (
        db.query(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0))
        .filter(Invoice.customer_id == invoice.customer_id, Invoice.status != "paid", Invoice.user_id == current_user.id)
        .scalar()
        or 0
    )
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id, Customer.user_id == current_user.id).first()
    if customer:
        customer.outstanding_amount = customer_balance

    post_entry(db, current_user, payload.payment_date, f"Payment for invoice {invoice.invoice_number}", f"payment:{payment.id}", "payment", [
        ("Cash", "asset", payload.amount, Decimal("0")),
        ("Accounts Receivable", "asset", Decimal("0"), payload.amount),
    ])

    db.commit()
    db.refresh(payment)
    return payment
