from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import Stock, Portfolio
from database import get_db
from dependencies import get_current_user_email
from models import User, Stock, Portfolio


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
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        return []  # or raise HTTPException(status_code=404, detail="User not found")

    # get symbols user already owns
    owned = (
        db.query(Stock.symbol)
        .join(Portfolio, Portfolio.stock_id == Stock.id)
        .filter(Portfolio.user_id == user.id)
        .all()
    )
    owned_tickers = [t[0] for t in owned]

    # base stock query
    query = db.query(Stock)

    # filter by search keywords if present
    if keywords:
        keyword_pattern = f"%{keywords.lower()}%"
        query = query.filter(
            or_(
                func.lower(Stock.symbol).like(keyword_pattern),
                func.lower(Stock.name).like(keyword_pattern)
            )
        )

    # exclude owned stocks
    if owned_tickers:
        query = query.filter(~Stock.symbol.in_(owned_tickers))

    # pagination
    results = query.offset(offset).limit(limit).all()

    return [{"symbol": stock.symbol, "name": stock.name} for stock in results]
