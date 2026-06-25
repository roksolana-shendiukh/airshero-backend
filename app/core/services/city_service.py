from sqlalchemy.orm import Session
from app.infrastructure.database.repositories import city_repository
from app.interfaces.schemas.city_schema import CityDTO
from app.infrastructure.database.repositories import route_repository

def get_leg2_available_dates(db, from_city, hub_city, to_city, leg1_date):
    return route_repository.get_leg2_dates_with_suggestions(
        db, from_city, hub_city, to_city, leg1_date
    )

def get_leg1_connecting_dates(db, from_city, hub_city, to_city):
    return route_repository.get_leg1_dates_with_connections(
        db, from_city, hub_city, to_city
    )

def search_cities(db: Session, query: str) -> list[CityDTO]:
    rows = city_repository.search_cities(db, query)
    return [
        CityDTO(
            cityId=row.city_id,
            cityName=row.city_name,
            countryName=row.country_name,
        )
        for row in rows
    ]


def get_alternative_destinations(db: Session, from_city_id: int) -> list[CityDTO]:
    rows = city_repository.get_alternative_destinations(db, from_city_id)
    return [
        CityDTO(
            cityId=row.city_id,
            cityName=row.city_name,
            countryName=row.country_name,
        )
        for row in rows
    ]


def get_available_dates(db: Session, from_city_id: int, to_city_id: int) -> list[str]:
    rows = city_repository.get_available_flight_dates(db, from_city_id, to_city_id)
    print(f"Raw rows count: {len(rows)}")
    for row in rows:
        print(f"  {row.departs_datetime}")
    dates = list({row.departs_datetime.strftime("%Y-%m-%d") for row in rows})
    print(f"After set: {dates}")
    return dates

def get_leg2_dates_with_suggestions(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
    leg1_date: str,
) -> dict:
    from app.infrastructure.database.repositories import route_repository
    return route_repository.get_leg2_dates_with_suggestions(
        db, from_city_id, hub_city_id, to_city_id, leg1_date
    )




