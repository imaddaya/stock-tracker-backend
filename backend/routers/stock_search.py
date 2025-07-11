from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import StocksTable, PortfoliosTable , UsersTable
from database import get_db
from dependencies import get_current_user_email

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("")
def get_stocks(
    keywords: str = Query(None, min_length=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    # get user id by email
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        return []  # or raise HTTPException(status_code=404, detail="User not found")

    # get symbols user already owns
    owned = (db.query(StocksTable.stock_symbol).join(PortfoliosTable, PortfoliosTable.stock_symbol == StocksTable.stock_symbol)
             .filter(PortfoliosTable.user_id == user.id).all())
    owned_tickers = [t[0] for t in owned]

    # base stock query
    query = db.query(StocksTable)

    # filter by search keywords if present
    if keywords:
        keyword_pattern = f"%{keywords.lower()}%"
        query = query.filter(
            or_(
                func.lower(StocksTable.stock_symbol).like(keyword_pattern),
                func.lower(StocksTable.stock_company_name).like(keyword_pattern)
            )
        )

    # exclude owned stocks
    if owned_tickers:
        query = query.filter(~StocksTable.stock_symbol.in_(owned_tickers))

    # pagination
    results = query.offset(offset).limit(limit).all()

    return [{"symbol": stock.stock_symbol, "name": stock.stock_company_name} for stock in results]
