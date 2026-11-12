from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
import re
import unicodedata

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.database import Branch, Customer, Inventory, Invoice, InvoiceItem, Product, Purchase, User

router = APIRouter()


class CopilotQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=400)


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _month_range(reference_date: date | None = None):
    ref = reference_date or date.today()
    current_start = ref.replace(day=1)
    previous_start = (current_start - timedelta(days=1)).replace(day=1)
    previous_end = min(ref.day, (current_start - timedelta(days=1)).day)
    previous_period_end = previous_start + timedelta(days=previous_end)
    return current_start, ref + timedelta(days=1), previous_start, previous_period_end


def _sales_total_for_period(db: Session, user_id: int, start: date | None, end: date | None = None) -> Decimal:
    query = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(Invoice.user_id == user_id)
    if start:
        query = query.filter(Invoice.invoice_date >= start)
    if end:
        query = query.filter(Invoice.invoice_date < end)
    return query.scalar() or Decimal("0")


def _purchase_total_for_period(db: Session, user_id: int, start: date | None = None, end: date | None = None) -> Decimal:
    query = db.query(func.coalesce(func.sum(Purchase.total_amount), 0)).filter(Purchase.user_id == user_id)
    if start:
        query = query.filter(Purchase.purchase_date >= start)
    if end:
        query = query.filter(Purchase.purchase_date < end)
    return query.scalar() or Decimal("0")


