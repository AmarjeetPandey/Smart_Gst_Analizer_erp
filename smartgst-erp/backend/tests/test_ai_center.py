from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient as StarletteTestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import create_app
from app.models.database import Base, Branch, Customer, Inventory, Invoice, InvoiceItem, Product, Purchase, User


def build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app, StarletteTestClient(app), testing_session


def auth_headers(user_id):
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user_id)})}"}


def add_invoice(db, user_id, invoice_number, invoice_date, total, status="unpaid", paid_amount=0):
    invoice = Invoice(
        user_id=user_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        subtotal=Decimal(str(total)),
        total_amount=Decimal(str(total)),
        paid_amount=Decimal(str(paid_amount)),
        status=status,
    )
    db.add(invoice)
    db.flush()
    return invoice


def test_summary_and_copilot_use_owned_records_and_correct_periods():
    app, client, testing_session = build_client()
    today = date.today()
    previous_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    previous_date = min(previous_start + timedelta(days=today.day - 1), today.replace(day=1) - timedelta(days=1))
    with testing_session() as db:
        owner = User(email="owner-ai@example.com", name="AI Owner", is_email_verified=True)
        other = User(email="other-ai@example.com", name="Other Owner", is_email_verified=True)
        db.add_all([owner, other])
        db.commit()
        db.refresh(owner)
        db.refresh(other)

        widget = Product(
            user_id=owner.id,
            name="Widget",
            sku="WIDGET-AI",
            purchase_price=Decimal("10"),
            selling_price=Decimal("25"),
        )
        db.add(widget)
        db.flush()

        current = add_invoice(db, owner.id, "AI-CURRENT", today, 100, status="paid", paid_amount=100)
        previous = add_invoice(db, owner.id, "AI-PREVIOUS", previous_date, 50)
        add_invoice(db, owner.id, "AI-FUTURE", today + timedelta(days=1), 999)
        add_invoice(db, other.id, "AI-OTHER", today, 10000)
        db.add_all(
            [
                InvoiceItem(invoice_id=current.id, product_id=widget.id, description="Widget", quantity=4, unit_price=25, subtotal=100, line_total=100),
                InvoiceItem(invoice_id=previous.id, product_id=widget.id, description="Widget", quantity=1, unit_price=50, subtotal=50, line_total=50),
                Purchase(user_id=owner.id, purchase_number="AI-PURCHASE", purchase_date=today, total_amount=Decimal("30")),
                Purchase(user_id=other.id, purchase_number="AI-OTHER-PURCHASE", purchase_date=today, total_amount=Decimal("500")),
            ]
        )
        db.commit()
        owner_id = owner.id

    headers = auth_headers(owner_id)
    summary_response = client.get("/api/v1/ai/business-summary", headers=headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["kpis"]["current_month_sales"] == 100
    assert summary["kpis"]["previous_month_sales"] == 50
    assert summary["kpis"]["period_change_percent"] == 100
    assert summary["periods"]["current"]["end"] == today.isoformat()
    assert summary["kpis"]["total_purchases"] == 30
    assert summary["kpis"]["average_order_value"] == 383
    assert summary["top_products"][0]["product"] == "Widget"
    assert summary["top_products"][0]["quantity"] == 5

    question_tests = [
        ("Is month kitni sales hui?", "100"),
        ("How much did I sell last month?", "50.00"),
        ("How much have I sold this year?", "150.00"),
        ("Last month ke comparison mein sales kitni badhi?", "100.00%"),
        ("Which product sold the most?", "Widget"),
        ("How much did I purchase this month?", "30.00"),
        ("How much profit did I make?", "1,119.00"),
        ("Kitne invoices paid aur unpaid hain?", "1 invoice is marked PAID"),
        ("How many invoices are paid and unpaid this month?", "0 are marked UNPAID"),
        ("Who are my top customers?", "No customer purchase history"),
        ("Show my business summary", "Sales increased by"),
        ("Which products are low in stock?", "No products are at or below"),
    ]
    for question, expected in question_tests:
        response = client.post(
            "/api/v1/ai/copilot/query",
            json={"question": question},
            headers=headers,
        )
        assert response.status_code == 200
        assert expected in response.json()["answer"]

    status_result = client.post(
        "/api/v1/ai/copilot/query",
        json={"question": "How many invoices are paid and unpaid?"},
        headers=headers,
    ).json()["data"]["invoice_statuses"]
    assert status_result["paid"]["count"] == 1
    assert status_result["unpaid"]["count"] == 2
    app.dependency_overrides.clear()


def test_forecast_requires_sufficient_history_and_counts_missing_days_as_zero():
    app, client, testing_session = build_client()
    today = date.today()
    with testing_session() as db:
        user = User(email="forecast-ai@example.com", name="Forecast Owner", is_email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        owner_id = user.id
        add_invoice(db, user.id, "FORECAST-1", today - timedelta(days=3), 100)
        db.commit()

    headers = auth_headers(owner_id)
    response = client.get("/api/v1/ai/forecast/summary", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert response.json()["sales_forecast"] is None

    with testing_session() as db:
        user = db.query(User).filter(User.id == owner_id).one()
        for index, offset in enumerate((27, 23, 19, 15, 11, 7), start=1):
            add_invoice(db, user.id, f"FORECAST-{index + 1}", today - timedelta(days=offset), 100)
        db.commit()

    response = client.get("/api/v1/ai/forecast/summary", headers=headers)
    assert response.status_code == 200
    forecast = response.json()
    assert forecast["status"] == "ok"
    assert forecast["data_points"] == 7
    assert forecast["historical_context"]["days_with_sales"] == 7
    assert forecast["sales_forecast"] == {"next_7_days": 175, "next_30_days": 750, "next_90_days": 2250}
    assert forecast["forecast_periods"]["next_7_days"]["start"] == (today + timedelta(days=1)).isoformat()
    app.dependency_overrides.clear()


def test_anomalies_and_alerts_deduplicate_product_warnings():
    app, client, testing_session = build_client()
    with testing_session() as db:
        user = User(email="stock-ai@example.com", name="Stock Owner", is_email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        product = Product(
            user_id=user.id,
            name="Low Widget",
            sku="LOW-WIDGET-AI",
            purchase_price=Decimal("10"),
            selling_price=Decimal("25"),
        )
        branch_a = Branch(user_id=user.id, name="Branch A")
        branch_b = Branch(user_id=user.id, name="Branch B")
        healthy_branch = Branch(user_id=user.id, name="Healthy Branch")
        db.add_all([product, branch_a, branch_b, healthy_branch])
        db.flush()
        db.add_all(
            [
                Inventory(product_id=product.id, branch_id=branch_a.id, quantity=2, reorder_level=10, min_stock_level=5),
                Inventory(product_id=product.id, branch_id=branch_b.id, quantity=3, reorder_level=10, min_stock_level=5),
                Inventory(product_id=product.id, branch_id=healthy_branch.id, quantity=100, reorder_level=10, min_stock_level=5),
            ]
        )
        db.commit()
        owner_id = user.id

    headers = auth_headers(owner_id)
    anomalies = client.get("/api/v1/ai/anomalies", headers=headers).json()["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_type"] == "low_stock_warning"
    assert anomalies[0]["product"] == "Low Widget"
    assert anomalies[0]["metrics"]["quantity"] == 5
    assert anomalies[0]["severity"] == "HIGH"
    assert anomalies[0]["recommended_action"]

    alerts = client.get("/api/v1/ai/alerts", headers=headers).json()
    stock_alerts = [alert for alert in alerts["alerts"] if alert["type"] == "inventory"]
    assert len(stock_alerts) == 1
    assert stock_alerts[0]["alert_id"] == f"low-stock-{anomalies[0]['entity_id']}"
    assert alerts["count"] == len(alerts["alerts"])
    copilot = client.post(
        "/api/v1/ai/copilot/query",
        json={"question": "What is low in stock?"},
        headers=headers,
    ).json()
    assert "Low Widget" in copilot["answer"]
    assert copilot["data"]["low_stock_products"][0]["quantity"] == 5
    app.dependency_overrides.clear()


def test_empty_business_data_returns_explicit_insufficient_states():
    app, client, testing_session = build_client()
    with testing_session() as db:
        user = User(email="empty-ai@example.com", name="Empty Owner", is_email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        owner_id = user.id

    headers = auth_headers(owner_id)
    summary = client.get("/api/v1/ai/business-summary", headers=headers).json()
    assert summary["status"] == "insufficient_data"
    assert summary["kpis"]["average_order_value"] == 0
    assert summary["kpis"]["period_change_percent"] is None
    assert summary["top_products"] == []
    forecast = client.get("/api/v1/ai/forecast/summary", headers=headers).json()
    assert forecast["status"] == "insufficient_data"
    assert forecast["sales_forecast"] is None
    assert client.get("/api/v1/ai/anomalies", headers=headers).json()["count"] == 0
    assert client.get("/api/v1/ai/alerts", headers=headers).json() == {"status": "ok", "count": 0, "alerts": []}
    unsupported = client.post(
        "/api/v1/ai/copilot/query",
        json={"question": "Can you calculate a metric not supported by these records?"},
        headers=headers,
    ).json()
    assert "could not match" in unsupported["answer"]

    with testing_session() as db:
        add_invoice(db, owner_id, "CURRENT-NO-COMPARISON", date.today(), 50)
        db.commit()
    summary = client.get("/api/v1/ai/business-summary", headers=headers).json()
    assert summary["kpis"]["current_month_sales"] == 50
    assert summary["kpis"]["period_change_percent"] is None
    comparison = client.post(
        "/api/v1/ai/copilot/query",
        json={"question": "Compare this month sales with last month"},
        headers=headers,
    ).json()
    assert comparison["data"]["comparison"]["change_percent"] is None
    assert "cannot be calculated" in comparison["answer"]
    app.dependency_overrides.clear()
