from sqlalchemy.orm import Session
from app.infrastructure.database.models.airport_model import Airport


def get_all(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Airport).offset(skip).limit(limit).all()