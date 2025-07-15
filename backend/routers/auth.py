from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import UserSignup, UserLogin, PasswordResetRequest, EmailSchema
from cruds import users as user_crud
from database import get_db
from utils.jwt import create_access_token, create_verification_token, create_password_reset_token, decode_token
from utils.email import send_verification_email, send_password_reset_email
from jose import JWTError
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    
    print(f"information about the user     : {user}\n")
    print("we start by checking passwords:")
    print(f"user.password is         : {user.password}")
    print(f"user.confirm_password is : {user.confirm_password}")
    print(f"check if user.password(1) is the same as user.confirm_password(2) : {user.password ==user.confirm_password}\n")
    print("if True we move on to check if the user already exists:\n")
    
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    print(f"we will go through the database looking for the email : {user.email}")
    print("if we find it we will raise an error saying that the user already exists")
    print("if we don't find it we will create the user\n")
    
    if user_crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = user_crud.create_user(db, user)

    print(f"user created successfully at: {db_user}")
    
    token = create_verification_token(db_user.email)

    print(f"token is : {token}")
    
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
def reset_password(data: dict, db: Session = Depends(get_db)):
    try:
        # Extract data from the request
        token = data.get("token")
        new_password = data.get("new_password")
        
        if not token or not new_password:
            raise HTTPException(status_code=400, detail="Token and new password are required")
        
        # Validate password complexity
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        if not any(c.isupper() for c in new_password):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
        if not any(c.islower() for c in new_password):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in new_password):
            raise HTTPException(status_code=400, detail="Password must contain at least one digit")
        if not any(c in "!@#$%^&*" for c in new_password):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character (!@#$%^&*)")
        
        payload = decode_token(token)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = user_crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.hashed_password = hashed_pw
        db.commit()
        return {"message": "Password reset successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/confirm-account-deletion")
def confirm_account_deletion(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        email = payload.get("email")
        token_type = payload.get("type")
        
        if not email or token_type != "account_deletion":
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = user_crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user and all related data
        db.delete(user)
        db.commit()
        
        return {"message": "Account deleted successfully"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
