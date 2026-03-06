from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies.auth import require_role
from app.database import get_db
from app.repositories import flight_repository
from app.repositories import city_repository

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/search")
def search_flights_endpoint(
    from_city: int,
    to_city: int,
    depart_date: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = flight_repository.search_flights(db, from_city, to_city, depart_date)
    return [
        {
            "flightId":        r["flight_id"],
            "flightClassId":   r["flight_class_id"],
            "flightPriceId":   r["flight_price_id"],
            "flightNumber":    r["flight_number"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "departsCode":     r["departure_airport_code"],
            "departsAirport":  r["departure_airport_name"],
            "arrivesCode":     r["arrival_airport_code"],
            "arrivesAirport":  r["arrival_airport_name"],
            "className":       r["class_name"],
            "ticketPrice":     float(r["ticket_price"]),
            "flightStatus":    r["flight_status_name"],
            "airlineName":     r["airline_name"],
            "airlineLogoUrl":  r["airline_logo_url"] or "",
        }
        for r in rows
    ]


@router.get("/available-dates")
def get_available_dates_for_route(
    from_city: int = Query(...),
    to_city: int = Query(...),
    db: Session = Depends(get_db),
):
    dates = city_repository.get_available_dates(db, from_city, to_city)
    return dates