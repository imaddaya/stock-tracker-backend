import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cruds import users as user_crud
from database import get_db
from dependencies import get_current_user_email
from models import (
    PortfoliosTable,
    StockDataCache,
    StocksTable,
    UsersTable,
)
from schemas import StockSummary, StockSymbol, WeeklyStockData


router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)


def update_cache_from_summary(
    cache: StockDataCache,
    response_data: dict,
) -> None:
    cache.open_price = response_data["open"]
    cache.high_price = response_data["high"]
    cache.low_price = response_data["low"]
    cache.current_price = response_data["price"]
    cache.volume = response_data["volume"]
    cache.latest_trading_day = response_data[
        "latest_trading_day"
    ]
    cache.previous_close = response_data[
        "previous_close"
    ]
    cache.change = response_data["change"]
    cache.change_percent = response_data[
        "change_percent"
    ]
    cache.last_updated = func.now()


@router.get(
    "/weekly-data/{symbol}",
    response_model=WeeklyStockData,
)
def get_weekly_stock_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    user = user_crud.get_user_by_email(
        db,
        current_user_email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.alpha_vantage_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha Vantage API key not set",
        )

    normalized_symbol = symbol.upper()

    portfolio_entry = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id == user.id,
            PortfoliosTable.stock_symbol
            == normalized_symbol,
        )
        .first()
    )

    if not portfolio_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your portfolio",
        )

    stock = (
        db.query(StocksTable)
        .filter(
            StocksTable.stock_symbol
            == normalized_symbol
        )
        .first()
    )

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    try:
        response = httpx.get(
            "https://www.alphavantage.co/query",
            params={
                "function": (
                    "TIME_SERIES_WEEKLY_ADJUSTED"
                ),
                "symbol": stock.stock_symbol,
                "apikey": user.alpha_vantage_api_key,
            },
            timeout=15,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Stock API error",
            )

        data = response.json()

        if "Error Message" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid stock symbol",
            )

        if (
            "Note" in data
            or "Information" in data
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "API call frequency limit reached"
                ),
            )

        weekly_data = data.get(
            "Weekly Adjusted Time Series",
            {},
        )

        if not weekly_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No weekly data available "
                    "for this stock"
                ),
            )

        formatted_data = []

        for date, values in weekly_data.items():
            formatted_data.append(
                {
                    "date": date,
                    "open": float(
                        values["1. open"]
                    ),
                    "high": float(
                        values["2. high"]
                    ),
                    "low": float(
                        values["3. low"]
                    ),
                    "close": float(
                        values["4. close"]
                    ),
                    "adjusted_close": float(
                        values[
                            "5. adjusted close"
                        ]
                    ),
                    "volume": int(
                        values["6. volume"]
                    ),
                    "dividend_amount": float(
                        values[
                            "7. dividend amount"
                        ]
                    ),
                }
            )

        formatted_data.sort(
            key=lambda item: item["date"],
            reverse=True,
        )

        return {
            "symbol": stock.stock_symbol,
            "name": stock.stock_company_name,
            "metadata": data.get(
                "Meta Data",
                {},
            ),
            "weekly_data": formatted_data[:52],
        }

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=(
                status.HTTP_504_GATEWAY_TIMEOUT
            ),
            detail=(
                "Request timeout - "
                "API service unavailable"
            ),
        )

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to communicate with "
                "stock data provider"
            ),
        )

    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Invalid response received from "
                "stock data provider"
            ),
        )

    except Exception as exc:
        print(
            "Failed to fetch weekly data "
            f"for {stock.stock_symbol}: {exc}"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal server error",
        )


