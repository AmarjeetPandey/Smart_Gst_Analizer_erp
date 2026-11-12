import pytest
import base64
from datetime import date
from decimal import Decimal
from email import policy
from email.parser import BytesParser
from io import BytesIO
from PIL import Image
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient as StarletteTestClient

from app.core.database import ensure_schema_compatibility, get_db
from app.core.security import create_access_token
from app.api.routes import dashboard
from app.main import create_app
from app.models.database import Base, Branch, Customer, Inventory, Invoice, InvoiceItem, Ledger, Payment, Product, Purchase, Transaction, User, UserRoleEnum, Vendor
from app.services import email_service


from pathlib import Path


def _png_data_uri():
    image = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(image, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(image.getvalue()).decode('ascii')}"


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr("app.main.ensure_schema_compatibility", lambda *_args, **_kwargs: None)
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with StarletteTestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_dashboard_summary_uses_real_user_data(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="owner@example.com", name="Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add_all(
        [
            Customer(user_id=user.id, name="Acme", phone="1111111111"),
            Product(
                user_id=user.id,
                name="Laptop",
                sku="LP-001",
                purchase_price=Decimal("500"),
                selling_price=Decimal("700"),
            ),
            Invoice(
                user_id=user.id,
                invoice_number="INV-001",
                invoice_date=date(2024, 1, 1),
                subtotal=Decimal("700"),
                cgst_amount=Decimal("0"),
                sgst_amount=Decimal("0"),
                igst_amount=Decimal("0"),
                total_tax=Decimal("0"),
                total_amount=Decimal("700"),
                paid_amount=Decimal("200"),
                status="partially_paid",
            ),
            Invoice(
                user_id=user.id,
                invoice_number="INV-002",
                invoice_date=date(2024, 1, 2),
                subtotal=Decimal("300"),
                cgst_amount=Decimal("0"),
                sgst_amount=Decimal("0"),
                igst_amount=Decimal("0"),
                total_tax=Decimal("0"),
                total_amount=Decimal("300"),
                paid_amount=Decimal("300"),
                status="paid",
            ),
        ]
    )
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert float(data["total_sales"]) == 1000.0
    assert float(data["outstanding"]) == 500.0
    assert data["total_products"] == 1
    assert data["total_customers"] == 1


