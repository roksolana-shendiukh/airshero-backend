from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.checkin_schema import IssueBoardingPassDTO, CalculateBaggageRequestDTO, CalculateBaggageResponseDTO
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
    

@router.get("/active-flights")
def get_active_flights(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")
    
    airport_id = checkin_repository.get_airport_id_by_agent(db, agent_id)
    if not airport_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    flights = checkin_repository.get_active_flights_for_agent(db, airport_id)
    return flights


@router.get("/flight-passengers/suggestions")
def get_flight_passenger_suggestions(
    q: str = Query(...),
    flight_number: str = Query(...),
    departs_date: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_suggestions_for_flight(
        db, q, flight_number, departs_date
    )


@router.get("/baggage-info/{booking_item_id}")
def get_baggage_info(
    booking_item_id: int,
    db:   Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    info = checkin_repository.get_baggage_info(db, booking_item_id)
    if not info:
        raise HTTPException(status_code=404, detail="Baggage info not found")
    return info


@router.get("/baggage-types")
def get_baggage_types(
    db:   Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_repository.get_baggage_types(db)


@router.post("/baggage-check")
def check_baggage_surcharge(
    booking_item_id: int = Query(...),
    baggage_units:   list = [],
    db:   Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    from app.services.checkin_baggage_service import calculate_surcharge

    info = checkin_repository.get_baggage_info(db, booking_item_id)
    if not info:
        raise HTTPException(status_code=404, detail="Baggage info not found")

    result = calculate_surcharge(info, baggage_units)
    return {
        "bookingItemId": booking_item_id,
        "surcharge":     result["surcharge"],
        "reasons":       result["reasons"],
        "hasSurcharge":  result["surcharge"] > 0,
    }


@router.get("/checked-baggage-weight/{flight_operation_id}")
def get_checked_baggage_weight(
    flight_operation_id: int,
    db:   Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    weight = checkin_repository.get_checked_baggage_weight(
        db, flight_operation_id
    )
    return {"totalCheckedWeightKg": weight}


@router.post("/baggage/{booking_item_id}/calculate", response_model=CalculateBaggageResponseDTO)
def calculate_baggage(
    booking_item_id: int,
    body: CalculateBaggageRequestDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")) 
):
    return checkin_service.calculate_baggage_surcharge(db, booking_item_id, body.bagWeights)


