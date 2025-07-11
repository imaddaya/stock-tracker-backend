from models import StocksTable, PortfoliosTable , UsersTable
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import StockSymbol, StockSummary
from cruds import users as user_crud
from database import get_db
from dependencies import get_current_user_email
import httpx

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/summary/{symbol}", response_model = StockSummary)
def get_stock_summary(ticker: str, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email),):
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user or not user.alpha_vantage_api_key:
        raise HTTPException(status_code=400, detail="Alpha Vantage API key not set")

    stock = db.query(StocksTable).filter(StocksTable.stock_symbol == ticker.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock.stock_symbol}&apikey={user.alpha_vantage_api_key}"

    try:
        response = httpx.get(url, timeout=10)
        data = response.json().get("Global Quote", {})
        if response.status_code != 200 or "Global Quote" not in response.json():
            raise HTTPException(status_code=502, detail="Stock API error")

        return StockSummary(
            symbol=data.get("01. symbol", stock.stock_symbol),
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
        print(f"❌ Failed to fetch data for {stock.stock_symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary")
def get_portfolio_summary(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = user_crud.get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's portfolio
    portfolio = db.query(PortfoliosTable).filter(PortfoliosTable.user_id == user.id).all()
    if not portfolio:
        return []

    summaries = []
    for entry in portfolio:
        stock = db.query(StocksTable).filter(StocksTable.stock_symbol == entry.stock_symbol).first()
        if stock:
            summaries.append({
                "symbol": stock.stock_symbol,
                "name": stock.stock_company_name
            })

    return summaries

@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_stock_to_portfolio(ticker: StockSymbol, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    print(current_user_email)
    print(ticker)
    print(db)
    # Get user by email
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user)
    # Get stock by symbol (uppercase to be safe)
    stock = db.query(StocksTable).filter(StocksTable.stock_symbol == ticker.stock_symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    print(stock)
    # Check if stock already in user's portfolio
    existing = db.query(PortfoliosTable).filter(
        PortfoliosTable.user_id == user.id,
        PortfoliosTable.stock_symbol == stock.stock_symbol
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in portfolio")

    # Add to portfolio
    new_entry = PortfoliosTable(user_id=user.id, stock_symbol = stock.stock_symbol)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {"message": f"Stock {stock.stock_symbol} added to portfolio"}

@router.delete("/remove/{symbol}", status_code=status.HTTP_200_OK)
def remove_stock_from_portfolio(symbol: str, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if stock exists in portfolio
    portfolio_entry = db.query(PortfoliosTable).filter(
        PortfoliosTable.user_id == user.id,
        PortfoliosTable.stock_symbol == symbol.upper()
    ).first()
    
    if not portfolio_entry:
        raise HTTPException(status_code=404, detail="Stock not found in portfolio")

    # Remove from portfolio
    db.delete(portfolio_entry)
    db.commit()

    return {"message": f"Stock {symbol.upper()} removed from portfolio"}