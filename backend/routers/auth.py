import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cruds import users as user_crud
from database import get_db
from schemas import EmailSchema, PasswordResetRequest, UserLogin, UserSignup
from utils.email import send_password_reset_email, send_verification_email
from utils.jwt import (
    create_access_token,
    create_password_reset_token,
    create_verification_token,
    decode_token,
    password_fingerprint,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(
    user: UserSignup,
    db: Session = Depends(get_db),
):
    if user_crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    try:
        db_user = user_crud.create_user(db, user)

        token = create_verification_token(
            db_user.email
        )

        send_verification_email(
            db_user.email,
            token,
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        print(
            "Failed to create user because the verification "
            f"email could not be sent: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Unable to send verification email. "
                "Please try again later."
            ),
        )

    return {
        "message": (
            "User created successfully. "
            "Please check your email to verify your account."
        )
    }


@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    db_user = user_crud.get_user_by_email(
        db,
        user.email,
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_matches = bcrypt.checkpw(
        user.password.encode("utf-8"),
        db_user.hashed_password.encode("utf-8"),
    )

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    access_token = create_access_token(
        db_user.email,
        db_user.hashed_password,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    payload = decode_token(
        token,
        expected_type="email_verification",
    )

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    user = user_crud.get_user_by_email(
        db,
        email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        return {
            "message": "Email already verified"
        }

    user.is_verified = True
    db.commit()

    return {
        "message": "Email verified successfully"
    }


@router.post("/forgot-password")
def forgot_password(
    email_data: EmailSchema,
    db: Session = Depends(get_db),
):
    generic_response = {
        "message": (
            "If your email is registered and verified, "
            "you'll receive password reset instructions."
        )
    }

    user = user_crud.get_user_by_email(
        db,
        email_data.email,
    )

    if not user or not user.is_verified:
        return generic_response

    try:
        token = create_password_reset_token(
            user.email,
            user.hashed_password,
        )

        send_password_reset_email(
            user.email,
            token,
        )

    except Exception as exc:
        # Do not reveal email-delivery failures to the caller,
        # because doing so could reveal whether an account exists.
        print(
            "Password reset email could not be sent "
            f"for {user.email}: {exc}"
        )

    return generic_response


@router.post("/reset-password")
def reset_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    payload = decode_token(
        data.token,
        expected_type="password_reset",
    )

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    user = user_crud.get_user_by_email(
        db,
        email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    token_password_fingerprint = payload.get(
        "password_fingerprint"
    )

    current_password_fingerprint = password_fingerprint(
        user.hashed_password
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Password reset token is no longer valid"
            ),
        )

    hashed_password = bcrypt.hashpw(
        data.new_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    user.hashed_password = hashed_password

    db.commit()

    return {
        "message": "Password reset successfully"
    }