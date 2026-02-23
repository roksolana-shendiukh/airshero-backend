from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies.auth import require_role
from app.database import get_db
from app.models.flight import FlightDTO
from app.repositories import flight_repository
from app.repositories import city_repository

router = APIRouter(prefix="/flights", tags=["Flights"])

@router.get("/search")
def search_flights_endpoint(
    from_city: int, 
    to_city: int, 
    depart_date: str, 
    db: Session = Depends(get_db)
):
    rows = flight_repository.search_flights(db, from_city, to_city, depart_date)
    return [
        {
            "flight_id": r.flight_id,
            "flight_number": r.flight_number,
            "departs_datetime": r.departs_datetime.isoformat(),
            "arrives_datetime": r.arrives_datetime.isoformat(),
            "airline_name": r.airline_name,
            "airline_logo_url": r.airline_logo_url,
            "departs_code": r.departs_code,
            "arrives_code": r.arrives_code,
            "class_name": r.class_name,
            "ticket_price": float(r.ticket_price)
        } for r in rows
    ]

@router.get("/available-dates")
def get_available_dates_for_route(
    from_city: int = Query(..., description="ID міста відправлення"),
    to_city: int = Query(..., description="ID міста прибуття"),
    db: Session = Depends(get_db)
):
    dates = city_repository.get_available_dates(db, from_city, to_city)
    return dates
