from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.services import city_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.infrastructure.database.repositories import flight_repository
from app.core.services import flight_service
from app.interfaces.schemas.flight_schema import FlightFilterRequestDTO


router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/search")
def search_flights(
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
            "airlineLogoUrl":  f"https://storage.googleapis.com/airshero-b81e4.firebasestorage.app/airlines/{r['airline_logo_url']}/{r['airline_logo_url']}.png" if r["airline_logo_url"] else "",
        }
        for r in rows
    ]


@router.get("/available-dates")
def get_available_dates(
    from_city: int = Query(...),
    to_city: int = Query(...),
    db: Session = Depends(get_db),
):
    return city_service.get_available_dates(db, from_city, to_city)


@router.post("/filter")
def filter_flights(
    body: FlightFilterRequestDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return flight_service.filter_flights(
        db,
        flight_ids=body.flightIds,
        class_names=body.classNames,
        min_price=body.minPrice,
        max_price=body.maxPrice,
        airline_names=body.airlineNames,
        sort_by=body.sortBy,
        departure_slots=body.departureSlots,
    )


@router.get("/without-operation")
def get_flights_without_operation(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned to this user")
    rows = flight_repository.get_flights_without_operation(db, airline_id)
    return [
        {
            "flightId":         r["flight_id"],
            "flightNumber":     r["flight_number"],
            "departsAirportId": r["departs_airport_id"],
            "departsCode":      r["departs_code"],
            "arrivesCode":      r["arrives_code"],
            "departsDatetime":  r["departs_datetime"].isoformat(),
            "arrivesDatetime":  r["arrives_datetime"].isoformat(),
            "flightStatus":     r["flight_status_name"],
            "airlineName": r["airline_name"],
        }
        for r in rows
    ]


@router.get("/{flight_id}/availability")
def get_flight_availability(
    flight_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    from sqlalchemy import text
    sql = text("""
        SELECT class_name, total_seats, booked_seats, available_seats
        FROM FN_GetFlightAvailability(:flight_id)
    """)
    rows = db.execute(sql, {"flight_id": flight_id}).fetchall()
    return [
        {
            "className":      r.class_name,
            "totalSeats":     r.total_seats,
            "bookedSeats":    r.booked_seats,
            "availableSeats": max(r.available_seats, 0),
        }
        for r in rows
    ]


@router.post("/availability")
def get_flights_availability(
    flight_ids: list[int],
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    from sqlalchemy import text
    result = {}
    for flight_id in flight_ids:
        sql = text("""
            SELECT class_name, total_seats, booked_seats, available_seats
            FROM FN_GetFlightAvailability(:flight_id)
        """)
        rows = db.execute(sql, {"flight_id": flight_id}).fetchall()
        result[flight_id] = [
            {
                "className":      r.class_name,
                "totalSeats":     r.total_seats,
                "bookedSeats":    r.booked_seats,
                "availableSeats": max(r.available_seats, 0),
            }
            for r in rows
        ]
    return result