@router.get(
    "/monthly-data/{symbol}",
    response_model=WeeklyStockData,
)
def get_monthly_stock_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    user = user_crud.get_user_by_email(
        db,
        current_user_email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.alpha_vantage_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha Vantage API key not set",
        )

    normalized_symbol = symbol.upper()

    portfolio_entry = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id == user.id,
            PortfoliosTable.stock_symbol
            == normalized_symbol,
        )
        .first()
    )

    if not portfolio_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your portfolio",
        )

    stock = (
        db.query(StocksTable)
        .filter(
            StocksTable.stock_symbol
            == normalized_symbol
        )
        .first()
    )

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    try:
        response = httpx.get(
            "https://www.alphavantage.co/query",
            params={
                "function": (
                    "TIME_SERIES_MONTHLY_ADJUSTED"
                ),
                "symbol": stock.stock_symbol,
                "apikey": user.alpha_vantage_api_key,
            },
            timeout=15,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Stock API error",
            )

        data = response.json()

        if "Error Message" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid stock symbol",
            )

        if (
            "Note" in data
            or "Information" in data
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "API call frequency limit reached"
                ),
            )

        monthly_data = data.get(
            "Monthly Adjusted Time Series",
            {},
        )

        if not monthly_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No monthly data available "
                    "for this stock"
                ),
            )

        formatted_data = []

        for date, values in monthly_data.items():
            formatted_data.append(
                {
                    "date": date,
                    "open": float(
                        values["1. open"]
                    ),
                    "high": float(
                        values["2. high"]
                    ),
                    "low": float(
                        values["3. low"]
                    ),
                    "close": float(
                        values["4. close"]
                    ),
                    "adjusted_close": float(
                        values[
                            "5. adjusted close"
                        ]
                    ),
                    "volume": int(
                        values["6. volume"]
                    ),
                    "dividend_amount": float(
                        values[
                            "7. dividend amount"
                        ]
                    ),
                }
            )

        formatted_data.sort(
            key=lambda item: item["date"],
            reverse=True,
        )

        return {
            "symbol": stock.stock_symbol,
            "name": stock.stock_company_name,
            "metadata": data.get(
                "Meta Data",
                {},
            ),
            "weekly_data": formatted_data,
        }

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=(
                status.HTTP_504_GATEWAY_TIMEOUT
            ),
            detail=(
                "Request timeout - "
                "API service unavailable"
            ),
        )

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to communicate with "
                "stock data provider"
            ),
        )

    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Invalid response received from "
                "stock data provider"
            ),
        )

    except Exception as exc:
        print(
            "Failed to fetch monthly data "
            f"for {stock.stock_symbol}: {exc}"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal server error",
        )


@router.get(
    "/summary/{symbol}",
    response_model=StockSummary,
)
def get_stock_summary(
    symbol: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    user = user_crud.get_user_by_email(
        db,
        current_user_email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.alpha_vantage_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha Vantage API key not set",
        )

    normalized_symbol = symbol.upper()

    stock = (
        db.query(StocksTable)
        .filter(
            StocksTable.stock_symbol
            == normalized_symbol
        )
        .first()
    )

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    user_id = user.id
    stock_symbol = stock.stock_symbol

    try:
        response = httpx.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": stock_symbol,
                "apikey": user.alpha_vantage_api_key,
            },
            timeout=10,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Stock API error",
            )

        response_json = response.json()

        if "Error Message" in response_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid stock symbol",
            )

        if (
            "Note" in response_json
            or "Information" in response_json
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "API call frequency limit reached"
                ),
            )

        data = response_json.get(
            "Global Quote",
            {},
        )

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stock data available",
            )

        response_data = {
            "symbol": stock_symbol,
            "name": stock.stock_company_name,
            "open": float(data["02. open"]),
            "high": float(data["03. high"]),
            "low": float(data["04. low"]),
            "price": float(data["05. price"]),
            "volume": int(data["06. volume"]),
            "latest_trading_day": data[
                "07. latest trading day"
            ],
            "previous_close": float(
                data["08. previous close"]
            ),
            "change": float(
                data["09. change"]
            ),
            "change_percent": data[
                "10. change percent"
            ],
        }

        existing_cache = (
            db.query(StockDataCache)
            .filter(
                StockDataCache.user_id
                == user_id,
                StockDataCache.stock_symbol
                == stock_symbol,
            )
            .first()
        )

        if existing_cache:
            update_cache_from_summary(
                existing_cache,
                response_data,
            )

        else:
            new_cache = StockDataCache(
                user_id=user_id,
                stock_symbol=stock_symbol,
                open_price=response_data["open"],
                high_price=response_data["high"],
                low_price=response_data["low"],
                current_price=response_data["price"],
                volume=response_data["volume"],
                latest_trading_day=(
                    response_data[
                        "latest_trading_day"
                    ]
                ),
                previous_close=(
                    response_data[
                        "previous_close"
                    ]
                ),
                change=response_data["change"],
                change_percent=(
                    response_data[
                        "change_percent"
                    ]
                ),
            )

            db.add(new_cache)

        try:
            db.commit()

        except IntegrityError:
            db.rollback()

            winning_cache = (
                db.query(StockDataCache)
                .filter(
                    StockDataCache.user_id
                    == user_id,
                    StockDataCache.stock_symbol
                    == stock_symbol,
                )
                .first()
            )

            if not winning_cache:
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Failed to update "
                        "stock data cache"
                    ),
                )

            update_cache_from_summary(
                winning_cache,
                response_data,
            )

            db.commit()

        return response_data

    except HTTPException:
        db.rollback()
        raise

    except httpx.TimeoutException:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_504_GATEWAY_TIMEOUT
            ),
            detail=(
                "Request timeout - "
                "API service unavailable"
            ),
        )

    except httpx.HTTPError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to communicate with "
                "stock data provider"
            ),
        )

    except (KeyError, TypeError, ValueError):
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Invalid response received from "
                "stock data provider"
            ),
        )

    except Exception as exc:
        db.rollback()

        print(
            "Failed to fetch stock data "
            f"for {stock_symbol}: {exc}"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal server error",
        )


