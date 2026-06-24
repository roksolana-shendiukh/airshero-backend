from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.services import airline_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_any_role

router = APIRouter(prefix="/airlines", tags=["Airlines"])


@router.get("/")
def list_all_airlines(db: Session = Depends(get_db)):
    return airline_service.get_all_airlines(db)


@router.get("/{airline_id}")
def get_airline_info(airline_id: int, db: Session = Depends(get_db)):
    return airline_service.get_airline_by_id(db, airline_id)

