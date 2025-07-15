
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
import schedule
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UsersTable, PortfoliosTable, StocksTable, StockDataCache
from utils.email import send_daily_summary_email

def send_scheduled_emails():
    """Send emails to users based on their scheduled reminder times"""
    db: Session = SessionLocal()
    try:
        current_time = datetime.now().strftime("%H:%M")
        
        # Find users with email reminders enabled for current time
        users = db.query(UsersTable).filter(
            UsersTable.email_reminder_enabled == True,
            UsersTable.email_reminder_time == current_time
        ).all()
        
        for user in users:
            try:
                # Get portfolio stocks for this user
                portfolio = db.query(PortfoliosTable).filter(PortfoliosTable.user_id == user.id).all()
                if not portfolio:
                    continue

                # Prepare portfolio summary with cached stock data
                portfolio_summary = []
                for entry in portfolio:
                    stock = db.query(StocksTable).filter(StocksTable.stock_symbol == entry.stock_symbol).first()
                    if stock:
                        cached_data = db.query(StockDataCache).filter(
                            StockDataCache.user_id == user.id,
                            StockDataCache.stock_symbol == stock.stock_symbol
                        ).first()
                        
                        if cached_data:
                            portfolio_summary.append({
                                "ticker": stock.stock_symbol,
                                "name": stock.stock_company_name,
                                "price": f"${cached_data.current_price:.2f}",
                                "change_percent": cached_data.change_percent,
                                "change": f"${cached_data.change:.2f}",
                                "open": f"${cached_data.open_price:.2f}",
                                "high": f"${cached_data.high_price:.2f}",
                                "low": f"${cached_data.low_price:.2f}",
                                "volume": f"{cached_data.volume:,}",
                                "latest_trading_day": cached_data.latest_trading_day,
                                "previous_close": f"${cached_data.previous_close:.2f}"
                            })
                        else:
                            portfolio_summary.append({
                                "ticker": stock.stock_symbol,
                                "name": stock.stock_company_name,
                                "price": "N/A",
                                "change_percent": "N/A",
                                "change": "N/A",
                                "open": "N/A",
                                "high": "N/A",
                                "low": "N/A",
                                "volume": "N/A",
                                "latest_trading_day": "N/A",
                                "previous_close": "N/A"
                            })

                if portfolio_summary:
                    send_daily_summary_email(user.email, portfolio_summary)
                    print(f"📧 Sent scheduled email to {user.email} at {current_time}")
                    
            except Exception as e:
                print(f"❌ Failed to send email to {user.email}: {e}")
                
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
    finally:
        db.close()

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Check every minute for users who need emails
    schedule.every().minute.do(send_scheduled_emails)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """Start the email scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📅 Email scheduler started - checking user reminder times every minute")
