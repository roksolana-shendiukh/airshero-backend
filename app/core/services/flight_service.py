from sqlalchemy.orm import Session

from app.infrastructure.database.repositories import flight_repository

AIRLINE_LOGO_BASE = "https://storage.googleapis.com/airshero-b81e4.firebasestorage.app/airlines"


def _map_row(r) -> dict:
    logo = r["airline_logo_url"]
    return {
        "flight_id":        r["flight_id"],
        "flight_class_id":  r["flight_class_id"],
        "flight_price_id":  r["flight_price_id"],
        "flight_number":    r["flight_number"],
        "departs_datetime": r["departs_datetime"].isoformat(),
        "arrives_datetime": r["arrives_datetime"].isoformat(),
        "flight_duration":  r["flight_duration"],
        "departs_code":     r["departure_airport_code"],
        "departs_airport":  r["departure_airport_name"],
        "arrives_code":     r["arrival_airport_code"],
        "arrives_airport":  r["arrival_airport_name"],
        "class_name":       r["class_name"],
        "ticket_price":     float(r["ticket_price"]),
        "flight_status":    r["flight_status_name"],
        "airline_name":     r["airline_name"],
        "airline_logo_url": f"{AIRLINE_LOGO_BASE}/{logo}/{logo}.png" if logo else "",
    }


def search_flights(db: Session, from_city: int, to_city: int, depart_date: str) -> list[dict]:
    rows = flight_repository.search_flights(db, from_city, to_city, depart_date)
    return [_map_row(r) for r in rows]


def filter_flights(
    db: Session,
    flight_ids:      list[int],
    class_names:     list[str] | None = None,
    min_price:       float | None = None,
    max_price:       float | None = None,
    airline_names:   list[str] | None = None,
    sort_by:         str = "price_asc",
    departure_slots: list[str] | None = None,
) -> list[dict]:
    rows = flight_repository.filter_flights_by_ids(
        db,
        flight_ids=     flight_ids,
        class_names=    class_names,
        min_price=      min_price,
        max_price=      max_price,
        airline_names=  airline_names,
        sort_by=        sort_by,
        departure_slots=departure_slots,
    )
    return [_map_row(r) for r in rows]


def get_flights_without_operation(db: Session, airline_id: int) -> list[dict]:
    rows = flight_repository.get_flights_without_operation(db, airline_id)
    return [
        {
            "flight_id":          r["flight_id"],
            "flight_number":      r["flight_number"],
            "departs_airport_id": r["departs_airport_id"],
            "departs_code":       r["departs_code"],
            "arrives_code":       r["arrives_code"],
            "departs_datetime":   r["departs_datetime"].isoformat(),
            "arrives_datetime":   r["arrives_datetime"].isoformat(),
            "flight_status":      r["flight_status_name"],
            "airline_name":       r["airline_name"],
        }
        for r in rows
    ]


def get_flight_availability(db: Session, flight_id: int) -> list[dict]:
    rows = flight_repository.get_flight_availability(db, flight_id)
    return [
        {
            "class_name":      r.class_name,
            "total_seats":     r.total_seats,
            "booked_seats":    r.booked_seats,
            "available_seats": max(r.available_seats, 0),
        }
        for r in rows
    ]


def get_flights_availability(db: Session, flight_ids: list[int]) -> dict:
    return {
        flight_id: get_flight_availability(db, flight_id)
        for flight_id in flight_ids
    }

