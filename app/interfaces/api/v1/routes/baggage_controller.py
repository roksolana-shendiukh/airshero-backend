from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.infrastructure.database.repositories import baggage_repository

router = APIRouter(prefix="/baggage", tags=["Baggage"])


@router.get("/options")
def get_baggage_options(
    flight_class_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        return baggage_repository.get_baggage_options(db, flight_class_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))