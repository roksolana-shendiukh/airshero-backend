from sqlalchemy.orm import Session
from app.models.airport_model import Airport


def get_all(db: Session) -> list[Airport]:
    return db.query(Airport).all()