from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import planning_service
from app.interfaces.schemas.planning_schema import (
    CreateFlightDTO,
    AddFlightBaggageDTO,
    CreateRouteDTO,
    CreateScheduleDTO,
    ConfigureFlightDTO,
    UpdateFlightClassesDTO,
    ConfirmFlightsDTO,
    UpdateFlightTimesDTO,
)

router = APIRouter(prefix="/planning", tags=["Planning"])
logger = logging.getLogger(__name__)

_AIRLINE_REQUIRED = "No airline assigned"


def _get_airline_id(user: dict) -> int:
    airline_id = user.get("airline_id")
    if not airline_id:
        raise HTTPException(status_code=403, detail=_AIRLINE_REQUIRED)
    return airline_id


@router.get("/overview/flights")
def get_overview_flights(
    mode:          str      = Query(default="day", pattern="^(all|day|month)$"),
    date:          str | None = Query(default=None),
    month:         int | None = Query(default=None),
    year:          int | None = Query(default=None),
    status:        str | None = Query(default=None),
    flight_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    airline_id = _get_airline_id(user)
    return planning_service.get_overview_flights(
        db, airline_id, mode=mode, date=date, month=month, year=year,
        status=status, flight_number=flight_number,
    )


@router.get("/overview/stats")
def get_overview_stats(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_overview_stats(db, _get_airline_id(user))


@router.get("/overview/available-dates")
def get_available_dates(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_available_dates(db, _get_airline_id(user))


@router.get("/overview/available-months")
def get_available_months(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_available_months(db, _get_airline_id(user))


@router.get("/airfleets")
def get_airfleets(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_airfleets_for_airline(db, _get_airline_id(user))


@router.get("/airports")
def get_airports(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_airports_for_airline(db, _get_airline_id(user))


@router.get("/baggage-rules")
def get_baggage_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_baggage_rules(db)


@router.get("/routes/generate-flight-number")
def generate_flight_number(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    try:
        return planning_service.generate_flight_number(db, _get_airline_id(user))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/routes/flight-numbers")
def get_all_flight_numbers(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_all_flight_numbers(db, _get_airline_id(user))


@router.get("/routes/duration")
def get_route_duration(
    airfleet_id:        int = Query(...),
    departs_airport_id: int = Query(...),
    arrives_airport_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    _get_airline_id(user)
    return planning_service.get_route_duration(
        db,
        airfleet_id=        airfleet_id,
        departs_airport_id= departs_airport_id,
        arrives_airport_id= arrives_airport_id,
    )


@router.get("/routes")
def get_routes(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_routes_for_airline(db, _get_airline_id(user))


@router.post("/routes")
def create_route(
    body: CreateRouteDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    try:
        return planning_service.create_route_with_schedule(
            db,
            airline_id=        _get_airline_id(user),
            airfleet_id=       body.airfleet_id,
            departs_airport_id=body.departs_airport_id,
            arrives_airport_id=body.arrives_airport_id,
            flight_number=     body.flight_number,
            flight_start_date= body.flight_start_date,
            flight_end_date=   body.flight_end_date,
            schedule_groups=[
                {
                    "day_ids":        g.day_ids,
                    "departure_time": g.departure_time,
                }
                for g in body.schedule_groups
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/routes/{route_id}/schedules")
def get_route_schedules(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_route_schedules(db, route_id)


@router.post("/routes/{route_id}/schedules")
def add_schedule(
    route_id: int,
    body: CreateScheduleDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    try:
        return planning_service.add_schedule_to_route(
            db,
            route_id=         route_id,
            flight_start_date=body.flight_start_date,
            flight_end_date=  body.flight_end_date,
            schedule_groups=[
                {
                    "day_ids":        g.day_ids,
                    "departure_time": g.departure_time,
                }
                for g in body.schedule_groups
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/setup/routes")
def get_routes_with_planned_flights(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_routes_with_planned_flights(db, _get_airline_id(user))


@router.get("/setup/routes/{route_id}/all-flights")
def get_all_flights_for_route(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_all_flights_for_route(db, route_id)


@router.get("/setup/routes/{route_id}/flights")
def get_planned_flights_for_route(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_planned_flights_for_route(db, route_id)


@router.post("/setup/flights/confirm")
def confirm_flights(
    body: ConfirmFlightsDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.confirm_flights(db, body.flight_ids)


@router.post("/setup/flights/{flight_id}/classes")
def update_flight_classes(
    flight_id: int,
    body: UpdateFlightClassesDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.update_flight_classes(db, flight_id, body.class_ids)


@router.get("/schedules/{flight_schedule_id}/booked-dates")
def get_booked_dates(
    flight_schedule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_booked_dates_for_schedule(db, flight_schedule_id)


@router.get("/pricing/routes")
def get_routes_with_pricing_flights(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_routes_with_pricing_flights(db, _get_airline_id(user))


@router.get("/pricing/routes/{route_id}/flights")
def get_pricing_flights_for_route(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_pricing_flights_for_route(db, route_id)


@router.get("/pricing/flights")
def get_flights_for_pricing(
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_scheduled_flights_for_pricing(db, _get_airline_id(user))


@router.get("/pricing/flights/{flight_id}/history")
def get_flight_price_history(
    flight_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_price_history_for_flight(db, flight_id)


@router.post("/pricing/flights/{flight_id}/prices")
def update_flight_prices(
    flight_id: int,
    body: ConfigureFlightDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.update_flight_prices(
        db,
        flight_id=   flight_id,
        class_prices=[{"class_id": cp.class_id, "price": cp.price}
                      for cp in body.class_prices],
    )


@router.get("/airfleet/{airfleet_id}/seat-layout")
def get_seat_layout(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.get_seat_layout(db, airfleet_id)


@router.post("/flights")
def create_flight(
    body: CreateFlightDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.create_flight(
        db,
        schedule_flight_id=body.schedule_flight_id,
        departs_datetime=  body.departs_datetime,
        arrives_datetime=  body.arrives_datetime,
        class_prices=      body.class_prices,
    )


@router.post("/flights/{flight_id}/baggage")
def update_flight_baggage(
    flight_id: int,
    body: AddFlightBaggageDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.update_flight_baggage(
        db, flight_id,
        options=[
            {
                "class_id":               opt.class_id,
                "baggage_pricing_rule_id": opt.baggage_pricing_rule_id,
                "price":                  opt.price,
            }
            for opt in body.baggage_options
        ],
    )


@router.post("/flights/{flight_id}/configure")
def configure_flight(
    flight_id: int,
    body: ConfigureFlightDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    return planning_service.configure_planned_flight(
        db,
        flight_id=   flight_id,
        class_prices=[{"class_id": cp.class_id, "price": cp.price}
                      for cp in body.class_prices],
    )


@router.post("/flights/{flight_id}/cancel")
def cancel_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    try:
        planning_service.cancel_flight(db, flight_id)
        return {"status": "success", "message": "Flight cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/flights/{flight_id}/times")
def update_flight_times(
    flight_id: int,
    body: UpdateFlightTimesDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("planningManager")),
):
    try:
        planning_service.update_flight_times(
            db,
            flight_id=  flight_id,
            departs_iso=body.departs_datetime,
            arrives_iso=body.arrives_datetime,
        )
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))