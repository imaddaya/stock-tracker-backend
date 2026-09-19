import re
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    model_validator,
)


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError(
            "Password must be at least 8 characters long"
        )

    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter"
        )

    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter"
        )

    if not re.search(r"[0-9]", password):
        raise ValueError(
            "Password must contain at least one digit"
        )

    if not re.search(r"[!@#$%^&*]", password):
        raise ValueError(
            "Password must contain at least one special character "
            "(!@#$%^&*)"
        )

    return password


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    alpha_vantage_api_key: str

    @field_validator("password")
    @classmethod
    def check_password_strength(
        cls,
        password: str,
    ) -> str:
        return validate_password_strength(password)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError(
                "Passwords do not match"
            )

        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class StockSymbol(BaseModel):
    stock_symbol: str


class PasswordResetRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def check_password_strength(
        cls,
        password: str,
    ) -> str:
        return validate_password_strength(password)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError(
                "Passwords do not match"
            )

        return self


class EmailSchema(BaseModel):
    email: EmailStr


class StockSummary(BaseModel):
    symbol: str
    name: str
    open: float
    high: float
    low: float
    price: float
    volume: int
    latest_trading_day: str
    previous_close: float
    change: float
    change_percent: str


class WeeklyDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
    dividend_amount: float


class WeeklyStockData(BaseModel):
    symbol: str
    name: str
    metadata: dict
    weekly_data: list[WeeklyDataPoint]


class EmailReminderRequest(BaseModel):
    reminder_time: Optional[str] = None
    enabled: bool
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(
        cls,
        timezone_name: str,
    ) -> str:
        timezone_name = timezone_name.strip()

        if not timezone_name:
            raise ValueError(
                "Timezone cannot be empty"
            )

        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            raise ValueError(
                "Invalid timezone"
            )

        return timezone_name