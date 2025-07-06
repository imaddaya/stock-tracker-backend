from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import StockTicker, StockSummary
from cruds import portfolios as portfolio_crud, users as user_crud
from database import get_db
from dependencies import get_current_user_email
import httpx


router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/summary", response_model=list[StockSummary])
def get_portfolio_summary(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user or not user.alpha_vantage_api_key:
        raise HTTPException(status_code=400, detail="Alpha Vantage API key not set")

    portfolio = portfolio_crud.get_user_portfolio(db, current_user_email)
    if not portfolio:
        return []

    summaries = []
    for stock in portfolio:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock.symbol}&apikey={user.alpha_vantage_api_key}"

        try:
            response = httpx.get(url, timeout=10)
            data = response.json().get("Global Quote", {})
            if not data:
                continue

            summaries.append(StockSummary(
                symbol=data.get("01. symbol", stock.symbol),
                name=stock.name,
                price=float(data.get("05. price", 0.0)),
                change_percent=data.get("10. change percent", "0%"),
                country=stock.region or "N/A"
            ))
        except Exception as e:
            print(f"❌ Failed to fetch data for {stock.symbol}: {e}")
            continue

    return summaries