def _top_products(
    db: Session,
    user_id: int,
    limit: int = 5,
    start: date | None = None,
    end: date | None = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(
            Product.id,
            Product.name,
            func.coalesce(func.sum(InvoiceItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(InvoiceItem.line_total), 0).label("revenue"),
        )
        .join(InvoiceItem, InvoiceItem.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .filter(Product.user_id == user_id, Invoice.user_id == user_id)
    )
    if start:
        query = query.filter(Invoice.invoice_date >= start)
    if end:
        query = query.filter(Invoice.invoice_date < end)
    rows = (
        query.group_by(Product.id, Product.name)
        .order_by(func.sum(InvoiceItem.quantity).desc(), Product.name.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "product_id": product_id,
            "product": name,
            "quantity": _as_float(quantity),
            "revenue": _as_float(revenue),
        }
        for product_id, name, quantity, revenue in rows
    ]


def _low_stock_products(db: Session, user_id: int, limit: int | None = 5) -> List[Dict[str, Any]]:
    rows = (
        db.query(
            Product.id,
            Product.name,
            Branch.id,
            Branch.name,
            Inventory.quantity,
            Inventory.reorder_level,
            Inventory.min_stock_level,
        )
        .join(Inventory, Inventory.product_id == Product.id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .filter(Product.user_id == user_id, Branch.user_id == user_id)
        .order_by(Product.name.asc(), Branch.name.asc(), Branch.id.asc())
        .all()
    )
    low_stock_by_product = {}
    for product_id, product_name, branch_id, branch_name, quantity, reorder, min_stock in rows:
        quantity_value = _as_float(quantity)
        minimum_value = _as_float(min_stock)
        threshold_value = _as_float(reorder if reorder is not None else min_stock)
        if quantity_value > threshold_value:
            continue
        product = low_stock_by_product.setdefault(
            product_id,
            {
                "product_id": product_id,
                "product": product_name,
                "quantity": 0.0,
                "reorder_level": 0.0,
                "min_stock_level": 0.0,
                "branch_count": 0,
                "below_minimum": False,
                "affected_branches": [],
            },
        )
        product["quantity"] += quantity_value
        product["reorder_level"] += threshold_value
        product["min_stock_level"] += minimum_value
        product["branch_count"] += 1
        product["below_minimum"] = product["below_minimum"] or quantity_value <= minimum_value
        product["affected_branches"].append(
            {
                "branch_id": branch_id,
                "branch": branch_name,
                "quantity": quantity_value,
                "reorder_level": threshold_value,
                "min_stock_level": minimum_value,
            }
        )
    result = sorted(
        low_stock_by_product.values(),
        key=lambda item: (not item["below_minimum"], item["quantity"], item["product"].casefold()),
    )
    return result[:limit] if limit is not None else result


def _get_business_summary(db: Session, user_id: int, include_low_stock: bool = True) -> Dict[str, Any]:
    current_start, current_end, previous_start, previous_end = _month_range()
    current_month_sales = _sales_total_for_period(db, user_id, current_start, current_end)
    previous_month_sales = _sales_total_for_period(db, user_id, previous_start, previous_end)
    total_sales = _sales_total_for_period(db, user_id, None)
    total_purchases = _purchase_total_for_period(db, user_id)
    total_orders = db.query(Invoice).filter(Invoice.user_id == user_id).count()
    purchase_count = db.query(Purchase).filter(Purchase.user_id == user_id).count()
    average_order_value = total_sales / total_orders if total_orders else Decimal("0")

    product_summary = _top_products(db, user_id, 5)
    low_stock = _low_stock_products(db, user_id) if include_low_stock else []
    ratio = (
        ((current_month_sales - previous_month_sales) / previous_month_sales) * 100
        if previous_month_sales > 0
        else None
    )
    if total_orders == 0:
        summary_text = "No invoice sales are available yet. Add invoices to see business performance."
    elif previous_month_sales == 0:
        if current_month_sales == 0:
            summary_text = "No invoice sales were recorded in either comparison period; a percentage change cannot be calculated."
        else:
            summary_text = "Current-period sales are available, but the comparison period has zero sales so a percentage change cannot be calculated."
    elif current_month_sales > previous_month_sales:
        summary_text = f"Sales increased by {abs(_as_float(ratio)):.2f}% compared with the previous period."
    elif current_month_sales < previous_month_sales:
        summary_text = f"Sales decreased by {abs(_as_float(ratio)):.2f}% compared with the previous period."
    else:
        summary_text = "Sales were unchanged compared with the previous period."

    return {
        "status": "ok" if total_orders else "insufficient_data",
        "summary": summary_text,
        "kpis": {
            "total_sales": _as_float(total_sales),
            "current_month_sales": _as_float(current_month_sales),
            "previous_month_sales": _as_float(previous_month_sales),
            "period_change_percent": round(_as_float(ratio), 2) if ratio is not None else None,
            "total_purchases": _as_float(total_purchases),
            "average_order_value": _as_float(average_order_value),
            "order_count": total_orders,
            "total_profit_loss": _as_float(total_sales - total_purchases) if total_orders and purchase_count else None,
        },
        "periods": {
            "current": {"start": current_start.isoformat(), "end": (current_end - timedelta(days=1)).isoformat()},
            "previous": {"start": previous_start.isoformat(), "end": (previous_end - timedelta(days=1)).isoformat()},
        },
        "top_products": product_summary,
        "low_stock_products": low_stock,
    }


@router.get("/ai/business-summary")
def get_business_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    return _get_business_summary(db, current_user.id)


@router.get("/ai/sales-analysis")
def get_sales_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    summary = _get_business_summary(db, current_user.id)
    return {
        "status": summary["status"],
        "summary": summary["summary"],
        "top_products": summary["top_products"],
        "low_stock_products": summary["low_stock_products"],
        "revenue": {
            "total_sales": summary["kpis"]["total_sales"],
            "current_month_sales": summary["kpis"]["current_month_sales"],
            "previous_month_sales": summary["kpis"]["previous_month_sales"],
        },
    }


@router.get("/ai/product-analysis")
def get_product_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {
        "status": "ok",
        "top_products": _top_products(db, current_user.id, 10),
        "low_stock_products": _low_stock_products(db, current_user.id),
    }


@router.get("/ai/customer-analysis")
def get_customer_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    customer_rows = (
        db.query(
            Customer.name,
            func.coalesce(func.sum(Invoice.total_amount), 0).label("revenue"),
            func.count(Invoice.id).label("orders"),
        )
        .join(Invoice, Invoice.customer_id == Customer.id)
        .filter(Customer.user_id == current_user.id, Invoice.user_id == current_user.id)
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Invoice.total_amount).desc())
        .limit(5)
        .all()
    )
    return {
        "status": "ok",
        "customers": [
            {
                "name": name,
                "revenue": _as_float(revenue),
                "orders": int(orders),
            }
            for name, revenue, orders in customer_rows
        ],
    }


@router.post("/ai/copilot/query")
def ask_copilot(request: CopilotQueryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    question = _normalize_question(request.question)
    if not question:
        return {"answer": "Please ask a business question about your sales, purchases, products, invoices, or inventory.", "data": {}}

    today = date.today()
    start, end, period_label = _query_period(question, today)
    money_basis = "invoice total_amount (including the invoice's stored discount and tax calculations)"

    if any(word in question for word in ("stock", "inventory", "reorder", "low stock", "bhandar", "stock mein", "स्टॉक", "इन्वेंटरी", "भंडार")):
        low_stock = _low_stock_products(db, current_user.id, limit=None)
        if not low_stock:
            return {"answer": "No products are at or below their configured reorder threshold.", "data": {"low_stock_products": []}}
        items = ", ".join(
            f"{item['product']} ({item['quantity']:g} in stock; reorder threshold {item['reorder_level']:g})"
            for item in low_stock
        )
        return {"answer": f"Low-stock products: {items}. Review stock and replenish as needed.", "data": {"low_stock_products": low_stock}}

    if any(phrase in question for phrase in ("most sold", "sold the most", "best selling", "top selling", "sabse zyada", "sabse jyada", "zyada bika", "kaunsa product", "सबसे ज्यादा", "सबसे अधिक", "कौन सा उत्पाद", "कौन सा प्रोडक्ट")):
        products = _top_products(db, current_user.id, 5, start, end)
        if not products:
            return {"answer": f"No product-linked invoice sales were found for {period_label}.", "data": {"top_products": []}}
        top = products[0]
        return {
            "answer": f"Top-selling product for {period_label}: {top['product']} ({top['quantity']:g} units sold).",
            "data": {"top_products": products, "period": {"label": period_label}},
        }

    if any(word in question for word in ("paid", "unpaid", "partially paid", "invoice status", "invoice kitne", "kitne invoice", "भुगतान", "बकाया")):
        query = db.query(func.lower(Invoice.status), func.count(Invoice.id), func.coalesce(func.sum(Invoice.total_amount), 0))
        if start:
            query = query.filter(Invoice.invoice_date >= start)
        if end:
            query = query.filter(Invoice.invoice_date < end)
        rows = query.filter(Invoice.user_id == current_user.id).group_by(func.lower(Invoice.status)).all()
        statuses = {status or "unknown": {"count": int(count), "invoice_total": _as_float(total)} for status, count, total in rows}
        paid = statuses.get("paid", {"count": 0, "invoice_total": 0})
        unpaid = statuses.get("unpaid", {"count": 0, "invoice_total": 0})
        partial = statuses.get("partially_paid", {"count": 0, "invoice_total": 0})
        answer = (
            f"For {period_label}, {paid['count']} invoice{'s' if paid['count'] != 1 else ''} "
            f"{'are' if paid['count'] != 1 else 'is'} marked PAID, "
            f"{unpaid['count']} are marked UNPAID, and {partial['count']} are marked PARTIALLY PAID. "
            "These counts use each invoice's saved status; invoice totals are not treated as collected payments."
        )
        return {"answer": answer, "data": {"period": {"label": period_label}, "invoice_statuses": statuses}}

    if any(word in question for word in ("profit", "profitability", "munafa", "munafe", "मुनाफा", "लाभ")):
        sales_count = db.query(Invoice.id).filter(Invoice.user_id == current_user.id)
        purchase_count = db.query(Purchase.id).filter(Purchase.user_id == current_user.id)
        if start:
            sales_count = sales_count.filter(Invoice.invoice_date >= start)
            purchase_count = purchase_count.filter(Purchase.purchase_date >= start)
        if end:
            sales_count = sales_count.filter(Invoice.invoice_date < end)
            purchase_count = purchase_count.filter(Purchase.purchase_date < end)
        if sales_count.count() == 0 or purchase_count.count() == 0:
            return {
                "answer": f"Profit cannot be estimated for {period_label}: both invoice sales and purchase records are required.",
                "data": {"period": {"label": period_label}, "profit_available": False},
            }
        sales = _sales_total_for_period(db, current_user.id, start, end)
        purchases = _purchase_total_for_period(db, current_user.id, start, end)
        profit = sales - purchases
        return {
            "answer": f"For {period_label}, the existing SmartGST sales-minus-purchases calculation is ₹{_as_float(profit):,.2f} (sales ₹{_as_float(sales):,.2f} minus purchases ₹{_as_float(purchases):,.2f}). This is the recorded gross comparison, not a complete net-profit statement.",
            "data": {
                "period": {"label": period_label},
                "sales": _as_float(sales),
                "purchases": _as_float(purchases),
                "profit_loss": _as_float(profit),
                "calculation": "invoice total_amount minus purchase total_amount",
            },
        }

    if any(word in question for word in ("purchase", "purchases", "kharid", "khareed", "kharida", "खरीद")):
        purchases = _purchase_total_for_period(db, current_user.id, start, end)
        return {
            "answer": f"Recorded purchases for {period_label}: ₹{_as_float(purchases):,.2f} (sum of purchase total_amount).",
            "data": {"period": {"label": period_label}, "purchases": _as_float(purchases)},
        }

    if any(word in question for word in ("customer", "who bought", "top customer")):
        query = (
            db.query(Customer.name, func.coalesce(func.sum(Invoice.total_amount), 0).label("revenue"))
            .join(Invoice, Invoice.customer_id == Customer.id)
            .filter(Customer.user_id == current_user.id, Invoice.user_id == current_user.id)
        )
        if start:
            query = query.filter(Invoice.invoice_date >= start)
        if end:
            query = query.filter(Invoice.invoice_date < end)
        rows = query.group_by(Customer.id, Customer.name).order_by(func.sum(Invoice.total_amount).desc()).limit(3).all()
        if not rows:
            return {"answer": f"No customer purchase history was found for {period_label}.", "data": {"customers": []}}
        customers = [{"name": name, "revenue": _as_float(revenue)} for name, revenue in rows]
        return {"answer": "Top customers by invoice sales: " + "; ".join(f"{c['name']} ₹{c['revenue']:,.2f}" for c in customers), "data": {"customers": customers}}

    comparison_requested = any(phrase in question for phrase in ("compare", "comparison", "versus", "vs", "compared", "badhi", "badi", "growth", "increase"))
    if comparison_requested:
        current_start, current_end, previous_start, previous_end = _month_range(today)
        current = _sales_total_for_period(db, current_user.id, current_start, current_end)
        previous = _sales_total_for_period(db, current_user.id, previous_start, previous_end)
        current_amount = _as_float(current)
        previous_amount = _as_float(previous)
        change = ((current - previous) / previous * 100) if previous else None
        current_period = {"start": current_start.isoformat(), "end": (current_end - timedelta(days=1)).isoformat()}
        previous_period = {"start": previous_start.isoformat(), "end": (previous_end - timedelta(days=1)).isoformat()}
        if change is None:
            answer = f"Current-period invoice sales are ₹{current_amount:,.2f}; the comparison period has zero sales, so a percentage change cannot be calculated."
        else:
            direction = "increased" if change > 0 else "decreased" if change < 0 else "were unchanged"
            answer = f"Sales {direction} by {abs(change):.2f}%: ₹{current_amount:,.2f} ({current_period['start']} to {current_period['end']}) versus ₹{previous_amount:,.2f} ({previous_period['start']} to {previous_period['end']})."
        return {
            "answer": answer,
            "data": {
                "comparison": {
                    "current": current_amount,
                    "previous": previous_amount,
                    "change_percent": round(change, 2) if change is not None else None,
                    "current_period": current_period,
                    "previous_period": previous_period,
                    "basis": money_basis,
                }
            },
        }

    if any(word in question for word in ("sale", "sales", "revenue", "sell", "sold", "bik", "bika", "income", "बिक्री", "बेचा", "बेचे")):
        sales = _sales_total_for_period(db, current_user.id, start, end)
        return {
            "answer": f"Recorded invoice sales for {period_label}: ₹{_as_float(sales):,.2f}, based on invoice total_amount (including its stored discount and tax calculations).",
            "data": {"sales": _as_float(sales), "period": {"label": period_label, "start": start.isoformat() if start else None, "end": (end - timedelta(days=1)).isoformat() if end else None}, "basis": money_basis},
        }

    if any(word in question for word in ("summary", "business", "overview")):
        summary = _get_business_summary(db, current_user.id)
        return {"answer": summary["summary"], "data": {"summary": summary}}

    return {
        "answer": "I can answer questions about recorded sales, purchases, top-selling products, stock, invoice statuses, customers, and the existing sales-minus-purchases calculation. I could not match this question to one of those data-backed queries.",
        "data": {},
    }


def _normalize_question(question: str) -> str:
    normalized = unicodedata.normalize("NFKC", question).casefold()
    normalized = re.sub(r"[^\w\s₹]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _query_period(question: str, today: date):
    if any(term in question for term in ("last month", "previous month", "pichle mahine", "pichlay mahine", "pichla mahina", "guzre mahine", "पिछले महीने", "पिछले माह")):
        current_month_start = today.replace(day=1)
        start = (current_month_start - timedelta(days=1)).replace(day=1)
        return start, current_month_start, f"last month ({start.isoformat()} to {(current_month_start - timedelta(days=1)).isoformat()})"
    if any(term in question for term in ("last year", "previous year", "pichle saal", "पिछले साल", "पिछले वर्ष")):
        start = date(today.year - 1, 1, 1)
        end = date(today.year, 1, 1)
        return start, end, f"last year ({start.isoformat()} to {(end - timedelta(days=1)).isoformat()})"
    if any(term in question for term in ("this year", "current year", "iss saal", "is saal", "इस साल", "इस वर्ष")):
        start = date(today.year, 1, 1)
        end = today + timedelta(days=1)
        return start, end, f"year to date ({start.isoformat()} to {today.isoformat()})"
    if any(term in question for term in ("today", "aaj", "आज")):
        return today, today + timedelta(days=1), f"today ({today.isoformat()})"
    if any(term in question for term in ("yesterday", "kal", "कल")):
        yesterday = today - timedelta(days=1)
        return yesterday, today, f"yesterday ({yesterday.isoformat()})"
    if any(term in question for term in ("last 7 days", "past 7 days", "previous 7 days")):
        start = today - timedelta(days=6)
        end = today + timedelta(days=1)
        return start, end, f"last 7 days ({start.isoformat()} to {today.isoformat()})"
    if any(term in question for term in ("this week", "current week", "iss hafte", "is hafte", "इस सप्ताह")):
        start = today - timedelta(days=today.weekday())
        end = today + timedelta(days=1)
        return start, end, f"this week ({start.isoformat()} to {today.isoformat()})"
    if any(term in question for term in ("this month", "current month", "iss mahine", "is mahine", "iss mahina", "is mahina", "is month", "month", "mahine", "mahina", "इस महीने", "इस माह")):
        start = today.replace(day=1)
        end = today + timedelta(days=1)
        return start, end, f"month to date ({start.isoformat()} to {today.isoformat()})"
    return None, None, "all recorded time"


@router.get("/ai/forecast/summary")
def get_forecast_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    today = date.today()
    history_start = today - timedelta(days=89)
    daily_rows = (
        db.query(Invoice.invoice_date, func.coalesce(func.sum(Invoice.total_amount), 0).label("total"))
        .filter(
            Invoice.user_id == current_user.id,
            Invoice.invoice_date >= history_start,
            Invoice.invoice_date <= today,
        )
        .group_by(Invoice.invoice_date)
        .order_by(Invoice.invoice_date.asc())
        .all()
    )

    daily_totals = defaultdict(float)
    for invoice_date, total in daily_rows:
        daily_totals[invoice_date] += _as_float(total)
    sales_days = sum(1 for total in daily_totals.values() if total > 0)
    first_recorded_day = min(daily_totals) if daily_totals else None
    available_days = (today - first_recorded_day).days + 1 if first_recorded_day else 0
    observed_data_points = len(daily_totals)
    last_28_days = [daily_totals[today - timedelta(days=offset)] for offset in range(27, -1, -1)]
    last_28_sales = sum(last_28_days)
    insufficient_reasons = []
    if available_days < 28:
        insufficient_reasons.append("at least 28 calendar days of recent history are required")
    if sales_days < 7:
        insufficient_reasons.append("sales must be recorded on at least 7 separate days in the last 90 days")
    if last_28_sales <= 0:
        insufficient_reasons.append("there are no recorded sales in the last 28 days")

    historical_context = {
        "period_start": history_start.isoformat(),
        "period_end": today.isoformat(),
        "calendar_days": 90,
        "days_with_sales": sales_days,
        "total_sales": round(sum(daily_totals.values()), 2),
        "last_28_days_sales": round(last_28_sales, 2),
        "daily_average_last_28_days": round(last_28_sales / 28, 2),
    }

    if insufficient_reasons:
        return {
            "status": "insufficient_data",
            "message": "Forecast unavailable: " + "; ".join(insufficient_reasons) + ".",
            "sales_forecast": None,
            "data_points": observed_data_points,
            "historical_context": historical_context,
            "model": "rolling_average",
        }

    daily_average = last_28_sales / 28
    tomorrow = today + timedelta(days=1)
    forecast = {
        "next_7_days": round(daily_average * 7, 2),
        "next_30_days": round(daily_average * 30, 2),
        "next_90_days": round(daily_average * 90, 2),
    }
    return {
        "status": "ok",
        "message": "Estimates use the average daily invoice sales from the last 28 calendar days, including days with no invoices.",
        "model": "rolling_average",
        "sales_forecast": forecast,
        "forecast_periods": {
            "next_7_days": {"start": tomorrow.isoformat(), "end": (tomorrow + timedelta(days=6)).isoformat()},
            "next_30_days": {"start": tomorrow.isoformat(), "end": (tomorrow + timedelta(days=29)).isoformat()},
            "next_90_days": {"start": tomorrow.isoformat(), "end": (tomorrow + timedelta(days=89)).isoformat()},
        },
        "historical_context": historical_context,
        "data_points": observed_data_points,
    }


@router.get("/ai/anomalies")
def get_anomalies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    anomalies: List[Dict[str, Any]] = []
    low_stock = _low_stock_products(db, current_user.id, limit=None)
    for item in low_stock:
        severity = "HIGH" if item["below_minimum"] else "MEDIUM"
        anomalies.append({
            "id": f"stock-{item['product_id']}",
            "entity_type": "inventory",
            "entity_id": item["product_id"],
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "anomaly_type": "low_stock_warning",
            "product": item["product"],
            "severity": severity,
            "reason": f"Available inventory across {item['branch_count']} affected branch(es) is {item['quantity']:g}, at or below the combined reorder thresholds of {item['reorder_level']:g}.",
            "recommended_action": "Review affected branch stock and replenish each low branch to its configured threshold.",
            "metrics": {
                "quantity": item["quantity"],
                "reorder_level": item["reorder_level"],
                "min_stock_level": item["min_stock_level"],
                "branch_count": item["branch_count"],
                "affected_branches": item["affected_branches"],
            },
            "status": "active",
        })

    return {"status": "ok", "count": len(anomalies), "anomalies": anomalies}


@router.get("/ai/alerts")
def get_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    summary = _get_business_summary(db, current_user.id, include_low_stock=False)
    alerts: List[Dict[str, Any]] = []

    change = summary["kpis"]["period_change_percent"]
    if change is not None and change < 0:
        current_period = summary["periods"]["current"]
        previous_period = summary["periods"]["previous"]
        alerts.append({
            "alert_id": "sales-drop",
            "type": "sales",
            "severity": "MEDIUM",
            "title": "Sales decline detected",
            "description": (
                f"Invoice sales decreased by {abs(change):.2f}% for {current_period['start']} to {current_period['end']} "
                f"compared with {previous_period['start']} to {previous_period['end']}."
            ),
            "recommended_action": "Review the sales and invoice records for both comparison periods.",
            "related_entity": "sales",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "resolved": False,
            "status": "active",
        })

    for item in _low_stock_products(db, current_user.id, limit=None):
        severity = "HIGH" if item["below_minimum"] else "MEDIUM"
        alerts.append({
            "alert_id": f"low-stock-{item['product_id']}",
            "type": "inventory",
            "severity": severity,
            "title": f"Low stock: {item['product']}",
            "description": f"{item['quantity']:g} combined units across {item['branch_count']} affected branch(es); combined reorder thresholds total {item['reorder_level']:g}.",
            "recommended_action": "Review affected branch stock and replenish each low branch to its configured threshold.",
            "related_entity": item["product"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "resolved": False,
            "status": "active",
        })

    return {"status": "ok", "count": len(alerts), "alerts": alerts}
