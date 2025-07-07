from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import UserSignup, UserLogin, PasswordResetRequest, EmailSchema
from cruds import users as user_crud
from database import get_db
from utils.jwt import (
    create_access_token,
    create_verification_token,
    create_password_reset_token,
    decode_token
)
from utils.email import send_verification_email, send_password_reset_email
from jose import JWTError
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if user_crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = user_crud.create_user(db, user)
    token = create_verification_token(db_user.email)
    send_verification_email(db_user.email, token)

    return {"message": "User created successfully. Please check your email to verify your account."}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(db_user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = user_crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_verified:
            return {"message": "Email already verified"}

        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")


@router.post("/forgot-password")
def forgot_password(email_data: EmailSchema, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_email(db, email_data.email)
    if user and user.is_verified:
        token = create_password_reset_token(user.email)
        send_password_reset_email(user.email, token)

    # Always return generic response to avoid leaking user info
    return {
        "message": "If your email is registered and verified, you'll receive password reset instructions."
    }


@router.post("/reset-password")
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.token)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = user_crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_pw = bcrypt.hashpw(data.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.hashed_password = hashed_pw
        db.commit()
        return {"message": "Password reset successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
