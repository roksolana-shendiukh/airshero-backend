from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import gate_service

router = APIRouter(prefix="/gates", tags=["Gates"])


@router.get("")
def get_gates(
    airport_id:   int | None = Query(default=None),
    min_capacity: int | None = Query(default=None),
    flight_id:    int | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return gate_service.get_gates(
        db,
        flight_id=   flight_id,
        airport_id=  airport_id,
        min_capacity=min_capacity,
    )

