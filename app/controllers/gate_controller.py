from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import gate_service

router = APIRouter(prefix="/gates", tags=["Gates"])


@router.get("")
def get_gates(
    airport_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return gate_service.get_all_gates(db, airport_id=airport_id)