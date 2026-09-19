import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from config import get_settings


settings = get_settings()


def password_fingerprint(hashed_password: str) -> str:
    return hashlib.sha256(
        hashed_password.encode("utf-8")
    ).hexdigest()


def create_token(
    data: dict,
    expires_delta: timedelta,
) -> str:
    payload = data.copy()

    payload["exp"] = (
        datetime.now(timezone.utc)
        + expires_delta
    )

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(
    token: str,
    expected_type: str | None = None,
) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if expected_type is not None:
        token_type = payload.get("type")

        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

    return payload


def create_verification_token(
    email: str,
) -> str:
    return create_token(
        data={
            "email": email,
            "type": "email_verification",
        },
        expires_delta=timedelta(hours=24),
    )


def create_password_reset_token(
    email: str,
    hashed_password: str,
) -> str:
    return create_token(
        data={
            "email": email,
            "type": "password_reset",
            "password_fingerprint": (
                password_fingerprint(
                    hashed_password
                )
            ),
        },
        expires_delta=timedelta(hours=1),
    )


def create_access_token(
    email: str,
) -> str:
    return create_token(
        data={
            "sub": email,
            "type": "access",
        },
        expires_delta=timedelta(minutes=60),
    )


def create_account_deletion_token(
    email: str,
) -> str:
    return create_token(
        data={
            "email": email,
            "type": "account_deletion",
        },
        expires_delta=timedelta(minutes=30),
    )