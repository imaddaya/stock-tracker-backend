from models import Stock, Portfolio , User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import StockTicker, StockSummary
from cruds import portfolios as portfolio_crud, users as user_crud
from database import get_db
from dependencies import get_current_user_email
import httpx



router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/summary/{symbol}", response_model=StockSummary)
def get_stock_summary(
    symbol: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user or not user.alpha_vantage_api_key:
        raise HTTPException(status_code=400, detail="Alpha Vantage API key not set")

    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock.symbol}&apikey={user.alpha_vantage_api_key}"

    try:
        response = httpx.get(url, timeout=10)
        data = response.json().get("Global Quote", {})
        if response.status_code != 200 or "Global Quote" not in response.json():
            raise HTTPException(status_code=502, detail="Stock API error")

        return StockSummary(
            symbol=data.get("01. symbol", stock.symbol),
            open=float(data.get("02. open", 0.0)),
            high=float(data.get("03. high", 0.0)),
            low=float(data.get("04. low", 0.0)),
            price=float(data.get("05. price", 0.0)),
            volume=int(data.get("06. volume", 0)),
            latest_trading_day=data.get("07. latest trading day", ""),
            previous_close=float(data.get("08. previous close", 0.0)),
            change=float(data.get("09. change", 0.0)),
            change_percent=data.get("10. change percent", "0%")
        )
    except Exception as e:
        print(f"❌ Failed to fetch data for {stock.symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_stock_to_portfolio(
    ticker: StockTicker,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    # Get user by email
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get stock by symbol (uppercase to be safe)
    stock = db.query(Stock).filter(Stock.symbol == ticker.ticker.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Check if stock already in user's portfolio
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == user.id,
        Portfolio.stock_id == stock.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in portfolio")

    # Add to portfolio
    new_entry = Portfolio(user_id=user.id, stock_id=stock.id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {"message": f"Stock {stock.symbol} added to portfolio"}