@router.get("/summary")
def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    user = user_crud.get_user_by_email(
        db,
        current_user_email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    portfolio = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id == user.id
        )
        .all()
    )

    if not portfolio:
        return []

    summaries = []

    for entry in portfolio:
        stock = (
            db.query(StocksTable)
            .filter(
                StocksTable.stock_symbol
                == entry.stock_symbol
            )
            .first()
        )

        if not stock:
            continue

        cached_data = (
            db.query(StockDataCache)
            .filter(
                StockDataCache.user_id == user.id,
                StockDataCache.stock_symbol
                == stock.stock_symbol,
            )
            .first()
        )

        if cached_data:
            summaries.append(
                {
                    "symbol": stock.stock_symbol,
                    "name": (
                        stock.stock_company_name
                    ),
                    "open": (
                        cached_data.open_price
                    ),
                    "high": (
                        cached_data.high_price
                    ),
                    "low": (
                        cached_data.low_price
                    ),
                    "price": (
                        cached_data.current_price
                    ),
                    "volume": cached_data.volume,
                    "latest_trading_day": (
                        cached_data
                        .latest_trading_day
                    ),
                    "previous_close": (
                        cached_data
                        .previous_close
                    ),
                    "change": cached_data.change,
                    "change_percent": (
                        cached_data
                        .change_percent
                    ),
                }
            )

        else:
            summaries.append(
                {
                    "symbol": stock.stock_symbol,
                    "name": (
                        stock.stock_company_name
                    ),
                }
            )

    return summaries


@router.post(
    "/add",
    status_code=status.HTTP_201_CREATED,
)
def add_stock_to_portfolio(
    ticker: StockSymbol,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    stock = (
        db.query(StocksTable)
        .filter(
            StocksTable.stock_symbol
            == ticker.stock_symbol.upper()
        )
        .first()
    )

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    user_id = user.id
    stock_symbol = stock.stock_symbol

    existing = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id == user_id,
            PortfoliosTable.stock_symbol
            == stock_symbol,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already in portfolio",
        )

    new_entry = PortfoliosTable(
        user_id=user_id,
        stock_symbol=stock_symbol,
    )

    try:
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

    except IntegrityError:
        db.rollback()

        existing_after_rollback = (
            db.query(PortfoliosTable)
            .filter(
                PortfoliosTable.user_id
                == user_id,
                PortfoliosTable.stock_symbol
                == stock_symbol,
            )
            .first()
        )

        if existing_after_rollback:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Stock already in portfolio"
                ),
            )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to add stock "
                "to portfolio"
            ),
        )

    return {
        "message": (
            f"Stock {stock_symbol} "
            "added to portfolio"
        )
    }


@router.delete(
    "/remove/{symbol}",
    status_code=status.HTTP_200_OK,
)
def remove_stock_from_portfolio(
    symbol: str,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    normalized_symbol = symbol.upper()

    portfolio_entry = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id == user.id,
            PortfoliosTable.stock_symbol
            == normalized_symbol,
        )
        .first()
    )

    if not portfolio_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in portfolio",
        )

    try:
        (
            db.query(StockDataCache)
            .filter(
                StockDataCache.user_id == user.id,
                StockDataCache.stock_symbol
                == normalized_symbol,
            )
            .delete(
                synchronize_session=False
            )
        )

        db.delete(portfolio_entry)
        db.commit()

    except Exception as exc:
        db.rollback()

        print(
            "Failed to remove stock "
            f"{normalized_symbol} "
            f"for user {user.email}: {exc}"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to remove stock "
                "from portfolio"
            ),
        )

    return {
        "message": (
            f"Stock {normalized_symbol} "
            "removed from portfolio"
        )
    }