def test_create_invoice_stores_paid_amount_and_payment_proof(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="owner@example.com", name="Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    response = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "INV-100",
            "invoice_date": "2024-01-10",
            "items": [{"description": "Laptop", "quantity": 1, "unit_price": "500", "gst_rate": 0}],
            "paid_amount": "100",
            "remaining_amount": "400",
            "sku": "SKU-100",
            "payment_proof_data": _png_data_uri(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    invoice = db.query(Invoice).filter(Invoice.invoice_number == "INV-100").first()
    assert invoice is not None
    assert invoice.paid_amount == Decimal("100")
    assert invoice.status == "partially_paid"
    assert invoice.file_path is not None
    assert Path(invoice.file_path).exists()
    assert b"/Subtype /Image" in Path(invoice.file_path).read_bytes()


def test_send_invoice_email_includes_uploaded_payment_proof(client, monkeypatch):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="owner@example.com", name="Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    invoice_response = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "INV-101",
            "invoice_date": "2024-01-10",
            "items": [{"description": "Laptop", "quantity": 1, "unit_price": "500", "gst_rate": 0}],
            "payment_proof_data": _png_data_uri(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invoice_response.status_code == 201

    sent_arguments = {}

    def capture_email(recipient, customer_name, invoice_number, pdf_path):
        sent_arguments["pdf_path"] = pdf_path
        return True

    monkeypatch.setattr(dashboard.EmailService, "send_invoice_pdf_email", capture_email)
    response = client.post(
        f"/api/v1/invoices/{invoice_response.json()['id']}/send",
        json={"recipient_email": "client@example.com", "payment_proof_expected": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert b"/Subtype /Image" in Path(sent_arguments["pdf_path"]).read_bytes()
    payment_proof_path = Path(sent_arguments["pdf_path"]).parent / f"payment_proof_{invoice_response.json()['id']}.png"
    assert payment_proof_path.suffix == ".png"
    assert payment_proof_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    invoice_without_proof = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "INV-102",
            "invoice_date": "2024-01-10",
            "items": [{"description": "Laptop", "quantity": 1, "unit_price": "500", "gst_rate": 0}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invoice_without_proof.status_code == 201

    missing_proof_response = client.post(
        f"/api/v1/invoices/{invoice_without_proof.json()['id']}/send",
        json={"recipient_email": "client@example.com", "payment_proof_expected": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert missing_proof_response.status_code == 404


def test_invoice_email_attaches_only_invoice_pdf(tmp_path, monkeypatch):
    invoice_pdf = tmp_path / "invoice.pdf"
    invoice_pdf.write_bytes(b"invoice")
    captured_message = {}

    class FakeSMTP:
        def __init__(self, server, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def starttls(self):
            pass

        def login(self, username, password):
            pass

        def sendmail(self, sender, recipient, message):
            captured_message["message"] = BytesParser(policy=policy.default).parsebytes(message.encode())

    monkeypatch.setattr(email_service.settings, "ENABLE_EMAIL_NOTIFICATIONS", True)
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    sent = email_service.EmailService.send_invoice_pdf_email(
        "client@example.com",
        "Client",
        "INV-101",
        str(invoice_pdf),
    )

    assert sent is True
    attachments = list(captured_message["message"].iter_attachments())
    assert [attachment.get_filename() for attachment in attachments] == ["invoice.pdf"]
    assert attachments[0].get_content_type() == "application/pdf"
    assert [attachment.get_payload(decode=True) for attachment in attachments] == [b"invoice"]


def test_product_quantity_is_stored_and_reduced_on_invoice(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="stock@example.com", name="Stock Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    product_response = client.post(
        "/api/v1/products",
        json={
            "name": "Mouse",
            "sku": "MOUSE-1",
            "purchase_price": "50",
            "selling_price": "100",
            "quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert product_response.status_code == 201
    product = db.query(Product).filter(Product.sku == "MOUSE-1").first()
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    assert inventory is not None
    assert inventory.quantity == 10

    invoice_response = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "INV-200",
            "invoice_date": "2024-01-10",
            "items": [{"description": "Mouse", "quantity": 3, "unit_price": "100", "gst_rate": 0}],
            "sku": "MOUSE-1",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert invoice_response.status_code == 201
    db.refresh(inventory)
    assert inventory.quantity == 7


def test_products_without_sku_can_be_added_more_than_once(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    user = User(email="blank-sku@example.com", name="Blank SKU Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    for name in ("First product", "Second product"):
        response = client.post(
            "/api/v1/products",
            json={"name": name, "sku": "", "purchase_price": "10", "selling_price": "20"},
            headers=headers,
        )
        assert response.status_code == 201
        assert response.json()["sku"] is None


def test_business_identifiers_are_user_scoped_and_reusable_after_clear(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    owner = User(email="identifier-owner@example.com", name="Owner", is_email_verified=True)
    other_user = User(email="identifier-other@example.com", name="Other", is_email_verified=True)
    db.add_all([owner, other_user])
    db.commit()
    db.refresh(owner)
    db.refresh(other_user)
    db.add_all([
        Product(user_id=owner.id, name="Old product", sku="REUSED-SKU", barcode="REUSED-BARCODE", purchase_price=Decimal("10"), selling_price=Decimal("20")),
        Product(user_id=other_user.id, name="Other product", sku="REUSED-SKU", barcode="REUSED-BARCODE", purchase_price=Decimal("10"), selling_price=Decimal("20")),
        Purchase(user_id=owner.id, purchase_number="REUSED-PURCHASE", purchase_date=date(2024, 1, 12)),
        Purchase(user_id=other_user.id, purchase_number="REUSED-PURCHASE", purchase_date=date(2024, 1, 12)),
        Invoice(user_id=owner.id, invoice_number="REUSED-INVOICE", invoice_date=date(2024, 1, 12)),
        Invoice(user_id=other_user.id, invoice_number="REUSED-INVOICE", invoice_date=date(2024, 1, 12)),
    ])
    db.commit()

    owner_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(owner.id)})}"}
    other_headers = {"Authorization": f"Bearer {create_access_token({'sub': str(other_user.id)})}"}
    clear_response = client.post(
        "/api/v1/history/clear",
        json={"confirmation": "CLEAR"},
        headers=owner_headers,
    )
    assert clear_response.status_code == 200

    product_response = client.post(
        "/api/v1/products",
        json={"name": "New product", "sku": "REUSED-SKU", "barcode": "REUSED-BARCODE", "purchase_price": "10", "selling_price": "20"},
        headers=owner_headers,
    )
    assert product_response.status_code == 201

    purchase_response = client.post(
        "/api/v1/purchases",
        json={
            "purchase_number": "REUSED-PURCHASE",
            "purchase_date": "2024-01-12",
            "items": [{"description": "New product", "quantity": 1, "unit_price": "10"}],
        },
        headers=owner_headers,
    )
    assert purchase_response.status_code == 201

    invoice_response = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "REUSED-INVOICE",
            "invoice_date": "2024-01-12",
            "items": [{"description": "New product", "quantity": 1, "unit_price": "20"}],
        },
        headers=owner_headers,
    )
    assert invoice_response.status_code == 201

    assert db.query(Product).filter(Product.user_id == other_user.id, Product.sku == "REUSED-SKU").count() == 1
    assert db.query(Purchase).filter(Purchase.user_id == other_user.id, Purchase.purchase_number == "REUSED-PURCHASE").count() == 1
    assert db.query(Invoice).filter(Invoice.user_id == other_user.id, Invoice.invoice_number == "REUSED-INVOICE").count() == 1
    assert client.post(
        "/api/v1/products",
        json={"name": "Duplicate SKU", "sku": "REUSED-SKU", "purchase_price": "10", "selling_price": "20"},
        headers=owner_headers,
    ).status_code == 409
    assert client.post(
        "/api/v1/purchases",
        json={
            "purchase_number": "REUSED-PURCHASE",
            "purchase_date": "2024-01-12",
            "items": [{"description": "Duplicate purchase", "quantity": 1, "unit_price": "10"}],
        },
        headers=other_headers,
    ).status_code == 409


def test_schema_compatibility_replaces_legacy_global_identifier_indexes():
    schema_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with schema_engine.begin() as connection:
        connection.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, sku VARCHAR(100), barcode VARCHAR(255))"))
        connection.execute(text("CREATE TABLE purchases (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, purchase_number VARCHAR(100) NOT NULL)"))
        connection.execute(text("CREATE TABLE invoices (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, invoice_number VARCHAR(100) NOT NULL)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_products_sku ON products (sku)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_products_barcode ON products (barcode)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_purchases_purchase_number ON purchases (purchase_number)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_invoices_invoice_number ON invoices (invoice_number)"))

    ensure_schema_compatibility(schema_engine)

    inspector = inspect(schema_engine)
    for table, field in (
        ("products", "sku"),
        ("products", "barcode"),
        ("purchases", "purchase_number"),
        ("invoices", "invoice_number"),
    ):
        assert not any(
            index.get("unique") and index.get("column_names") == [field]
            for index in inspector.get_indexes(table)
        )
        assert any(
            index.get("unique") and index.get("column_names") == ["user_id", field]
            for index in inspector.get_indexes(table)
        )

    with schema_engine.begin() as connection:
        connection.execute(text("INSERT INTO products (user_id, sku, barcode) VALUES (1, 'SHARED-SKU', 'SHARED-BARCODE'), (2, 'SHARED-SKU', 'SHARED-BARCODE')"))
        connection.execute(text("INSERT INTO purchases (user_id, purchase_number) VALUES (1, 'SHARED-PURCHASE'), (2, 'SHARED-PURCHASE')"))
        connection.execute(text("INSERT INTO invoices (user_id, invoice_number) VALUES (1, 'SHARED-INVOICE'), (2, 'SHARED-INVOICE')"))
    schema_engine.dispose()


def test_record_payment_updates_invoice_and_customer_balance(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="payments@example.com", name="Payments Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    customer = Customer(user_id=user.id, name="Customer", phone="9999999999")
    db.add(customer)
    db.commit()
    db.refresh(customer)

    invoice = Invoice(
        user_id=user.id,
        customer_id=customer.id,
        invoice_number="INV-PAY-1",
        invoice_date=date(2024, 1, 10),
        subtotal=Decimal("500"),
        total_amount=Decimal("500"),
        paid_amount=Decimal("0"),
        status="unpaid",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    token = create_access_token({"sub": str(user.id)})
    response = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": invoice.id,
            "amount": "200",
            "payment_date": "2024-01-11",
            "payment_method": "upi",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    db.refresh(invoice)
    db.refresh(customer)
    assert invoice.paid_amount == Decimal("200")
    assert invoice.status == "partially_paid"
    assert customer.outstanding_amount == Decimal("300")


def test_create_purchase_increases_product_inventory(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())

    user = User(email="purchase@example.com", name="Purchase Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    vendor = Vendor(user_id=user.id, name="Supplier", phone="8888888888")
    product = Product(user_id=user.id, name="Keyboard", sku="KEY-1", purchase_price=Decimal("20"), selling_price=Decimal("40"))
    db.add_all([vendor, product])
    db.commit()
    db.refresh(vendor)
    db.refresh(product)

    token = create_access_token({"sub": str(user.id)})
    response = client.post(
        "/api/v1/purchases",
        json={
            "purchase_number": "PUR-1",
            "purchase_date": "2024-01-12",
            "vendor_id": vendor.id,
            "items": [{"product_id": product.id, "description": "Keyboard", "quantity": 5, "unit_price": "20", "gst_rate": 18}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    purchase = db.query(Purchase).filter(Purchase.purchase_number == "PUR-1").first()
    inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    assert purchase.total_amount == Decimal("118")
    assert inventory.quantity == 5


def test_duplicate_purchase_number_returns_conflict(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    user = User(email="duplicate-purchase@example.com", name="Purchase Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Purchase(user_id=user.id, purchase_number="PUR-DUP", purchase_date=date(2024, 1, 12)))
    db.commit()
    token = create_access_token({"sub": str(user.id)})

    response = client.post(
        "/api/v1/purchases",
        json={
            "purchase_number": "PUR-DUP",
            "purchase_date": "2024-01-12",
            "items": [{"description": "Widget", "quantity": 1, "unit_price": "10"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Purchase number already exists"


def test_interstate_invoice_uses_igst_and_posts_balanced_journal(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    user = User(email="gst@example.com", name="GST Owner", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})

    response = client.post(
        "/api/v1/invoices",
        json={
            "invoice_number": "INV-GST-1",
            "invoice_date": "2024-01-12",
            "seller_state": "Maharashtra",
            "place_of_supply": "Gujarat",
            "items": [{"description": "Service", "quantity": 1, "unit_price": "1000", "gst_rate": 18}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    invoice = db.query(Invoice).filter(Invoice.invoice_number == "INV-GST-1").first()
    assert invoice.igst_amount == Decimal("180.00")
    assert invoice.cgst_amount == Decimal("0.00")
    transactions = db.query(Transaction).filter(Transaction.reference_id == f"invoice:{invoice.id}").all()
    assert sum((row.debit for row in transactions), Decimal("0")) == sum((row.credit for row in transactions), Decimal("0"))


def test_cancel_invoice_restores_stock_and_is_auditable(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    user = User(email="cancel@example.com", name="Cancel Owner", role="admin", is_email_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    product_response = client.post(
        "/api/v1/products",
        json={"name": "Cable", "sku": "CAB-1", "purchase_price": "10", "selling_price": "20", "quantity": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert product_response.status_code == 201
    invoice_response = client.post(
        "/api/v1/invoices",
        json={"invoice_number": "INV-CANCEL-1", "invoice_date": "2024-01-12", "sku": "CAB-1", "items": [{"description": "Cable", "quantity": 1, "unit_price": "20", "gst_rate": 0}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    invoice_id = invoice_response.json()["id"]
    response = client.post(f"/api/v1/invoices/{invoice_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    inventory = db.query(Inventory).join(Product).filter(Product.sku == "CAB-1").first()
    assert inventory.quantity == 2
    assert db.query(Invoice).filter(Invoice.id == invoice_id).first().status == "cancelled"


def test_clear_business_history_only_removes_current_users_records(client):
    override_get_db = client.app.dependency_overrides[get_db]
    db = next(override_get_db())
    user = User(email="clear@example.com", name="Clear Owner", role=UserRoleEnum.VIEWER, is_email_verified=True)
    other_user = User(email="other@example.com", name="Other Owner", is_email_verified=True)
    db.add_all([user, other_user])
    db.commit()
    db.refresh(user)
    db.refresh(other_user)

    branch = Branch(user_id=user.id, name="Main")
    customer = Customer(user_id=user.id, name="Clear Customer", phone="1111111111")
    product = Product(user_id=user.id, name="Clear Product", sku="CLEAR-1", purchase_price=Decimal("10"), selling_price=Decimal("20"))
    invoice = Invoice(user_id=user.id, invoice_number="CLEAR-INV", invoice_date=date(2024, 1, 1), total_amount=Decimal("20"), paid_amount=Decimal("0"), status="unpaid")
    other_customer = Customer(user_id=other_user.id, name="Keep Customer", phone="2222222222")
    db.add_all([branch, customer, product, invoice, other_customer])
    db.commit()
    db.refresh(invoice)
    db.add_all([
        InvoiceItem(invoice_id=invoice.id, description="Clear Product", quantity=1, unit_price=Decimal("20"), subtotal=Decimal("20"), line_total=Decimal("20")),
        Payment(invoice_id=invoice.id, customer_id=customer.id, amount=Decimal("5"), payment_date=date(2024, 1, 1), payment_method="cash"),
    ])
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    rejected = client.post("/api/v1/history/clear", json={"confirmation": "clear"}, headers={"Authorization": f"Bearer {token}"})
    assert rejected.status_code == 400

    response = client.post("/api/v1/history/clear", json={"confirmation": "CLEAR"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert db.query(User).filter(User.id == user.id).first() is not None
    assert db.query(Customer).filter(Customer.user_id == user.id).count() == 0
    assert db.query(Product).filter(Product.user_id == user.id).count() == 0
    assert db.query(Invoice).filter(Invoice.user_id == user.id).count() == 0
    assert db.query(InvoiceItem).count() == 0
    assert db.query(Payment).count() == 0
    assert db.query(Customer).filter(Customer.user_id == other_user.id).count() == 1
