from sqlalchemy.orm import Session
from models import Stock

def get_stock_by_ticker(db: Session, ticker: str):
    return db.query(Stock).filter(Stock.symbol == ticker.upper()).first()

def list_all_stocks(db: Session):
    return db.query(Stock).all()

def add_stock(db: Session, ticker: str, name: str, region: str, listed: bool = True):
    existing = get_stock_by_ticker(db, ticker)
    if existing:
        # Update if needed
        existing.name = name
        existing.region = region
        existing.is_listed = listed
        db.commit()
        return existing

    new_stock = Stock(symbol=ticker.upper(), name=name, region=region, is_listed=listed)
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
    return db.query(Stock).filter(
        (Stock.symbol.ilike(query)) | 
        (Stock.name.ilike(query))
    ).all()
