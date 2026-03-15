from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import gate_service

router = APIRouter(prefix="/gates", tags=["Gates"])


@router.get("")
def get_gates(
    airport_id:   int | None = Query(default=None),
    min_capacity: int | None = Query(default=None),
    flight_id:    int | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    if flight_id is not None:
        return gate_service.get_gates_for_flight(db, flight_id)
    return gate_service.get_all_gates(
        db, airport_id=airport_id, min_capacity=min_capacity
    )