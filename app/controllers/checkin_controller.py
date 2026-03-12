from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.checkin_schema import IssueBoardingPassDTO
from app.schemas.boarding_pass_schema import BoardingPassDTO
from app.repositories import checkin_repository
from app.services import checkin_service

router = APIRouter(prefix="/checkin", tags=["Check-In"])


@router.get("/booking")
def find_booking(
    document_number: str = Query(...),
    flight_number:   str = Query(...),
    departs_date:    str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    rows = checkin_service.get_passenger_booking(
        db, document_number, flight_number, departs_date
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    return rows


@router.get("/seat-map/{flight_operation_id}")
def get_seat_map(
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    result = checkin_repository.get_seat_map(db, flight_operation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return result


@router.get("/flight-operation")
def get_flight_operation(
    flight_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    op = checkin_repository.get_flight_operation_by_flight_id(db, flight_id)
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return {"flight_operation_id": op.flight_operation_id}


@router.post("/baggage-check")
def check_baggage(
    booking_item_id: int = Query(...),
    flight_id: int = Query(...),
    baggage_units: list = [],
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_repository.check_baggage_surcharge(
        db, booking_item_id, flight_id, baggage_units
    )


@router.post("/issue", response_model=BoardingPassDTO)
def issue_boarding_pass(
    data: IssueBoardingPassDTO,
    flight_operation_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent = checkin_repository.get_checkin_agent_by_user_email(db, user.get("email", ""))
    if not agent:
        raise HTTPException(status_code=403, detail="Check-in agent not found")

    try:
        return checkin_repository.issue_boarding_pass(
            db=db,
            data=data,
            checkin_agent_id=agent.checkin_agent_id,
            flight_operation_id=flight_operation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))