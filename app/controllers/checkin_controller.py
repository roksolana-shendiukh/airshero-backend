from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.checkin_schema import IssueBoardingPassDTO, CalculateBaggageRequestDTO, CalculateBaggageResponseDTO, IssueCheckinDTO
from app.schemas.boarding_pass_schema import BoardingPassDTO
from app.services import checkin_service, reference_service

router = APIRouter(prefix="/checkin", tags=["Check-In"])


@router.get("/booking")
def find_booking(
    document_number: str = Query(...),
    flight_number:   str = Query(...),
    departs_date:    str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    rows = checkin_service.get_passenger_booking(db, document_number, flight_number, departs_date)
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    return rows


@router.get("/payment-methods")
def get_payment_methods(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return reference_service.get_payment_methods(db)


@router.get("/seat-map/{flight_operation_id}")
def get_seat_map(
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    result = checkin_service.get_seat_map(db, flight_operation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return result


@router.get("/active-flights")
def get_active_flights(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")
    return checkin_service.get_active_flights(db, agent_id)


@router.get("/flight-passengers/suggestions")
def get_flight_passenger_suggestions(
    q: str = Query(...),
    flight_number: str = Query(...),
    departs_date: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_suggestions_for_flight(db, q, flight_number, departs_date)


@router.get("/baggage-info/{booking_item_id}")
def get_baggage_info(
    booking_item_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    info = checkin_service.get_baggage_info(db, booking_item_id)
    if not info:
        raise HTTPException(status_code=404, detail="Baggage info not found")
    return info


@router.get("/baggage-types")
def get_baggage_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_baggage_types(db)


@router.get("/checked-baggage-weight/{flight_operation_id}")
def get_checked_baggage_weight(
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_checked_baggage_weight(db, flight_operation_id)


@router.post("/baggage/{booking_item_id}/calculate", response_model=CalculateBaggageResponseDTO)
def calculate_baggage(
    booking_item_id: int,
    body: CalculateBaggageRequestDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.calculate_baggage_surcharge(db, booking_item_id, body.bagWeights)


@router.post("/issue-with-baggage")
def issue_with_baggage(
    data: IssueCheckinDTO,
    flight_operation_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")

    try:
        return checkin_service.issue_with_baggage(
            db=db,
            data=data,
            flight_operation_id=flight_operation_id,
            checkin_agent_id=agent_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check-already-checked-in/{booking_item_id}")
def check_already_checked_in(
    booking_item_id: int,
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.check_already_checked_in(db, booking_item_id, flight_operation_id)


@router.get("/stats/{flight_operation_id}")
def get_boarding_stats(
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_boarding_stats(db, flight_operation_id)


@router.get("/recent/{flight_operation_id}")
def get_recently_checked_in(
    flight_operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_recently_checked_in(db, flight_operation_id)

@router.get("/boarding-pass/{boarding_pass_id}")
def get_boarding_pass(
    boarding_pass_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    result = checkin_service.get_boarding_pass_details(db, boarding_pass_id)
    if not result:
        raise HTTPException(status_code=404, detail="Boarding pass not found")
    return result


