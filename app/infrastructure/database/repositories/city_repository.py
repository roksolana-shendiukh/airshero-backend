from sqlalchemy.orm import Session, aliased
from sqlalchemy import text, or_
from datetime import date, datetime, timedelta

from app.infrastructure.database.models.airport_model import Airport
from app.infrastructure.database.models.flight_model import Flight, Route
from app.infrastructure.database.models.flight_operation_model import (
    ScheduledFlight, FlightStatus
)
from app.infrastructure.database.models.flight_schedule_model import (
    FlightSchedule, FlightSeason
)


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


def _base_scheduled_query(db: Session):
    """
    Базовий join-ланцюжок який використовується в кількох функціях:
    ScheduledFlight → Flight → Route → DepAirport / ArrAirport
                   → FlightStatus
    """
    DepAirport = aliased(Airport, name="dep")
    ArrAirport = aliased(Airport, name="arr")

    q = (
        db.query(ScheduledFlight, DepAirport, ArrAirport)
        .join(Flight, Flight.flight_id == ScheduledFlight.flight_id)
        .join(Route, Route.route_id == Flight.route_id)
        .join(DepAirport, DepAirport.airport_id == Route.departs_airport_id)
        .join(ArrAirport, ArrAirport.airport_id == Route.arrives_airport_id)
        .join(FlightStatus, FlightStatus.flight_status_id == ScheduledFlight.flight_status_id)
    )
    return q, DepAirport, ArrAirport


def get_alternative_destinations(db: Session, from_city_id: int) -> list:
    today = date.today()
    q, DepAirport, ArrAirport = _base_scheduled_query(db)

    return (
        q.with_entities(ArrAirport.city_id.label("city_id"))
        .filter(
            DepAirport.city_id == from_city_id,
            FlightStatus.flight_status_name != "Cancelled",
            ScheduledFlight.departs_date >= today,
        )
        .distinct()
        .all()
    )


def get_available_flight_dates(
    db: Session,
    from_city_id: int,
    to_city_id: int,
) -> list:
    today = date.today()
    q, DepAirport, ArrAirport = _base_scheduled_query(db)

    return (
        q.with_entities(ScheduledFlight.departs_date)
        .filter(
            DepAirport.city_id == from_city_id,
            ArrAirport.city_id == to_city_id,
            FlightStatus.flight_status_name != "Cancelled",
            ScheduledFlight.departs_date >= today,
        )
        .distinct()
        .order_by(ScheduledFlight.departs_date)
        .all()
    )


def get_leg2_flight_dates(
    db: Session,
    hub_city_id: int,
    to_city_id: int,
    leg1_date: str,
) -> list:
    today = date.today()
    leg1 = datetime.strptime(leg1_date, "%Y-%m-%d").date()
    max_date = leg1 + timedelta(days=1)

    q, DepAirport, ArrAirport = _base_scheduled_query(db)

    return (
        q.with_entities(ScheduledFlight.departs_date)
        .filter(
            DepAirport.city_id == hub_city_id,
            ArrAirport.city_id == to_city_id,
            FlightStatus.flight_status_name != "Cancelled",
            ScheduledFlight.departs_date >= leg1,
            ScheduledFlight.departs_date <= max_date,
        )
        .distinct()
        .order_by(ScheduledFlight.departs_date)
        .all()
    )

