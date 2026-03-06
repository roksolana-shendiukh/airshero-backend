from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import require_role
from app.repositories import baggage_repository

router = APIRouter(prefix="/baggage", tags=["Baggage"])


@router.get("/options")
def get_baggage_options(
    flight_class_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        options = baggage_repository.get_baggage_options(db, flight_class_id)
        return options
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))