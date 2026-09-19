from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import UsersTable
from utils.jwt import decode_token, password_fingerprint


security = HTTPBearer()


def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> str:
    payload = decode_token(
        credentials.credentials,
        expected_type="access",
    )

    email = payload.get("sub")

    if not isinstance(email, str) or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    token_password_fingerprint = payload.get(
        "password_fingerprint"
    )

    if not isinstance(
        token_password_fingerprint,
        str,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is no longer valid",
        )

    user = (
        db.query(UsersTable)
        .filter(UsersTable.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is no longer valid",
        )

    current_password_fingerprint = password_fingerprint(
        user.hashed_password
    )

    if (
        token_password_fingerprint
        != current_password_fingerprint
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is no longer valid",
        )

    return user.email