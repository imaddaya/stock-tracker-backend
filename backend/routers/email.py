
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user_email
from database import get_db
from utils.email import send_daily_summary_email
from sqlalchemy.orm import Session
from models import UsersTable, PortfoliosTable, StocksTable, StockDataCache
from cruds import users as user_crud
from schemas import EmailReminderRequest
import re

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/reminder-settings")
def set_email_reminder(
    request: EmailReminderRequest, 
    db: Session = Depends(get_db), 
    current_user_email: str = Depends(get_current_user_email)
):
    """Set or update email reminder settings for the current user"""
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate time format if provided and enabled
    if request.reminder_time and request.enabled:
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', request.reminder_time):
            raise HTTPException(
                status_code=400, 
                detail="Invalid time format. Use HH:MM format (e.g., 09:30)"
            )
    
    # Update user settings
    user.email_reminder_enabled = request.enabled
    user.timezone = request.timezone or "UTC"
    if request.enabled and request.reminder_time:
        user.email_reminder_time = request.reminder_time
    elif not request.enabled:
        user.email_reminder_time = None  # Clear time when disabled
    
    try:
        db.commit()
        return {
            "message": "Email reminder settings updated successfully",
            "enabled": user.email_reminder_enabled,
            "reminder_time": user.email_reminder_time,
            "timezone": user.timezone
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/send-summary")
def send_email_summary(
    db: Session = Depends(get_db), 
    current_user_email: str = Depends(get_current_user_email)
):
    """Send daily portfolio summary email to the current user"""
    # Get user
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get portfolio stocks
    portfolio = db.query(PortfoliosTable).filter(PortfoliosTable.user_id == user.id).all()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio is empty - add some stocks first")

    # Prepare portfolio summary with cached stock data
    portfolio_summary = []
    for entry in portfolio:
        stock = db.query(StocksTable).filter(
            StocksTable.stock_symbol == entry.stock_symbol
        ).first()
        
        if stock:
            # Get cached stock data
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
                # If no cached data, include stock but mark as N/A
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

    if not portfolio_summary:
        raise HTTPException(status_code=404, detail="No stock data available in portfolio")

    # Send email
    try:
        send_daily_summary_email(current_user_email, portfolio_summary)
        return {
            "message": "Email sent successfully",
            "stocks_included": len(portfolio_summary),
            "recipient": current_user_email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/test-send")
def test_send_email(
    db: Session = Depends(get_db), 
    current_user_email: str = Depends(get_current_user_email)
):
    """Test endpoint to manually send an email summary"""
    try:
        result = send_email_summary(db, current_user_email)
        return {
            "message": "Test email sent successfully", 
            "details": result
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@router.get("/settings")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    """Get current email reminder settings for the user"""
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email_reminder_enabled": user.email_reminder_enabled or False,
        "email_reminder_time": user.email_reminder_time,
        "timezone": user.timezone or "UTC"
    }
