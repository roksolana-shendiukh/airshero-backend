from sqlalchemy.orm import Session
from app.infrastructure.database.models.airport_model import Airport
from app.infrastructure.database.repositories import airport_repository
from app.interfaces.schemas.airport_schema import AirportDTO


def _map_airport(a: Airport) -> AirportDTO:
    return AirportDTO(
        airportId=a.airport_id,
        airportName=a.airport_name,
        airportCode=a.airport_code,
        airportAddress=a.airport_address,
        latitude=float(a.latitude) if a.latitude is not None else None,
        longitude=float(a.longitude) if a.longitude is not None else None,
    )


def get_all_airports(db: Session) -> list[AirportDTO]:
    airports = airport_repository.get_all(db)
    return [_map_airport(a) for a in airports]