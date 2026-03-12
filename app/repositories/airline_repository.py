from sqlalchemy.orm import Session
from app.models.airline_model import Airline


def get_all(db: Session) -> list[Airline]:
    return db.query(Airline).all()