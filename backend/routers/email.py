from fastapi import APIRouter, Depends
from dependencies import get_current_user_email
from cruds import portfolios as portfolio_crud
from database import get_db
from utils.email import send_daily_summary_email
from sqlalchemy.orm import Session    

router = APIRouter(prefix="/email", tags=["email"])

@router.get("/send-summary")
def send_email_summary(db: Session = Depends(get_db), current_user_email: str = Depends(get_current_user_email)):
    # Get portfolio stocks
    portfolio = portfolio_crud.get_user_portfolio(db, current_user_email)
    if not portfolio:
        return {"message": "Portfolio is empty"}

    # Call utility to send email
    send_daily_summary_email(current_user_email, portfolio)
    return {"message": "Email sent successfully"}
