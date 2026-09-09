import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient as StarletteTestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import create_app
from app.models.database import Base, Branch, Customer, Inventory, Invoice, Product, User


from pathlib import Path


@pytest.fixture
def client():
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
            "payment_proof_data": "data:image/png;base64,AAAA",
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
