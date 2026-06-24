from sqlalchemy.orm import Session
from app.infrastructure.database.models.airfleet_model import Airfleet
from app.infrastructure.database.models.airline_model import AirlineAirfleet


def get_all(
    db: Session,
    airline_id: int | None = None,
    min_range_km: float | None = None,
) -> list[Airfleet]:
    query = db.query(Airfleet)

    if airline_id is not None:
        query = query.join(
            AirlineAirfleet,
            AirlineAirfleet.airfleet_id == Airfleet.airfleet_id,
        ).filter(AirlineAirfleet.airline_id == airline_id)

    if min_range_km is not None:
        query = query.filter(Airfleet.aircraft_range_km >= min_range_km)

    return query.all()