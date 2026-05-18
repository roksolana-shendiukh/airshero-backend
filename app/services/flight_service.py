from sqlalchemy.orm import Session
from app.repositories import flight_repository


def _map_row(r) -> dict:
    return {
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


def search_flights(db: Session, from_city: int, to_city: int, depart_date: str) -> list[dict]:
    rows = flight_repository.search_flights(db, from_city, to_city, depart_date)
    return [_map_row(r) for r in rows]


def filter_flights(
    db: Session,
    flight_ids: list[int],
    class_names: list[str] | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    airline_names: list[str] | None = None,
    sort_by: str = "price_asc",
    departure_slots: list[str] | None = None,
) -> list[dict]:
    rows = flight_repository.filter_flights_by_ids(
        db,
        flight_ids=flight_ids,
        class_names=class_names,
        min_price=min_price,
        max_price=max_price,
        airline_names=airline_names,
        sort_by=sort_by,
        departure_slots=departure_slots,
    )
    return [_map_row(r) for r in rows]

