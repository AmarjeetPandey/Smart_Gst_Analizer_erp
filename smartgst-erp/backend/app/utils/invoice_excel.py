from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def generate_invoice_excel(invoice, customer_name: str, item, shop_name: str | None) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Invoice"

    title = shop_name or "SmartGST AI ERP"
    sheet.append([title])
    sheet.append(["TAX INVOICE"])
    sheet.append(["Invoice Number", invoice.invoice_number])
    sheet.append(["Invoice Date", str(invoice.invoice_date)])
    sheet.append(["Customer", customer_name or "Customer"])
    sheet.append([])
    sheet.append(["Description", "SKU", "Quantity", "Unit Price", "GST %", "Subtotal", "Tax", "Total"])
    sheet.append([
        item.description,
        item.product.sku if item.product else "",
        item.quantity,
        float(item.unit_price),
        item.gst_rate,
        float(item.subtotal),
        float(item.tax_amount),
        float(item.line_total),
    ])
    sheet.append([])
    sheet.append(["Subtotal", float(invoice.subtotal)])
    sheet.append(["Discount", float(invoice.discount_amount or 0)])
    sheet.append(["Tax", float(invoice.total_tax)])
    sheet.append(["Total Amount", float(invoice.total_amount)])
    sheet.append(["Paid Amount", float(invoice.paid_amount)])
    sheet.append(["Remaining Amount", float(invoice.total_amount - invoice.paid_amount)])

    sheet["A1"].font = Font(size=18, bold=True, color="1F73B7")
    sheet["A2"].font = Font(size=13, bold=True)
    for cell in sheet["A7:H7"][0]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F73B7")
    for column, width in {"A": 28, "B": 18, "C": 12, "D": 14, "E": 10, "F": 14, "G": 14, "H": 14}.items():
        sheet.column_dimensions[column].width = width

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output