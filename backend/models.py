from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UsersTable(Base):
    __tablename__ = "users_table"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    alpha_vantage_api_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    email_reminder_time: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    email_reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="UTC",
    )

    last_api_key_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_saved_stocks: Mapped[list["PortfoliosTable"]] = relationship(
        "PortfoliosTable",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    stock_data_cache: Mapped[list["StockDataCache"]] = relationship(
        "StockDataCache",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    email_reminder_deliveries: Mapped[
        list["EmailReminderDelivery"]
    ] = relationship(
        "EmailReminderDelivery",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class StocksTable(Base):
    __tablename__ = "stocks_table"

    stock_symbol: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        index=True,
        nullable=False,
    )

    stock_company_name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )

    is_listed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    stock_appearance_in_portfolios: Mapped[
        list["PortfoliosTable"]
    ] = relationship(
        "PortfoliosTable",
        back_populates="stock",
        cascade="all, delete-orphan",
    )


class PortfoliosTable(Base):
    __tablename__ = "portfolios_table"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users_table.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    stock_symbol: Mapped[str] = mapped_column(
        ForeignKey(
            "stocks_table.stock_symbol",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["UsersTable"] = relationship(
        "UsersTable",
        back_populates="user_saved_stocks",
    )

    stock: Mapped["StocksTable"] = relationship(
        "StocksTable",
        back_populates="stock_appearance_in_portfolios",
    )


class StockDataCache(Base):
    __tablename__ = "stock_data_cache"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users_table.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    stock_symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    open_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    high_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    low_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    current_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    volume: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    latest_trading_day: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    previous_close: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    change: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    change_percent: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["UsersTable"] = relationship(
        "UsersTable",
        back_populates="stock_data_cache",
    )


class EmailReminderDelivery(Base):
    __tablename__ = "email_reminder_deliveries"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "local_date",
            name="uq_email_reminder_delivery_user_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users_table.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    local_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["UsersTable"] = relationship(
        "UsersTable",
        back_populates="email_reminder_deliveries",
    )