from sqlalchemy.orm import Session
from app.infrastructure.database.models.airline_model import Airline


def get_all(db: Session) -> list[Airline]:
    return db.query(Airline).all()


def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Airline]:
    return db.query(Airline).offset(skip).limit(limit).all()


def get_by_id(db: Session, airline_id: int) -> Airline | None:
    return db.query(Airline).filter(Airline.airline_id == airline_id).first()