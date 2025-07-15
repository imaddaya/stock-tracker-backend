from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_current_user_email
from database import get_db
from models import UsersTable
from schemas import EmailSchema
from utils.email import send_email
from utils.jwt import create_verification_token
from pydantic import BaseModel
from datetime import datetime
from utils.jwt import create_verification_token
from utils.email import send_account_deletion_email
from datetime import timedelta


router = APIRouter(prefix="/user", tags=["user"])

class UpdateApiKeyRequest(BaseModel):
    new_api_key: str

@router.get("/profile")
def get_profile(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user.email,
        "alpha_vantage_api_key": user.alpha_vantage_api_key,
        "email_reminder_time": user.email_reminder_time,
        "email_reminder_enabled": user.email_reminder_enabled
    }

@router.put("/update-api-key")
def update_api_key(request: UpdateApiKeyRequest, db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for rate limiting (once per week)
    if user.last_api_key_update:
        from datetime import timedelta
        if (datetime.utcnow() - user.last_api_key_update) < timedelta(days=7):
            raise HTTPException(status_code=429, detail="API key can only be updated once per week")
    
    user.alpha_vantage_api_key = request.new_api_key
    user.last_api_key_update = datetime.utcnow()
    db.commit()
    
    return {"message": "API key updated successfully"}

@router.delete("/delete-account")
def initiate_account_deletion(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    user = db.query(UsersTable).filter(UsersTable.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from utils.jwt import create_account_deletion_token
    token = create_account_deletion_token(user.email)
    
    # Send deletion confirmation email
    send_account_deletion_email(user.email, token)
    
    return {"message": "Account deletion verification email sent. You have 30 minutes to confirm."}

@router.delete("/confirm-delete-account")
def confirm_account_deletion(token: str, db: Session = Depends(get_db)):
    from utils.jwt import decode_token
    from jose import JWTError
    
    try:
        payload = decode_token(token)
        email = payload.get("email")
        token_type = payload.get("type")
        
        if not email or token_type != "account_deletion":
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(UsersTable).filter(UsersTable.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user and all related data (portfolios, cache, etc.)
        db.delete(user)
        db.commit()
        
        return {"message": "Account deleted successfully"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")


