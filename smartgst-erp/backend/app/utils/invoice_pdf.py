from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _money(value: Decimal | float | int) -> str:
    return f"INR {Decimal(str(value or 0)):,.2f}"


def generate_invoice_pdf(output_path: str, invoice_number: str, customer_name: str, invoice_date: str, due_date: str | None, item_description: str, sku: str | None, quantity: float, unit_price: Decimal, gst_rate: float, subtotal: Decimal, total_tax: Decimal, total_amount: Decimal, paid_amount: Decimal, remaining_amount: Decimal, shop_name: str | None = None, company_gstin: str | None = None, company_address: str | None = None, company_state: str | None = None, company_state_code: str | None = None, company_phone: str | None = None, company_email: str | None = None, discount_amount: Decimal = Decimal("0"), cgst_amount: Decimal = Decimal("0"), sgst_amount: Decimal = Decimal("0"), igst_amount: Decimal = Decimal("0"), attached_image_path: str | None = None) -> str:
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    navy = colors.HexColor("#17324D")
    teal = colors.HexColor("#168C83")
    pale_teal = colors.HexColor("#EAF5F3")
    slate = colors.HexColor("#52616B")
    light_line = colors.HexColor("#DCE5EA")
    safe_shop_name = shop_name or "SmartGST AI ERP"
    safe_customer = customer_name or "Customer"
    safe_sku = sku or "N/A"
    safe_due_date = due_date or "-"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="InvoiceTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=navy, spaceAfter=2))
    styles.add(ParagraphStyle(name="SmallLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=slate, spaceAfter=2))
    styles.add(ParagraphStyle(name="SmallValue", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=navy))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12, textColor=navy))
    styles.add(ParagraphStyle(name="RightBody", parent=styles["Body"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontSize=8, leading=11, textColor=slate, alignment=TA_LEFT))

    def p(text: str, style: str = "Body") -> Paragraph:
        return Paragraph(str(text).replace("&", "&amp;"), styles[style])

    document = SimpleDocTemplate(
        str(output_path_obj),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=14 * mm,
        title=f"Invoice {invoice_number}",
        author=safe_shop_name,
    )

    story = []
    company_contact = "<br/>".join(filter(None, [company_address, f"GSTIN: {company_gstin}" if company_gstin else None, f"{company_state} ({company_state_code})" if company_state else None, company_phone, company_email]))
    header = Table([
        [p(safe_shop_name, "InvoiceTitle"), p("TAX INVOICE", "RightBody")],
        [p(company_contact or "Professional invoice", "SmallValue"), p(f"Invoice #{invoice_number}", "RightBody")],
    ], colWidths=[105 * mm, 73 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, -1), (-1, -1), 1.3, teal),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([header, Spacer(1, 8 * mm)])

    details = Table([
        [p("BILL TO", "SmallLabel"), p("INVOICE DETAILS", "SmallLabel")],
        [p(safe_customer, "SmallValue"), p(f"Date: {invoice_date}<br/>Due date: {safe_due_date}", "SmallValue")],
    ], colWidths=[89 * mm, 89 * mm])
    details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), pale_teal),
        ("BOX", (0, 0), (-1, -1), 0.6, light_line),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, light_line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([details, Spacer(1, 8 * mm)])

    item_table = Table([
        [p("DESCRIPTION", "SmallLabel"), p("SKU", "SmallLabel"), p("QTY", "SmallLabel"), p("UNIT PRICE", "SmallLabel"), p("GST", "SmallLabel"), p("AMOUNT", "SmallLabel")],
        [p(item_description), p(safe_sku), p(quantity), p(_money(unit_price)), p(f"{gst_rate}%"), p(_money(subtotal), "RightBody")],
    ], colWidths=[61 * mm, 24 * mm, 16 * mm, 28 * mm, 17 * mm, 32 * mm], repeatRows=1)
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, light_line),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, light_line),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([item_table, Spacer(1, 7 * mm)])

    summary = Table([
        [p("Subtotal", "Body"), p(_money(subtotal), "RightBody")],
        [p("Discount", "Body"), p(f"- {_money(discount_amount)}", "RightBody")],
        [p("CGST", "Body"), p(_money(cgst_amount), "RightBody")],
        [p("SGST", "Body"), p(_money(sgst_amount), "RightBody")],
        [p("IGST", "Body"), p(_money(igst_amount), "RightBody")],
        [p("GST / Tax", "Body"), p(_money(total_tax), "RightBody")],
        [p("TOTAL", "SmallLabel"), p(_money(total_amount), "RightBody")],
        [p("Paid", "Body"), p(_money(paid_amount), "RightBody")],
        [p("Balance due", "SmallLabel"), p(_money(remaining_amount), "RightBody")],
    ], colWidths=[55 * mm, 55 * mm], hAlign="RIGHT")
    summary.setStyle(TableStyle([
        ("LINEABOVE", (0, 4), (-1, 4), 1, teal),
        ("BACKGROUND", (0, 4), (-1, 4), pale_teal),
        ("LINEABOVE", (0, 6), (-1, 6), 1, teal),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([summary, Spacer(1, 12 * mm)])
    if attached_image_path:
        story.extend([
            p("ATTACHED PHOTO", "SmallLabel"),
            Spacer(1, 2 * mm),
            Image(attached_image_path, width=document.width, height=105 * mm, kind="proportional"),
            Spacer(1, 8 * mm),
        ])
    story.extend([p("Thank you for your business.", "Footer"), p("This is a computer-generated invoice and does not require a signature.", "Footer")])

    document.build(story)
    return str(output_path_obj)
