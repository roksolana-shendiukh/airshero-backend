from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import route_service

router = APIRouter(tags=["Routes"])


@router.get("/routes")
def get_routes(db: Session = Depends(get_db)):
    return route_service.get_all_routes(db)