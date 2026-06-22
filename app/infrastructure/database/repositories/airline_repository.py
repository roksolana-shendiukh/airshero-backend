from sqlalchemy.orm import Session
from app.infrastructure.database.models.airline_model import Airline


def get_all(db: Session) -> list[Airline]:
    return db.query(Airline).all()