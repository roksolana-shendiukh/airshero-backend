from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from app.models.airport_model import Airport
from app.models.flight_model import Flight, FlightClass
from app.models.flight_schedule_model import FlightSchedule
from app.models.route_model import Route


_SEARCH_CITIES = text("""
    SELECT DISTINCT TOP 10
        ci.city_id,
        ci.city_name,
        co.country_name,
        CASE
            WHEN ci.city_name LIKE :q_start THEN 0
            WHEN co.country_name LIKE :q_start THEN 1
            ELSE 2
        END AS sort_order
    FROM City ci
    JOIN Country co ON ci.country_id = co.country_id
    WHERE
        ci.city_name LIKE :q
        OR co.country_name LIKE :q
    ORDER BY sort_order, ci.city_name
""")


def search_cities(db: Session, query: str) -> list:
    return db.execute(_SEARCH_CITIES, {
        "q":       f"%{query}%",
        "q_start": f"{query}%",
    }).fetchall()


def get_alternative_destinations(db: Session, from_city_id: int) -> list:
    return (
        db.query(
            Airport.city_id.label("city_id"),
        )
        .join(Route, Route.arrives_airport_id == Airport.airport_id)
        .join(FlightSchedule, FlightSchedule.route_id == Route.route_id)
        .join(Flight, Flight.flight_schedule_id == FlightSchedule.flight_schedule_id)
        .join(Airport.__table__.alias("dep"), text("dep.airport_id = Route.departs_airport_id"))
        .filter(text("dep.city_id = :from_id").bindparams(from_id=from_city_id))
        .distinct()
        .all()
    )


def get_available_flight_dates(db: Session, from_city_id: int, to_city_id: int) -> list:
    return (
        db.query(Flight.departs_datetime)
        .join(FlightSchedule, Flight.flight_schedule_id == FlightSchedule.flight_schedule_id)
        .join(Route, FlightSchedule.route_id == Route.route_id)
        .join(
            Airport.__table__.alias("dep"),
            text("dep.airport_id = Route.departs_airport_id"),
        )
        .join(
            Airport.__table__.alias("arr"),
            text("arr.airport_id = Route.arrives_airport_id"),
        )
        .filter(
            text("dep.city_id = :from_id").bindparams(from_id=from_city_id),
            text("arr.city_id = :to_id").bindparams(to_id=to_city_id),
        )
        .distinct()
        .order_by(Flight.departs_datetime)
        .all()
    )