from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.orm import aliased
from app.infrastructure.database.models.airport_model import Airport
from app.infrastructure.database.models.flight_model import Flight, FlightStatus
from app.infrastructure.database.models.flight_schedule_model import FlightSchedule
from app.infrastructure.database.models.route_model import Route
from app.infrastructure.database.models.flight_model import Flight
from app.infrastructure.database.models.route_model import Route
from datetime import date
from sqlalchemy import or_
from datetime import datetime, timedelta


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
    DepAirport = aliased(Airport)
    ArrAirport = aliased(Airport)
    today = date.today()

    return (
        db.query(Flight.departs_datetime)
        .join(FlightSchedule, Flight.flight_schedule_id == FlightSchedule.flight_schedule_id)
        .join(Route, FlightSchedule.route_id == Route.route_id)
        .join(DepAirport, DepAirport.airport_id == Route.departs_airport_id)
        .join(ArrAirport, ArrAirport.airport_id == Route.arrives_airport_id)
        .join(FlightStatus, Flight.flight_status_id == FlightStatus.flight_status_id)
        .filter(
            DepAirport.city_id == from_city_id,
            ArrAirport.city_id == to_city_id,
            FlightStatus.flight_status_name != 'Cancelled',
            Flight.departs_datetime >= today,
            or_(
                FlightSchedule.flight_end_date.is_(None),
                FlightSchedule.flight_end_date >= today,
            ),
        )
        .distinct()
        .order_by(Flight.departs_datetime)
        .all()
    )


def get_leg2_flight_dates(
    db: Session,
    hub_city_id: int,
    to_city_id: int,
    leg1_date: str,
) -> list:
    DepAirport = aliased(Airport)
    ArrAirport = aliased(Airport)
    today = date.today()

    leg1 = datetime.strptime(leg1_date, "%Y-%m-%d").date()
    min_date = leg1
    max_date = leg1 + timedelta(days=1)

    return (
        db.query(Flight.departs_datetime)
        .join(FlightSchedule, Flight.flight_schedule_id == FlightSchedule.flight_schedule_id)
        .join(Route, FlightSchedule.route_id == Route.route_id)
        .join(DepAirport, DepAirport.airport_id == Route.departs_airport_id)
        .join(ArrAirport, ArrAirport.airport_id == Route.arrives_airport_id)
        .join(FlightStatus, Flight.flight_status_id == FlightStatus.flight_status_id)
        .filter(
            DepAirport.city_id == hub_city_id,
            ArrAirport.city_id == to_city_id,
            FlightStatus.flight_status_name != 'Cancelled',
            Flight.departs_datetime >= datetime.combine(min_date, datetime.min.time()),
            Flight.departs_datetime <= datetime.combine(max_date, datetime.max.time()),
            or_(
                FlightSchedule.flight_end_date.is_(None),
                FlightSchedule.flight_end_date >= today,
            ),
        )
        .distinct()
        .order_by(Flight.departs_datetime)
        .all()
    )






