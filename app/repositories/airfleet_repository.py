from sqlalchemy.orm import Session, joinedload
from app.models.aircraft_model import Airfleet


def get_all(db: Session) -> list[Airfleet]:
    return (
        db.query(Airfleet)
        .options(joinedload(Airfleet.manufacturer))
        .all()
    )