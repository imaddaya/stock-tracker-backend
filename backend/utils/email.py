import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import get_settings

settings = get_settings()

def send_email(subject: str, recipient: str, html_content: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_ADDRESS
    message["To"] = recipient
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.EMAIL_ADDRESS,settings.EMAIL_PASSWORD)  # ✅ Now both are safe strings
            server.sendmail(settings.EMAIL_ADDRESS, recipient, message.as_string())
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        raise

def send_verification_email(email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/email-verified?token={token}"
    html = f"""
    <h3>Verify your email</h3>
    <p>Click the link below to verify your email address:</p>
    <a href="{verification_link}" style="color:#0070f3;">Verify Email</a>
    """
    send_email("Please verify your email", email, html)

def send_password_reset_email(email: str, token: str):
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <h3>Reset your password</h3>
    <p>Click the link below to reset your password:</p>
    <a href="{reset_link}" style="color:#0070f3;">Reset Password</a>
    <p>This link will expire in 1 hour.</p>
    """
    send_email("Reset your password", email, html)

def send_account_deletion_email(email: str, token: str):
    deletion_link = f"{settings.FRONTEND_URL}/confirm-account-deletion?token={token}"
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
    html = "<h3>📈 Daily Stock Portfolio Summary</h3>"
    html += "<p>Here's your comprehensive daily portfolio update:</p>"
    html += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; font-size: 14px;'>"
    html += """
    <tr style='background-color: #f2f2f2;'>
        <th>Ticker</th>
        <th>Company</th>
        <th>Current Price</th>
        <th>Change ($)</th>
        <th>Change (%)</th>
        <th>Open</th>
        <th>High</th>
        <th>Low</th>
        <th>Volume</th>
        <th>Previous Close</th>
        <th>Trading Day</th>
    </tr>
    """

    for stock in portfolio_summary:
        # Color coding for positive/negative changes
        change_color = "green"
        if stock.get('change_percent', 'N/A') != 'N/A' and stock.get('change_percent').startswith('-'):
            change_color = "red"
        elif stock.get('change_percent') == 'N/A':
            change_color = "gray"
            
        html += f"""
        <tr>
            <td><strong>{stock.get('ticker', 'N/A')}</strong></td>
            <td>{stock.get('name', 'N/A')}</td>
            <td><strong>{stock.get('price', 'N/A')}</strong></td>
            <td style='color: {change_color}; font-weight: bold;'>{stock.get('change', 'N/A')}</td>
            <td style='color: {change_color}; font-weight: bold;'>{stock.get('change_percent', 'N/A')}</td>
            <td>{stock.get('open', 'N/A')}</td>
            <td>{stock.get('high', 'N/A')}</td>
            <td>{stock.get('low', 'N/A')}</td>
            <td>{stock.get('volume', 'N/A')}</td>
            <td>{stock.get('previous_close', 'N/A')}</td>
            <td>{stock.get('latest_trading_day', 'N/A')}</td>
        </tr>
        """

    html += "</table>"
    html += "<br><p><small>📅 Data may be delayed. For real-time quotes, please visit your portfolio dashboard.</small></p>"
    html += "<br><p style='color: #666;'><small>This is an automated daily summary email. You can modify your email preferences in your account settings.</small></p>"

    send_email("📊 Daily Stock Portfolio Summary", email, html)