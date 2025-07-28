from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException
import os
from config import get_settings

settings = get_settings()

# JWT settings
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.environ["JWT_ALGORITHM"]

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Email verification token
def create_verification_token(email: str):
    return create_token(
        data={"email": email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )

# Password reset token
def create_password_reset_token(email: str):
    return create_token(
        data={"email": email, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )

# Access token (used in login)
def create_access_token(email: str):
    return create_token(
        data={"sub": email, "type": "access"},
        expires_delta=timedelta(minutes=60)  # or make this configurable
    )

# Account deletion token
def create_account_deletion_token(email: str):
    return create_token(
        data={"email": email, "type": "account_deletion"},
        expires_delta=timedelta(minutes=30)
    )
