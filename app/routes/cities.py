from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies.auth import require_role
from app.database import get_db
from app.models.city import CityDTO
from app.repositories import city_repository

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("/search", response_model=list[CityDTO])
def search_cities(
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = city_repository.search_cities(db, q)
    return [
        CityDTO(
            cityId=row.city_id,
            cityName=row.city_name,
            countryName=row.country_name,
        )
        for row in rows
    ]

@router.get("/alternatives/{from_city_id}", response_model=list[CityDTO])
def get_alternative_destinations(from_city_id: int, db: Session = Depends(get_db)):
    rows = city_repository.get_alternatives(db, from_city_id)
    return [
        CityDTO(
            cityId=row.city_id, 
            cityName=row.city_name, 
            countryName=row.country_name
        ) for row in rows
    ]

@router.get("/available-dates")
def read_available_dates(
    from_city: int, 
    to_city: int, 
    db: Session = Depends(get_db)
):
    return city_repository.get_available_dates(db, from_city, to_city)