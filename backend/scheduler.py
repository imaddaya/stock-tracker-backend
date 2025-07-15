
import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models import UsersTable
from utils.email import send_daily_summary_email
from routers.email import send_email_summary

def send_daily_emails():
    """Send daily summary emails to users whose reminder time has arrived"""
    db = next(get_db())
    
    # Get current time in HH:MM format
    current_time = datetime.now().strftime("%H:%M")
    
    # Get users with email reminders enabled and matching reminder time
    users = db.query(UsersTable).filter(
        UsersTable.email_reminder_enabled == True,
        UsersTable.email_reminder_time == current_time
    ).all()
    
    for user in users:
        try:
            # Call the same function used in the API endpoint
            send_email_summary(db, user.email)
            print(f"✅ Daily email sent to {user.email} at {current_time}")
        except Exception as e:
            print(f"❌ Failed to send email to {user.email}: {e}")
    
    db.close()

def start_scheduler():
    """Start the background scheduler that checks every minute"""
    # Schedule to run every minute to check for user-specific times
    schedule.every().minute.do(send_daily_emails)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📅 Email scheduler started - checking user reminder times every minute")
