from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import baggage_service

router = APIRouter(prefix="/baggage", tags=["Baggage"])


@router.get("/options")
def get_baggage_options(
    flight_class_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return baggage_service.get_baggage_options(db, flight_class_id)