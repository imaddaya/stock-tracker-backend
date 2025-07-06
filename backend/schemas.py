from pydantic import BaseModel, EmailStr, validator
import re

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    alpha_vantage_api_key: str

    @validator("password")
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StockTicker(BaseModel):
    ticker: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class EmailSchema(BaseModel):
    email: EmailStr

class StockSummary(BaseModel):
    symbol: str
    name: str
    price: float
    change_percent: str
    country: str