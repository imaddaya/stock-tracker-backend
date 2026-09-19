from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user_email
from models import (
    PortfoliosTable,
    StocksTable,
    UsersTable,
)


router = APIRouter(
    prefix="/stocks",
    tags=["stocks"],
)


@router.get("")
def get_stocks(
    keywords: str | None = Query(
        None,
        min_length=1,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    user = (
        db.query(UsersTable)
        .filter(
            UsersTable.email
            == current_user_email
        )
        .first()
    )

    if not user:
        return []

    owned = (
        db.query(
            StocksTable.stock_symbol
        )
        .join(
            PortfoliosTable,
            PortfoliosTable.stock_symbol
            == StocksTable.stock_symbol,
        )
        .filter(
            PortfoliosTable.user_id == user.id
        )
        .all()
    )

    owned_tickers = [
        ticker[0]
        for ticker in owned
    ]

    query = db.query(
        StocksTable
    )

    if keywords:
        keyword_pattern = (
            f"%{keywords.lower()}%"
        )

        query = query.filter(
            or_(
                func.lower(
                    StocksTable.stock_symbol
                ).like(
                    keyword_pattern
                ),
                func.lower(
                    StocksTable.stock_company_name
                ).like(
                    keyword_pattern
                ),
            )
        )

    if owned_tickers:
        query = query.filter(
            ~StocksTable.stock_symbol.in_(
                owned_tickers
            )
        )

    results = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "symbol": stock.stock_symbol,
            "name": stock.stock_company_name,
        }
        for stock in results
    ]