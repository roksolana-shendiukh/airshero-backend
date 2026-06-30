from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import route_service

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("")
def get_routes(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airline_id")  
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned to this user")
    return route_service.get_all_routes(db, airline_id=airline_id)


@router.get("/alternatives")
def get_alternatives(
    from_city: int,
    to_city:   int,
    db: Session = Depends(get_db),
):
    return route_service.get_flight_alternatives(db, from_city, to_city)