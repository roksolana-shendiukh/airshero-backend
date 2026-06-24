from sqlalchemy.orm import Session
from app.infrastructure.database.repositories import storage_repository
from app.infrastructure.database.models.airfleet_model import Airfleet
from app.infrastructure.database.models.airline_model import Airline


def get_airfleet_photos(db: Session, airfleet_id: int) -> list[str]:
    airfleet = db.query(Airfleet).filter(
        Airfleet.airfleet_id == airfleet_id
    ).first()

    if not airfleet or not airfleet.aircraft_url:
        return []

    prefix = f"airfleets/{airfleet.aircraft_url}/"
    return storage_repository.list_files(prefix)

def get_airline_logo(db: Session, airline_id: int) -> str | None:
    airline = db.query(Airline).filter(
        Airline.airline_id == airline_id
    ).first()

    if not airline or not airline.airline_url:
        return None

    prefix = f"airlines/{airline.airline_url}/"
    
    files = storage_repository.list_files(prefix)

    return files[0] if files else None


