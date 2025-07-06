from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from cruds import stocks as stock_crud
from database import get_db

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/search")
def search_stocks(keywords: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    # Query local stocks table for ticker/name matches containing keywords
    results = stock_crud.search_stocks(db, keywords)
    return results
