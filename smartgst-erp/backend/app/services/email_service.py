import smtplib
from html import escape
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_otp_email(email: str, otp_code: str) -> bool:
        """Send OTP email to user"""
        try:
            subject = "SmartGST AI ERP - Email Verification OTP"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .otp-box {{ background-color: #fff; padding: 20px; text-align: center; margin: 20px 0; border: 2px solid #3498db; border-radius: 5px; }}
                    .otp-code {{ font-size: 32px; font-weight: bold; color: #3498db; letter-spacing: 5px; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>SmartGST AI ERP</h1>
                    </div>
                    <div class="content">
                        <h2>Email Verification</h2>
                        <p>Hello,</p>
                        <p>You have requested to verify your email address for SmartGST AI ERP. Please use the following One-Time Password (OTP) to complete your verification:</p>
                        <div class="otp-box">
                            <p class="otp-code">{otp_code}</p>
                            <p>This OTP is valid for 10 minutes</p>
                        </div>
                        <p>If you did not request this verification, please ignore this email.</p>
                        <p>Do not share this OTP with anyone.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 SmartGST AI ERP. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return EmailService._send_email(email, subject, html_body)
        except Exception as e:
            print(f"Error sending OTP email: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_reminder(email: str, customer_name: str, invoice_number: str, amount: float, due_date: str) -> bool:
        """Send payment reminder email"""
        try:
            subject = f"Payment Reminder - Invoice {invoice_number}"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .info-box {{ background-color: #fff; padding: 20px; margin: 20px 0; border-left: 4px solid #f39c12; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>SmartGST AI ERP</h1>
                    </div>
                    <div class="content">
                        <h2>Payment Reminder</h2>
                        <p>Hello {customer_name},</p>
                        <p>This is a friendly reminder that your payment is due.</p>
                        <div class="info-box">
                            <p><strong>Invoice Number:</strong> {invoice_number}</p>
                            <p><strong>Amount Due:</strong> ₹ {amount}</p>
                            <p><strong>Due Date:</strong> {due_date}</p>
                        </div>
                        <p>Please arrange payment at your earliest convenience. If you have already made the payment, please ignore this reminder.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 SmartGST AI ERP. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return EmailService._send_email(email, subject, html_body)
        except Exception as e:
            print(f"Error sending payment reminder: {str(e)}")
            return False
    
    @staticmethod
    def send_low_stock_alert(email: str, product_name: str, current_stock: float, min_stock: float) -> bool:
        """Send low stock alert email"""
        try:
            subject = f"Low Stock Alert - {product_name}"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .alert-box {{ background-color: #fff; padding: 20px; margin: 20px 0; border-left: 4px solid #e74c3c; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Stock Alert</h1>
                    </div>
                    <div class="content">
                        <h2>Low Stock Warning</h2>
                        <div class="alert-box">
                            <p><strong>Product:</strong> {product_name}</p>
                            <p><strong>Current Stock:</strong> {current_stock}</p>
                            <p><strong>Minimum Stock Level:</strong> {min_stock}</p>
                        </div>
                        <p>The stock level for {product_name} has fallen below the minimum threshold. Please consider placing a reorder soon.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 SmartGST AI ERP. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return EmailService._send_email(email, subject, html_body)
        except Exception as e:
            print(f"Error sending stock alert: {str(e)}")
            return False
    
    @staticmethod
    def send_invoice_pdf_email(
        email: str,
        customer_name: str,
        invoice_number: str,
        invoice_pdf_path: str,
    ) -> bool:
        """Send the invoice PDF, which includes any uploaded photo, to the customer."""
        try:
            if not settings.ENABLE_EMAIL_NOTIFICATIONS:
                return False

            subject = f"Invoice {invoice_number} - SmartGST AI ERP"
            safe_customer_name = escape(customer_name or "Customer")
            safe_invoice_number = escape(invoice_number)
            html_body = f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8"></head>
            <body>
                <div style="max-width:620px;margin:0 auto;font-family:Arial,sans-serif;color:#17324d;border:1px solid #dce5ea;border-radius:8px;overflow:hidden">
                    <div style="background:#17324d;color:#fff;padding:24px 28px">
                        <div style="font-size:12px;letter-spacing:1.5px;color:#9de0d8">SMARTGST AI ERP</div>
                        <h2 style="margin:8px 0 0;font-size:24px">Your invoice is ready</h2>
                    </div>
                    <div style="padding:28px">
                        <p style="font-size:16px">Hello {safe_customer_name},</p>
                        <p>Please find your invoice <strong>#{safe_invoice_number}</strong> attached as a PDF.</p>
                        <p style="color:#52616b">The attachment is formatted for easy viewing, printing, and record keeping.</p>
                        <p style="margin-top:28px">Thank you for your business.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            attachment_path = Path(invoice_pdf_path)
            if not attachment_path.is_file():
                return False
            with attachment_path.open("rb") as fh:
                part = MIMEApplication(fh.read(), _subtype="pdf", Name=attachment_path.name)
            part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, email, msg.as_string())

            return True
        except Exception as e:
            print(f"Error sending invoice email: {str(e)}")
            return False

    @staticmethod
    def _send_email(to_email: str, subject: str, html_body: str) -> bool:
        """Internal method to send email via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            
            part = MIMEText(html_body, "html")
            msg.attach(part)
            
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"Error in SMTP communication: {str(e)}")
            return False
