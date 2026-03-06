from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.repositories import checkin_repository
from app.models.checkin_dto import IssueBoardingPassDTO, BoardingPassDTO

router = APIRouter(prefix="/checkin", tags=["Check-In"])


@router.get("/booking")
def find_booking(
    booking_number: str | None = Query(default=None),
    document_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    if not booking_number and not document_number:
        raise HTTPException(
            status_code=422,
            detail="Provide booking_number or document_number",
        )

    if booking_number:
        result = checkin_repository.get_booking_by_number(db, booking_number)
    else:
        result = checkin_repository.get_booking_by_document(db, document_number)

    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Перевірка статусу
    if result.booking_status.lower() != "confirmed":
        raise HTTPException(
            status_code=400,
            detail=f"Booking status is '{result.booking_status}', expected 'Confirmed'",
        )
    if result.payment_status and result.payment_status.lower() != "paid":
        raise HTTPException(
            status_code=400,
            detail=f"Payment status is '{result.payment_status}', expected 'Paid'",
        )

    return result

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
    """Розраховує доплату за багаж якщо перевищено норму."""
    from app.models.checkin_dto import BaggageUnitInputDTO
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
        bp = checkin_repository.issue_boarding_pass(
            db=db,
            data=data,
            checkin_agent_id=agent.checkin_agent_id,
            flight_operation_id=flight_operation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return bp