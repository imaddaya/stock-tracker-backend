from sqlalchemy.orm import Session
from models import Portfolio

def get_user_portfolio(db: Session, user_email: str):
    return db.query(Portfolio).filter(Portfolio.user_email == user_email).all()

def add_stock_to_portfolio(db: Session, user_email: str, ticker: str):
    # Check if stock already in portfolio
    existing = db.query(Portfolio).filter(Portfolio.user_email == user_email, Portfolio.ticker == ticker).first()
    if existing:
        return existing
    new_entry = Portfolio(user_email=user_email, ticker=ticker.upper())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

def remove_stock_from_portfolio(db: Session, user_email: str, ticker: str):
    entry = db.query(Portfolio).filter(Portfolio.user_email == user_email, Portfolio.ticker == ticker.upper()).first()
    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False
