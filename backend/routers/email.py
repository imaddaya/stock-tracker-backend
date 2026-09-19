import re

from fastapi import APIRouter, Depends, HTTPException
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
from schemas import EmailReminderRequest
from utils.email import send_daily_summary_email


router = APIRouter(
    prefix="/email",
    tags=["email"],
)


def format_currency(value: float | None) -> str:
    if value is None:
        return "N/A"

    return f"${value:.2f}"


def format_volume(value: int | None) -> str:
    if value is None:
        return "N/A"

    return f"{value:,}"


@router.post("/reminder-settings")
def set_email_reminder(
    request: EmailReminderRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    """Set or update email reminder settings for the current user."""

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
            status_code=404,
            detail="User not found",
        )

    if (
        request.reminder_time
        and request.enabled
    ):
        if not re.match(
            r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
            request.reminder_time,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid time format. "
                    "Use HH:MM format "
                    "(e.g., 09:30)"
                ),
            )

    user.email_reminder_enabled = (
        request.enabled
    )

    user.timezone = (
        request.timezone or "UTC"
    )

    if (
        request.enabled
        and request.reminder_time
    ):
        user.email_reminder_time = (
            request.reminder_time
        )

    elif not request.enabled:
        user.email_reminder_time = None

    try:
        db.commit()

        return {
            "message": (
                "Email reminder settings "
                "updated successfully"
            ),
            "enabled": (
                user.email_reminder_enabled
            ),
            "reminder_time": (
                user.email_reminder_time
            ),
            "timezone": user.timezone,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update settings: "
                f"{exc}"
            ),
        )


@router.post("/send-summary")
def send_email_summary(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    """Send daily portfolio summary email to the current user."""

    user = user_crud.get_user_by_email(
        db,
        current_user_email,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    portfolio = (
        db.query(PortfoliosTable)
        .filter(
            PortfoliosTable.user_id
            == user.id
        )
        .all()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail=(
                "Portfolio is empty - "
                "add some stocks first"
            ),
        )

    portfolio_summary = []

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
                StockDataCache.user_id
                == user.id,
                StockDataCache.stock_symbol
                == stock.stock_symbol,
            )
            .first()
        )

        if cached_data:
            portfolio_summary.append(
                {
                    "ticker": (
                        stock.stock_symbol
                    ),
                    "name": (
                        stock.stock_company_name
                    ),
                    "price": format_currency(
                        cached_data.current_price
                    ),
                    "change_percent": (
                        cached_data.change_percent
                        or "N/A"
                    ),
                    "change": format_currency(
                        cached_data.change
                    ),
                    "open": format_currency(
                        cached_data.open_price
                    ),
                    "high": format_currency(
                        cached_data.high_price
                    ),
                    "low": format_currency(
                        cached_data.low_price
                    ),
                    "volume": format_volume(
                        cached_data.volume
                    ),
                    "latest_trading_day": (
                        cached_data
                        .latest_trading_day
                        or "N/A"
                    ),
                    "previous_close": (
                        format_currency(
                            cached_data
                            .previous_close
                        )
                    ),
                }
            )

        else:
            portfolio_summary.append(
                {
                    "ticker": (
                        stock.stock_symbol
                    ),
                    "name": (
                        stock.stock_company_name
                    ),
                    "price": "N/A",
                    "change_percent": "N/A",
                    "change": "N/A",
                    "open": "N/A",
                    "high": "N/A",
                    "low": "N/A",
                    "volume": "N/A",
                    "latest_trading_day": (
                        "N/A"
                    ),
                    "previous_close": "N/A",
                }
            )

    if not portfolio_summary:
        raise HTTPException(
            status_code=404,
            detail=(
                "No stock data available "
                "in portfolio"
            ),
        )

    try:
        send_daily_summary_email(
            current_user_email,
            portfolio_summary,
        )

        return {
            "message": (
                "Email sent successfully"
            ),
            "stocks_included": len(
                portfolio_summary
            ),
            "recipient": (
                current_user_email
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to send email: "
                f"{exc}"
            ),
        )


@router.post("/test-send")
def test_send_email(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    """Test endpoint to manually send an email summary."""

    try:
        result = send_email_summary(
            db,
            current_user_email,
        )

        return {
            "message": (
                "Test email sent successfully"
            ),
            "details": result,
        }

    except HTTPException as exc:
        raise exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to send test email: "
                f"{exc}"
            ),
        )


@router.get("/settings")
def get_email_settings(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(
        get_current_user_email
    ),
):
    """Get current email reminder settings for the user."""

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
            status_code=404,
            detail="User not found",
        )

    return {
        "email_reminder_enabled": (
            user.email_reminder_enabled
            or False
        ),
        "email_reminder_time": (
            user.email_reminder_time
        ),
        "timezone": (
            user.timezone or "UTC"
        ),
    }