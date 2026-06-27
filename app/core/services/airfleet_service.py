from sqlalchemy.orm import Session, joinedload

from app.infrastructure.database.repositories import airfleet_repository
from app.interfaces.schemas.airfleet_schema import AirfleetDTO
from app.infrastructure.database.models.flight_model import Flight
from app.infrastructure.database.models.flight_schedule_model import FlightSchedule


def _get_route_range(db: Session, flight_id: int) -> float | None:
    flight = (
        db.query(Flight)
        .options(
            joinedload(Flight.flight_schedule)
            .joinedload(FlightSchedule.route)
        )
        .filter(Flight.flight_id == flight_id)
        .first()
    )
    if not flight:
        return None
    schedule = getattr(flight, "flight_schedule", None)
    route    = getattr(schedule, "route", None)
    range_km = getattr(route, "flight_range", None)
    return float(range_km) if range_km else None


def get_all_airfleets(
    db: Session,
    airline_id: int | None = None,
    flight_id:  int | None = None,
) -> list[AirfleetDTO]:
    min_range_km = _get_route_range(db, flight_id) if flight_id else None

    return [
        AirfleetDTO(
            airfleet_id=               a.airfleet_id,
            aircraft_model=            a.aircraft_model,
            manufacturer_name=         getattr(a.manufacturer, 'airfleet_manufacturer_name', None),
            seat_capacity=             a.seat_capacity,
            aircraft_range_km=         float(a.aircraft_range_km) if a.aircraft_range_km else None,
            aircraft_speed=            float(a.aircraft_speed) if a.aircraft_speed else None,
            baggage_capacity=          float(a.baggage_capacity) if a.baggage_capacity else None,
            aircraft_fuel_consumption= float(a.aircraft_fuel_consumption) if a.aircraft_fuel_consumption else None,
            aircraft_url=              a.aircraft_url,
        )
        for a in airfleet_repository.get_all(
            db,
            airline_id=  airline_id,
            min_range_km=min_range_km,
        )
    ]