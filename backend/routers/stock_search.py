from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from cruds import stocks as stock_crud
from database import get_db

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("")
def get_stocks(
    keywords: str = Query(None, min_length=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    if keywords:
        return stock_crud.search_stocks(db, keywords)[offset:offset+limit]
    else:
        return stock_crud.list_all_stocks(db)[offset:offset+limit]