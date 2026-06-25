from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.services import city_service, flight_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.flight_schema import FlightFilterRequestDTO

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/search")
def search_flights(
    from_city:   int,
    to_city:     int,
    depart_date: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return flight_service.search_flights(db, from_city, to_city, depart_date)


@router.get("/available-dates")
def get_available_dates(
    from_city: int = Query(...),
    to_city:   int = Query(...),
    db: Session = Depends(get_db),
):
    return city_service.get_available_dates(db, from_city, to_city)


@router.get("/without-operation")
def get_flights_without_operation(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airline_id") 
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned to this user")
    return flight_service.get_flights_without_operation(db, airline_id)


@router.post("/filter")
def filter_flights(
    body: FlightFilterRequestDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return flight_service.filter_flights(
        db,
        flight_ids=     body.flight_ids,
        class_names=    body.class_names,
        min_price=      body.min_price,
        max_price=      body.max_price,
        airline_names=  body.airline_names,
        sort_by=        body.sort_by,
        departure_slots=body.departure_slots,
    )


@router.post("/availability")
def get_flights_availability(
    flight_ids: list[int],
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return flight_service.get_flights_availability(db, flight_ids)


@router.get("/{flight_id}/availability")
def get_flight_availability(
    flight_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return flight_service.get_flight_availability(db, flight_id)