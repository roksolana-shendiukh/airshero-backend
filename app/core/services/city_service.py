import logging
from sqlalchemy.orm import Session

from app.infrastructure.database.repositories import city_repository, route_repository
from app.interfaces.schemas.city_schema import CityDTO

logger = logging.getLogger(__name__)


def search_cities(db: Session, query: str) -> list[CityDTO]:
    rows = city_repository.search_cities(db, query)
    return [
        CityDTO(
            city_id=     row.city_id,
            city_name=   row.city_name,
            country_name=row.country_name,
        )
        for row in rows
    ]


def get_alternative_destinations(db: Session, from_city_id: int) -> list[CityDTO]:
    rows = city_repository.get_alternative_destinations(db, from_city_id)
    return [
        CityDTO(
            city_id=     row.city_id,
            city_name=   row.city_name,
            country_name=row.country_name,
        )
        for row in rows
    ]


def get_available_dates(db: Session, from_city_id: int, to_city_id: int) -> list[str]:
    rows = city_repository.get_available_flight_dates(db, from_city_id, to_city_id)
    return list({row.departs_datetime.strftime("%Y-%m-%d") for row in rows})


def get_leg1_connecting_dates(
    db: Session,
    from_city:  int,
    hub_city:   int,
    to_city:    int,
) -> dict:
    return route_repository.get_leg1_dates_with_connections(
        db, from_city, hub_city, to_city
    )


def get_leg2_available_dates(
    db: Session,
    from_city:  int,
    hub_city:   int,
    to_city:    int,
    leg1_date:  str,
) -> dict:
    return route_repository.get_leg2_dates_with_suggestions(
        db, from_city, hub_city, to_city, leg1_date
    )