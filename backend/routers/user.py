from datetime import datetime, timedelta, timezone

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
)


router = APIRouter(prefix="/user", tags=["user"])


class UpdateApiKeyRequest(BaseModel):
    new_api_key: str = Field(
        min_length=1,
        max_length=128,
    )


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = (
        db.query(UsersTable)
        .filter(UsersTable.email == current_user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
        "alpha_vantage_api_key_masked": masked_api_key,
        "email_reminder_time": user.email_reminder_time,
        "email_reminder_enabled": user.email_reminder_enabled,
        "timezone": user.timezone,
    }


@router.put("/update-api-key")
def update_api_key(
    request: UpdateApiKeyRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = (
        db.query(UsersTable)
        .filter(UsersTable.email == current_user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_api_key = request.new_api_key.strip()

    if not new_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key cannot be empty",
        )

    now = datetime.now(timezone.utc)

    if user.last_api_key_update:
        last_update = ensure_utc(
            user.last_api_key_update
        )

        elapsed = now - last_update

        if elapsed < timedelta(days=7):
            retry_after = (
                timedelta(days=7)
                - elapsed
            )

            retry_after_seconds = max(
                1,
                int(retry_after.total_seconds()),
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
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

    user.alpha_vantage_api_key = new_api_key
    user.last_api_key_update = now

    db.commit()

    return {
        "message": "API key updated successfully"
    }


@router.delete("/delete-account")
def initiate_account_deletion(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = (
        db.query(UsersTable)
        .filter(UsersTable.email == current_user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    token = create_account_deletion_token(
        user.email
    )

    send_account_deletion_email(
        user.email,
        token,
    )

    return {
        "message": (
            "Account deletion verification email sent. "
            "You have 30 minutes to confirm."
        )
    }


@router.delete("/confirm-delete-account")
def confirm_account_deletion(
    token: str,
    db: Session = Depends(get_db),
):
    payload = decode_token(
        token,
        expected_type="account_deletion",
    )

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    user = (
        db.query(UsersTable)
        .filter(UsersTable.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return {
        "message": "Account deleted successfully"
    }