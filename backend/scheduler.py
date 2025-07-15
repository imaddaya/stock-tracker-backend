
import schedule
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UsersTable, PortfoliosTable, StocksTable, StockDataCache
from utils.email import send_daily_summary_email
import pytz

def send_scheduled_emails():
    """Send daily summary emails to users based on their scheduled reminder times in their timezone"""
    db: Session = SessionLocal()
    try:
        # Get all users with email reminders enabled
        users = db.query(UsersTable).filter(
            UsersTable.email_reminder_enabled == True,
            UsersTable.email_reminder_time.isnot(None)
        ).all()

        print(f"🕐 Checking scheduled emails - Found {len(users)} users with reminders enabled")

        for user in users:
            try:
                # Get user's timezone
                user_tz = pytz.timezone(user.timezone or "UTC")
                
                # Get current time in user's timezone
                user_current_time = datetime.now(user_tz).strftime("%H:%M")
                
                # Check if it's time to send email for this user
                if user_current_time == user.email_reminder_time:
                    print(f"⏰ Time to send email to {user.email} (their time: {user_current_time}, timezone: {user.timezone})")
                    
                    # Get user's portfolio stocks
                    portfolio = db.query(PortfoliosTable).filter(
                        PortfoliosTable.user_id == user.id
                    ).all()

                    if not portfolio:
                        print(f"⚠️ User {user.email} has empty portfolio - skipping email")
                        continue

                    # Prepare portfolio summary with cached stock data
                    portfolio_summary = []
                    for entry in portfolio:
                        stock = db.query(StocksTable).filter(
                            StocksTable.stock_symbol == entry.stock_symbol
                        ).first()

                        if stock:
                            # Get cached stock data for this user and stock
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
                                # Include stock but mark data as unavailable
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

                    # Send email if we have portfolio data
                    if portfolio_summary:
                        send_daily_summary_email(user.email, portfolio_summary)
                        print(f"📧 Sent scheduled email to {user.email} at {user_current_time} {user.timezone} ({len(portfolio_summary)} stocks)")
                    else:
                        print(f"⚠️ No portfolio data available for {user.email} - skipping email")

            except pytz.exceptions.UnknownTimeZoneError:
                print(f"❌ Invalid timezone '{user.timezone}' for user {user.email}")
            except Exception as e:
                print(f"❌ Failed to send scheduled email to {user.email}: {str(e)}")

    except Exception as e:
        print(f"❌ Scheduler error: {str(e)}")
    finally:
        db.close()

def run_scheduler():
    """Run the scheduler in a background thread"""
    # Schedule to check every minute for users who need emails
    schedule.every().minute.do(send_scheduled_emails)

    print("📅 Email scheduler running - checking every minute for scheduled emails (timezone-aware)")

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Check every second for pending jobs
        except Exception as e:
            print(f"❌ Scheduler thread error: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

def start_scheduler():
    """Start the email scheduler in a background daemon thread"""
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("🚀 Email scheduler started successfully (timezone-aware)")
        return True
    except Exception as e:
        print(f"❌ Failed to start email scheduler: {str(e)}")
        return False
