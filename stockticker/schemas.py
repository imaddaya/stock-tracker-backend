from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class StockTicker(BaseModel):
    ticker: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class EmailSchema(BaseModel):
    email: EmailStr