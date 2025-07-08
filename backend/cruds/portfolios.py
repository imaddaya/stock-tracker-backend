from sqlalchemy.orm import Session , joinedload
from models import Portfolio, User, Stock

def get_user_portfolio(db: Session, user_email: str):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return []

    # eager load the related stock to avoid attribute errors
    return (
        db.query(Portfolio)
        .options(joinedload(Portfolio.stock))
        .filter(Portfolio.user_id == user.id)
        .all()
    )
def add_stock_to_portfolio(db: Session, user_email: str, ticker: str):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return None 

    stock = db.query(Stock).filter(Stock.symbol == ticker.upper()).first()
    if not stock:
        return None  # or raise error

    existing = db.query(Portfolio).filter(
        Portfolio.user_id == user.id,
        Portfolio.stock_id == stock.id
    ).first()
    if existing:
        return existing

    new_entry = Portfolio(user_id=user.id, stock_id=stock.id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

def remove_stock_from_portfolio(db: Session, user_email: str, ticker: str):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return False

    stock = db.query(Stock).filter(Stock.symbol == ticker.upper()).first()
    if not stock:
        return False

    entry = db.query(Portfolio).filter(
        Portfolio.user_id == user.id,
        Portfolio.stock_id == stock.id
    ).first()

    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False
