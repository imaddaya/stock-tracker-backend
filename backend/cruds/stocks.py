from sqlalchemy.orm import Session
from models import StocksTable

def get_stock_by_ticker(db: Session, ticker: str):
    return db.query(StocksTable).filter(StocksTable.stock_symbol == ticker.upper()).first()

def list_all_stocks(db: Session):
    return db.query(StocksTable).all()

def add_stock(db: Session, ticker: str, name: str, listed: bool = True):
    existing = get_stock_by_ticker(db, ticker)
    if existing:
        # Update if needed
        existing.stock_company_name = name
        existing.is_listed = listed
        db.commit()
        return existing

    new_stock = StocksTable(stock_symbol=ticker.upper(), stock_company_name=name,is_listed=listed)
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return new_stock

def remove_stock(db: Session, ticker: str):
    stock = get_stock_by_ticker(db, ticker)
    if stock:
        db.delete(stock)
        db.commit()
        return True
    return False

def search_stocks(db: Session, keywords: str):
    query = f"%{keywords.lower()}%"
    return db.query(StocksTable).filter(
        (StocksTable.stock_symbol.ilike(query)) | 
        (StocksTable.stock_company_name.ilike(query))
    ).all()
