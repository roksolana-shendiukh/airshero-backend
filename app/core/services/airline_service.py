from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.infrastructure.database.repositories import airline_repository, storage_repository


def get_logo_url(airline_url: str | None) -> str | None:
    if not airline_url:
        return None
    prefix = f"airlines/{airline_url}/"
    files  = storage_repository.list_files(prefix)
    return files[0] if files else None


def get_all_airlines(db: Session, skip: int = 0, limit: int = 50) -> list[dict]:
    airlines = airline_repository.get_all(db, skip=skip, limit=limit)
    return [
        {
            "airline_id":   a.airline_id,
            "airline_name": a.airline_name,
            "iata_code":    a.iata_code,
            "logo":         get_logo_url(a.airline_url),
        }
        for a in airlines
    ]


def get_airline_by_id(db: Session, airline_id: int) -> dict:
    airline = airline_repository.get_by_id(db, airline_id)
    if not airline:
        raise HTTPException(status_code=404, detail="Airline not found")
    return {
        "airline_id":   airline.airline_id,
        "country_id":   airline.country_id,
        "alliance_id":  airline.alliance_id,
        "airline_name": airline.airline_name,
        "iata_code":    airline.iata_code,
        "airline_url":  airline.airline_url,
        "logo":         get_logo_url(airline.airline_url),
    }