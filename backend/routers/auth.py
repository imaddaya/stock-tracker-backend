from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import UserSignup, UserLogin, PasswordResetRequest, EmailSchema
from cruds import users as user_crud
from database import get_db
from utils.jwt import create_verification_token
from utils.email import send_verification_email, send_password_reset_email
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    # Validate passwords match (can also be done in schema)
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check if user exists
    if user_crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    db_user = user_crud.create_user(db, user)

    # Send verification email
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

    # TODO: Create and return JWT token (implement utility for this)
    return {"message": "Login successful (token creation to be implemented)"}

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    # TODO: Decode token and mark user verified if token valid
    return {"message": "Email verification (to be implemented)"}

@router.post("/forgot-password")
def forgot_password(email_data: EmailSchema, db: Session = Depends(get_db)):
    # TODO: Send password reset email if user exists and is verified
    return {"message": "Forgot password flow (to be implemented)"}

@router.post("/reset-password")
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    # TODO: Verify token and update user password
    return {"message": "Reset password flow (to be implemented)"}
