from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.infrastructure.database.models.airline_model import Airline
from app.infrastructure.database.repositories import storage_repository

router = APIRouter(prefix="/airlines", tags=["Airlines"])

def get_airline_logo_url(airline_url_path: str) -> str | None:
    if not airline_url_path:
        return None
    
    prefix = f"airlines/{airline_url_path}/"
    files = storage_repository.list_files(prefix)
    
    return files[0] if files else None

@router.get("/{airline_id}")
def get_airline_info(airline_id: int, db: Session = Depends(get_db)):
    airline = db.query(Airline).filter(Airline.airline_id == airline_id).first()
    
    if not airline:
        raise HTTPException(status_code=404, detail="Airline not found")

    logo_url = get_airline_logo_url(airline.airline_url)

    return {
        "airline_id": airline.airline_id,
        "country_id": airline.country_id,
        "airline_name": airline.airline_name,
        "iata_code": airline.iata_code,
        "airline_url": airline.airline_url,
        "logo": logo_url
    }

@router.get("/")
def list_all_airlines(db: Session = Depends(get_db)):
    airlines = db.query(Airline).all()
    result = []
    
    for airline in airlines:
        result.append({
            "airline_id": airline.airline_id,
            "airline_name": airline.airline_name,
            "iata_code": airline.iata_code,
            "logo": get_airline_logo_url(airline.airline_url)
        })
        
    return result