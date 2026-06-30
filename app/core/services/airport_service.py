from sqlalchemy.orm import Session

from app.infrastructure.database.repositories import airport_repository
from app.interfaces.schemas.airport_schema import AirportDTO


def _map_airport(a) -> AirportDTO:
    return AirportDTO(
        airport_id=      a.airport_id,
        airport_name=    a.airport_name,
        airport_code=    a.airport_code,
        airport_address= a.airport_address,
        latitude=        float(a.latitude)  if a.latitude  is not None else None,
        longitude=       float(a.longitude) if a.longitude is not None else None,
    )


def get_all_airports(db: Session, skip: int = 0, limit: int = 50) -> list[AirportDTO]:
    return [_map_airport(a) for a in airport_repository.get_all(db, skip=skip, limit=limit)]