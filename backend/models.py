from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from database import Base

class UsersTable(Base): # Use capital letter for class name
    __tablename__ = "users_table" # Use snake_case for table name
# everything is clear here
    id: Mapped[int] = mapped_column(primary_key=True, index=True) 
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    alpha_vantage_api_key: Mapped[str] = mapped_column(String(128), nullable=False)
    email_reminder_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Format: "HH:MM"
    email_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=True, default="UTC")  # e.g., 
    last_api_key_update: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
#RELATIONSHIP BETWEEN TABLES
    user_saved_stocks: Mapped[list["PortfoliosTable"]] = relationship("PortfoliosTable", back_populates="user", cascade="all, delete-orphan")

class StocksTable(Base):
    __tablename__ = "stocks_table"

    stock_symbol: Mapped[str] = mapped_column(String(20), primary_key=True, index=True, nullable=False)
    stock_company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_listed: Mapped[bool] = mapped_column(Boolean, default=True)
#RELATIONSHIP BETWEEN TABLES
    stock_appearance_in_portfolios: Mapped[list["PortfoliosTable"]] = relationship(
        "PortfoliosTable", back_populates="stock", cascade="all, delete-orphan")

class PortfoliosTable(Base):
    __tablename__ = "portfolios_table"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users_table.id"), nullable=False)
    stock_symbol: Mapped[str] = mapped_column(ForeignKey("stocks_table.stock_symbol"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#RELATIONSHIP BETWEEN TABLES
    user: Mapped["UsersTable"] = relationship("UsersTable", back_populates="user_saved_stocks")
    stock: Mapped["StocksTable"] = relationship("StocksTable", back_populates="stock_appearance_in_portfolios")

class StockDataCache(Base):
    __tablename__ = "stock_data_cache"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users_table.id"), nullable=False)
    stock_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=True)
    high_price: Mapped[float] = mapped_column(Float, nullable=True)
    low_price: Mapped[float] = mapped_column(Float, nullable=True)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[int] = mapped_column(Integer, nullable=True)
    latest_trading_day: Mapped[str] = mapped_column(String(20), nullable=True)
    previous_close: Mapped[float] = mapped_column(Float, nullable=True)
    change: Mapped[float] = mapped_column(Float, nullable=True)
    change_percent: Mapped[str] = mapped_column(String(20), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#RELATIONSHIP BETWEEN TABLES
    user: Mapped["UsersTable"] = relationship("UsersTable")