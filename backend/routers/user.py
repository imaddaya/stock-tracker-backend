from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user_email
from models import UsersTable
from utils.email import send_account_deletion_email
from utils.jwt import (
    create_account_deletion_token,
    decode_token,
    password_fingerprint,
)


router = APIRouter(
    prefix="/user",
    tags=["user"],
)


ALPHA_VANTAGE_URL = (
    "https://www.alphavantage.co/query"
)


class UpdateApiKeyRequest(BaseModel):
    new_api_key: str = Field(
        min_length=1,
        max_length=128,
    )


def ensure_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def validate_alpha_vantage_api_key(
    api_key: str,
) -> None:
    try:
        response = httpx.get(
            ALPHA_VANTAGE_URL,
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": "IBM",
                "apikey": api_key,
            },
            timeout=10,
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unable to validate API key "
                "right now. Please try again later."
            ),
        )

    except httpx.HTTPError:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unable to validate API key "
                "right now. Please try again later."
            ),
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unable to validate API key "
                "right now. Please try again later."
            ),
        )

    try:
        data = response.json()

    except ValueError:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unable to validate API key "
                "right now. Please try again later."
            ),
        )

    global_quote = data.get(
        "Global Quote"
    )

    if (
        isinstance(global_quote, dict)
        and global_quote.get("01. symbol")
    ):
        return

    provider_message = " ".join(
        str(data.get(key, ""))
        for key in (
            "Error Message",
            "Information",
            "Note",
        )
    ).lower()

    if (
        "api key" in provider_message
        or "apikey" in provider_message
        or "invalid" in provider_message
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid Alpha Vantage API key"
            ),
        )

    raise HTTPException(
        status_code=(
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        detail=(
            "Unable to validate API key "
            "right now. Please try again later."
        ),
    )


@router.get("/profile")
def get_profile(
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
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found",
        )

    masked_api_key = None

    if user.alpha_vantage_api_key:
        masked_api_key = (
            "********"
            + user.alpha_vantage_api_key[-4:]
        )

    return {
        "email": user.email,
        "alpha_vantage_api_key_masked": (
            masked_api_key
        ),
        "email_reminder_time": (
            user.email_reminder_time
        ),
        "email_reminder_enabled": (
            user.email_reminder_enabled
        ),
        "timezone": user.timezone,
    }


@router.put("/update-api-key")
def update_api_key(
    request: UpdateApiKeyRequest,
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
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found",
        )

    new_api_key = (
        request.new_api_key.strip()
    )

    if not new_api_key:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="API key cannot be empty",
        )

    now = datetime.now(
        timezone.utc
    )

    if user.last_api_key_update:
        last_update = ensure_utc(
            user.last_api_key_update
        )

        elapsed = (
            now - last_update
        )

        if elapsed < timedelta(days=7):
            retry_after = (
                timedelta(days=7)
                - elapsed
            )

            retry_after_seconds = max(
                1,
                int(
                    retry_after.total_seconds()
                ),
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "API key can only be updated "
                    "once per week"
                ),
                headers={
                    "Retry-After": str(
                        retry_after_seconds
                    ),
                },
            )

    validate_alpha_vantage_api_key(
        new_api_key
    )

    user.alpha_vantage_api_key = (
        new_api_key
    )

    user.last_api_key_update = now

    try:
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to update API key"
            ),
        )

    return {
        "message": (
            "API key updated successfully"
        )
    }


@router.delete("/delete-account")
def initiate_account_deletion(
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
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found",
        )

    token = (
        create_account_deletion_token(
            user.email,
            user.hashed_password,
        )
    )

    send_account_deletion_email(
        user.email,
        token,
    )

    return {
        "message": (
            "Account deletion verification "
            "email sent. You have 30 minutes "
            "to confirm."
        )
    }


@router.post(
    "/confirm-delete-account"
)
def confirm_account_deletion(
    token: str,
    db: Session = Depends(get_db),
):
    payload = decode_token(
        token,
        expected_type="account_deletion",
    )

    email = payload.get("email")

    if (
        not isinstance(email, str)
        or not email
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid token",
        )

    user = (
        db.query(UsersTable)
        .filter(
            UsersTable.email == email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found",
        )

    token_password_fingerprint = (
        payload.get(
            "password_fingerprint"
        )
    )

    current_password_fingerprint = (
        password_fingerprint(
            user.hashed_password
        )
    )

    if (
        not isinstance(
            token_password_fingerprint,
            str,
        )
        or token_password_fingerprint
        != current_password_fingerprint
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Account deletion token "
                "is no longer valid"
            ),
        )

    db.delete(user)
    db.commit()

    return {
        "message": (
            "Account deleted successfully"
        )
    }