from sqlalchemy.orm import Session
from app.repositories import storage_repository
from app.models.airfleet_model import Airfleet


def get_airfleet_photos(db: Session, airfleet_id: int) -> list[str]:
    airfleet = db.query(Airfleet).filter(
        Airfleet.airfleet_id == airfleet_id
    ).first()

    if not airfleet or not airfleet.aircraft_url:
        return []

    prefix = f"airfleets/{airfleet.aircraft_url}/"
    return storage_repository.list_files(prefix)