from fastapi import APIRouter, Depends
from dependencies import get_current_user_email
from cruds import portfolios as portfolio_crud
from database import get_db
from utils.email import send_daily_summary_email
from sqlalchemy.orm import Session    

router = APIRouter(prefix="/email", tags=["email"])

@router.get("/send-summary")
def send_email_summary(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    from cruds import users as user_crud
    from models import PortfoliosTable, StocksTable, StockDataCache
    
    # Get user
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get portfolio stocks
    portfolio = db.query(PortfoliosTable).filter(PortfoliosTable.user_id == user.id).all()
    if not portfolio:
        return {"message": "Portfolio is empty"}

    # Prepare portfolio summary with cached stock data
    portfolio_summary = []
    for entry in portfolio:
        stock = db.query(StocksTable).filter(StocksTable.stock_symbol == entry.stock_symbol).first()
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
                    "change": f"${cached_data.change:.2f}"
                })
            else:
                # If no cached data, include stock but mark as N/A
                portfolio_summary.append({
                    "ticker": stock.stock_symbol,
                    "name": stock.stock_company_name,
                    "price": "N/A",
                    "change_percent": "N/A",
                    "change": "N/A"
                })

    if not portfolio_summary:
        return {"message": "No stock data available"}

    # Call utility to send email
    send_daily_summary_email(current_user_email, portfolio_summary)
    return {"message": "Email sent successfully"}
