from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import planning_service
from app.schemas.planning_schema import CreateFlightDTO, AddFlightBaggageDTO

router = APIRouter(prefix="/planning", tags=["Planning"])


@router.get("/overview/flights")
def get_overview_flights(
    mode: str = Query(default="day", pattern="^(all|day|month)$"),
    date: str | None = Query(default=None),
    month: int | None = Query(default=None),
    year: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned")
    return planning_service.get_overview_flights(
        db, airline_id, mode=mode, date=date, month=month, year=year, status=status
    )


@router.get("/overview/stats")
def get_overview_stats(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned to this user")
    return planning_service.get_overview_stats(db, airline_id)

@router.get("/overview/available-dates")
def get_available_dates(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned")
    return planning_service.get_available_dates(db, airline_id)

@router.get("/overview/available-months")
def get_available_months(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned")
    return planning_service.get_available_months(db, airline_id)


@router.get("/routes")
def get_routes(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned")
    return planning_service.get_routes_for_airline(db, airline_id)

@router.post("/flights")
def create_flight(
    body: CreateFlightDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.create_flight(
        db,
        flight_schedule_id=body.flightScheduleId,
        departs_datetime=body.departsDatetime,
        arrives_datetime=body.arrivesDatetime,
        class_prices=body.classPrices,
    )


@router.get("/baggage-rules")
def get_baggage_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager"))
):
    return planning_service.get_baggage_rules(db)


@router.post("/flights/{flight_id}/baggage")
def add_baggage_to_flight(
    flight_id: int,
    body: AddFlightBaggageDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager"))
):
    options =[
        {
            "class_id": opt.classId,
            "baggage_pricing_rule_id": opt.baggagePricingRuleId,
            "price": opt.price
        }
        for opt in body.baggageOptions
    ]
    
    return planning_service.add_baggage_to_flight(db, flight_id, options)


@router.get("/seat-layout/{airfleet_id}")
def get_seat_layout_endpoint(airfleet_id: int, db: Session = Depends(get_db)):
    return planning_service.get_seat_layout(db, airfleet_id)

@router.get("/routes/{route_id}/schedules")
def get_route_schedules(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_route_schedules(db, route_id)


@router.get("/airfleet/{airfleet_id}/seat-layout")
def get_seat_layout(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_seat_layout(db, airfleet_id)


@router.get("/schedules/{flight_schedule_id}/booked-dates")
def get_booked_dates(
    flight_schedule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_booked_dates_for_schedule(db, flight_schedule_id)








