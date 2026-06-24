from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.services import airport_service

router = APIRouter(prefix="/airports", tags=["Airports"])


@router.get("")
def get_airports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
):
    return airport_service.get_all_airports(db, skip=skip, limit=limit)