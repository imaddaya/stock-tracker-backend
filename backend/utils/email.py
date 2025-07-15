import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from config import FRONTEND_URL  

EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

def send_email(subject: str, recipient: str, html_content: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = recipient
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # ✅ Now both are safe strings
            server.sendmail(EMAIL_ADDRESS, recipient, message.as_string())
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        raise

def send_verification_email(email: str, token: str):
    verification_link = f"{FRONTEND_URL}/email-verified?token={token}"
    html = f"""
    <h3>Verify your email</h3>
    <p>Click the link below to verify your email address:</p>
    <a href="{verification_link}" style="color:#0070f3;">Verify Email</a>
    """
    send_email("Please verify your email", email, html)

def send_password_reset_email(email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <h3>Reset your password</h3>
    <p>Click the link below to reset your password:</p>
    <a href="{reset_link}" style="color:#0070f3;">Reset Password</a>
    <p>This link will expire in 1 hour.</p>
    """
    send_email("Reset your password", email, html)

def send_account_deletion_email(email: str, token: str):
    deletion_link = f"{FRONTEND_URL}/confirm-account-deletion?token={token}"
    html = f"""
    <h3>⚠️ Account Deletion Confirmation</h3>
    <p>You have requested to delete your account. This action is <strong>PERMANENT</strong> and cannot be undone.</p>
    <p>Click the link below to permanently delete your account:</p>
    <a href="{deletion_link}" style="color:#dc3545; font-weight: bold;">DELETE MY ACCOUNT PERMANENTLY</a>
    <p><strong>This link will expire in 30 minutes.</strong></p>
    <p>If you did not request this deletion, please ignore this email.</p>
    """
    send_email("🚨 Confirm Account Deletion", email, html)

def send_daily_summary_email(email: str, portfolio_summary: list):
    html = "<h3>📈 Daily Stock Summary</h3>"
    html += "<table border='1' cellpadding='6' cellspacing='0'>"
    html += "<tr><th>Ticker</th><th>Price</th><th>Change %</th></tr>"

    for stock in portfolio_summary:
        html += f"<tr><td>{stock.get('ticker')}</td><td>{stock.get('price')}</td><td>{stock.get('change_percent')}</td></tr>"

    html += "</table>"

    send_email("📊 Daily Stock Portfolio Summary", email, html)