from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

from openpyxl import load_workbook

from app.utils.invoice_excel import generate_invoice_excel


def test_invoice_excel_includes_discount():
    invoice = SimpleNamespace(
        invoice_number="INV-TEST",
        invoice_date="2026-11-03",
        subtotal=Decimal("900.00"),
        discount_amount=Decimal("100.00"),
        total_tax=Decimal("162.00"),
        total_amount=Decimal("1062.00"),
        paid_amount=Decimal("0.00"),
    )
    item = SimpleNamespace(
        description="Sample item",
        product=None,
        quantity=1,
        unit_price=Decimal("1000.00"),
        gst_rate=18,
        subtotal=Decimal("900.00"),
        tax_amount=Decimal("162.00"),
        line_total=Decimal("1062.00"),
    )

    workbook_stream = generate_invoice_excel(invoice, "Customer", item, None)
    sheet = load_workbook(BytesIO(workbook_stream.getvalue()), data_only=True).active
    summary = {
        sheet.cell(row, 1).value: sheet.cell(row, 2).value
        for row in range(11, sheet.max_row + 1)
    }

    assert summary["Discount"] == 100
    assert summary["Total Amount"] == 1062
