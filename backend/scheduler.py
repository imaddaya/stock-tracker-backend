
import schedule
import time
import threading
from sqlalchemy.orm import Session
from database import get_db
from models import UsersTable
from utils.email import send_daily_summary_email
from routers.email import send_email_summary

def send_daily_emails():
    """Send daily summary emails to all users with email reminders enabled"""
    db = next(get_db())
    
    # Get all users with email reminders enabled
    users = db.query(UsersTable).filter(UsersTable.email_reminder_enabled == True).all()
    
    for user in users:
        try:
            # Call the same function used in the API endpoint
            send_email_summary(db, user.email)
            print(f"✅ Daily email sent to {user.email}")
        except Exception as e:
            print(f"❌ Failed to send email to {user.email}: {e}")
    
    db.close()

def start_scheduler():
    """Start the background scheduler"""
    schedule.every().day.at("09:00").do(send_daily_emails)  # Send at 9 AM daily
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📅 Email scheduler started - daily emails at 9:00 AM")
