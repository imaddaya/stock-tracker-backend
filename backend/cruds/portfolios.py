from sqlalchemy.orm import Session 
from models import PortfoliosTable, UsersTable, StocksTable

def get_user_portfolio(db: Session, user_email: str):
    user = db.query(UsersTable).filter(UsersTable.email == user_email).first()
    print(user)
    if not user:
        return []
        
    return (
        db.query(PortfoliosTable)
        .filter(PortfoliosTable.user_id == user.id)
        .all()
    )
def add_stock_to_portfolio(db: Session, user_email: str, ticker: str):
    user = db.query(UsersTable).filter(UsersTable.email == user_email).first()
    if not user:
        return None 

    stock = db.query(StocksTable).filter(StocksTable.stock_symbol == ticker.upper()).first()
    if not stock:
        return None  # or raise error

    existing = db.query(PortfoliosTable).filter(
        PortfoliosTable.user_id == user.id,
        PortfoliosTable.stock_symbol == stock.stock_symbol
    ).first()
    if existing:
        return existing

    new_entry = PortfoliosTable(user_id=user.id, stock_symbol=stock.stock_symbol)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

def remove_stock_from_portfolio(db: Session, user_email: str, ticker: str):
    user = db.query(UsersTable).filter(UsersTable.email == user_email).first()
    if not user:
        return False

    stock = db.query(StocksTable).filter(StocksTable.symbol == ticker.upper()).first()
    if not stock:
        return False

    entry = db.query(PortfoliosTable).filter(
        PortfoliosTable.user_id == user.id,
        PortfoliosTable.stock_symbol == stock.stock_symbol
    ).first()

    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False
