import time
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from database import SessionLocal
from models import (
    PortfoliosTable,
    StockDataCache,
    StocksTable,
    UsersTable,
)
from utils.email import send_daily_summary_email


def format_currency(value: float | None) -> str:
    if value is None:
        return "N/A"

    return f"${value:.2f}"


def format_volume(value: int | None) -> str:
    if value is None:
        return "N/A"

    return f"{value:,}"


def send_scheduled_emails() -> None:
    """Send portfolio summary emails at each user's configured local time."""
    db: Session = SessionLocal()

    try:
        users = (
            db.query(UsersTable)
            .filter(
                UsersTable.email_reminder_enabled.is_(True),
                UsersTable.email_reminder_time.isnot(None),
            )
            .all()
        )

        print(
            "Checking scheduled emails - "
            f"{len(users)} user(s) have reminders enabled"
        )

        for user in users:
            try:
                user_timezone = ZoneInfo(
                    user.timezone or "UTC"
                )

                current_time = datetime.now(
                    user_timezone
                ).strftime("%H:%M")

                if current_time != user.email_reminder_time:
                    continue

                portfolio = (
                    db.query(PortfoliosTable)
                    .filter(
                        PortfoliosTable.user_id == user.id
                    )
                    .all()
                )

                if not portfolio:
                    print(
                        f"Skipping {user.email}: "
                        "portfolio is empty"
                    )
                    continue

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
                            StockDataCache.user_id == user.id,
                            StockDataCache.stock_symbol
                            == stock.stock_symbol,
                        )
                        .first()
                    )

                    if cached_data:
                        portfolio_summary.append(
                            {
                                "ticker": stock.stock_symbol,
                                "name": stock.stock_company_name,
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
                                    cached_data.latest_trading_day
                                    or "N/A"
                                ),
                                "previous_close": format_currency(
                                    cached_data.previous_close
                                ),
                            }
                        )

                    else:
                        portfolio_summary.append(
                            {
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
                                "previous_close": "N/A",
                            }
                        )

                if not portfolio_summary:
                    print(
                        f"Skipping {user.email}: "
                        "no portfolio data available"
                    )
                    continue

                send_daily_summary_email(
                    user.email,
                    portfolio_summary,
                )

                print(
                    f"Sent scheduled email to {user.email} "
                    f"at {current_time} "
                    f"({user.timezone or 'UTC'})"
                )

            except ZoneInfoNotFoundError:
                print(
                    f"Invalid timezone '{user.timezone}' "
                    f"for user {user.email}"
                )

            except Exception as exc:
                print(
                    f"Failed to send scheduled email "
                    f"to {user.email}: {exc}"
                )

    except Exception as exc:
        print(f"Scheduler database error: {exc}")

    finally:
        db.close()


def run_scheduler() -> None:
    """Run the email scheduler as a standalone process."""
    print(
        "Email scheduler started - "
        "checking reminders every minute"
    )

    while True:
        try:
            send_scheduled_emails()
        except Exception as exc:
            print(f"Scheduler error: {exc}")

        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()