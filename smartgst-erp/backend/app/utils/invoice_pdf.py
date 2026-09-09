import os
from decimal import Decimal
from pathlib import Path


def _escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_invoice_pdf(output_path: str, invoice_number: str, customer_name: str, invoice_date: str, due_date: str | None, item_description: str, sku: str | None, quantity: float, unit_price: Decimal, gst_rate: float, subtotal: Decimal, total_tax: Decimal, total_amount: Decimal, paid_amount: Decimal, remaining_amount: Decimal) -> str:
    safe_customer = customer_name or "Customer"
    safe_sku = sku or "N/A"
    safe_due_date = due_date or "-"

    lines = [
        "SMARTGST AI ERP INVOICE",
        f"Invoice #: {invoice_number}",
        f"Date: {invoice_date}",
        f"Due Date: {safe_due_date}",
        "",
        f"Customer: {safe_customer}",
        f"SKU: {safe_sku}",
        f"Item: {item_description}",
        f"Qty: {quantity}",
        f"Unit Price: INR {float(unit_price):.2f}",
        f"GST %: {gst_rate}",
        f"Subtotal: INR {float(subtotal):.2f}",
        f"Tax: INR {float(total_tax):.2f}",
        f"Total Amount: INR {float(total_amount):.2f}",
        f"Paid Amount: INR {float(paid_amount):.2f}",
        f"Remaining Amount: INR {float(remaining_amount):.2f}",
        "",
        "Thank you for your business.",
    ]

    content_stream = "BT\n/F1 11 Tf\n72 760 Td\n"
    for index, line in enumerate(lines):
        escaped_line = _escape_pdf(line)
        if index == 0:
            content_stream += f"({escaped_line}) Tj\n"
        else:
            content_stream += "T*\n"
            content_stream += f"({escaped_line}) Tj\n"
    content_stream += "ET\n"

    objects = []
    object_bodies = []

    object_bodies.append("<< /Type /Catalog /Pages 2 0 R >>")
    object_bodies.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    object_bodies.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")
    object_bodies.append(f"<< /Length {len(content_stream.encode('latin-1'))} >>\nstream\n{content_stream}endstream")
    object_bodies.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf_parts = ["%PDF-1.4\n"]
    offsets = [0]
    for index, body in enumerate(object_bodies, start=1):
        offsets.append(len("".join(pdf_parts).encode("latin-1")))
        pdf_parts.append(f"{index} 0 obj\n{body}\nendobj\n")

    pdf_bytes = "".join(pdf_parts).encode("latin-1")
    xref_offset = len(pdf_bytes)
    xref = [f"xref\n0 {len(object_bodies) + 1}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n")
    xref.append(f"trailer\n<< /Size {len(object_bodies) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n")

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with output_path_obj.open("wb") as fh:
        fh.write(pdf_bytes)
        fh.write("".join(xref).encode("latin-1"))

    return str(output_path_obj)
