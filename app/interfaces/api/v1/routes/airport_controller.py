from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.services import airport_service

router = APIRouter(tags=["Airports"])


@router.get("/airports")
def get_airports(db: Session = Depends(get_db)):
    return airport_service.get_all_airports(db)