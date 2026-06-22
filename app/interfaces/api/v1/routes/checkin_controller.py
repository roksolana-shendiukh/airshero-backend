from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.services import checkin_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.checkin_schema import IssueBoardingPassDTO, CalculateBaggageRequestDTO, CalculateBaggageResponseDTO, IssueCheckinDTO
from app.interfaces.schemas.boarding_pass_schema import BoardingPassDTO
from app.core.services import reference_service
from fastapi import Body

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


@router.get("/boarding-passes")
def get_boarding_passes(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
    search: str | None = Query(None),
    route_city: str | None = Query(None),
    class_name: str | None = Query(None),
    date_filter: str | None = Query('today'),
    skip: int = 0,
    limit: int = 50,
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")
    return checkin_service.get_boarding_passes_history(
        db, agent_id=agent_id,
        search=search,
        route_city=route_city,
        class_name=class_name,
        date_filter=date_filter,
        skip=skip, limit=limit,
    )


@router.get("/boarding-pass/{boarding_pass_id}/baggage")
def get_boarding_pass_baggage(
    boarding_pass_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    return checkin_service.get_baggage_units(db, boarding_pass_id)


@router.get("/boarding-passes/classes")
def get_boarding_pass_classes(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")
    return checkin_service.get_boarding_pass_classes(db, agent_id)

@router.get("/boarding-passes/cities")
def get_boarding_pass_cities(
    db: Session = Depends(get_db),
    user=Depends(require_role("checkInAgent")),
):
    agent_id = user.get("agentId")
    if not agent_id:
        raise HTTPException(status_code=403, detail="Agent not assigned")
    return checkin_service.get_boarding_pass_cities(db, agent_id)


@router.put("/boarding-pass/{boarding_pass_id}/reprint")
def reprint_boarding_pass(
    boarding_pass_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("checkInAgent")),
):
    checkin_service.reprint_boarding_pass(db, boarding_pass_id)
    return {"ok": True}

@router.put("/boarding-pass/{boarding_pass_id}/seat")
def update_seat(
    boarding_pass_id: int,
    seat_layout_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    user = Depends(require_role("checkInAgent")),
):
    checkin_service.update_boarding_pass_seat(db, boarding_pass_id, seat_layout_id)
    return {"ok": True}


