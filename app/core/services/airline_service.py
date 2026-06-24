from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.infrastructure.database.models.airline_model import Airline
from app.infrastructure.database.repositories import storage_repository


def _get_logo_url(airline_url: str | None) -> str | None:
    if not airline_url:
        return None
    prefix = f"airlines/{airline_url}/"
    files = storage_repository.list_files(prefix)
    return files[0] if files else None


def get_all_airlines(db: Session, skip: int = 0, limit: int = 50) -> list[dict]:
    airlines = db.query(Airline).offset(skip).limit(limit).all()
    return [
        {
            "airline_id":   airline.airline_id,
            "airline_name": airline.airline_name,
            "iata_code":    airline.iata_code,
            "logo":         _get_logo_url(airline.airline_url),
        }
        for airline in airlines
    ]


def get_airline_by_id(db: Session, airline_id: int) -> dict:
    airline = db.query(Airline).filter(Airline.airline_id == airline_id).first()

    if not airline:
        raise HTTPException(status_code=404, detail="Airline not found")

    return {
        "airline_id":   airline.airline_id,
        "country_id":   airline.country_id,
        "alliance_id":  airline.alliance_id,
        "airline_name": airline.airline_name,
        "iata_code":    airline.iata_code,
        "airline_url":  airline.airline_url,
        "logo":         _get_logo_url(airline.airline_url),
    }