from sqlalchemy.orm import Session

from app.infrastructure.database.repositories import baggage_repository


def get_baggage_options(db: Session, flight_class_id: int) -> list:
    return baggage_repository.get_baggage_options(db, flight_class_id)