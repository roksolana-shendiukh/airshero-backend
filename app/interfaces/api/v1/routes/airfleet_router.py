from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.services import airfleet_service, storage_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role, require_any_role


router = APIRouter(prefix="/airfleets", tags=["Airfleets"])


@router.get("")
def get_airfleets(
    flight_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airline_id")  
    return airfleet_service.get_all_airfleets(db, airline_id=airline_id, flight_id=flight_id)


@router.get("/{airfleet_id}/photos")
def get_airfleet_photos(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("flightOperator", "planningManager", "systemAdmin")),
):
    return storage_service.get_airfleet_photos(db, airfleet_id)