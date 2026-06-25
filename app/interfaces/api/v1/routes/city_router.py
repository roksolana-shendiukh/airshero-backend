from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.city_schema import CityDTO
from app.core.services import city_service

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("/search", response_model=list[CityDTO])
def search_cities(
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return city_service.search_cities(db, q)


@router.get("/available-dates/leg1-connecting")
def get_leg1_connecting_dates(
    from_city: int,
    hub_city: int,
    to_city: int,
    db: Session = Depends(get_db),
):
    return city_service.get_leg1_connecting_dates(db, from_city, hub_city, to_city)


@router.get("/available-dates/leg2")
def get_leg2_available_dates(
    from_city: int,
    hub_city: int,
    to_city: int,
    leg1_date: str,
    db: Session = Depends(get_db),
):
    return city_service.get_leg2_available_dates(db, from_city, hub_city, to_city, leg1_date)


@router.get("/available-dates")
def get_available_dates(
    from_city: int,
    to_city: int,
    db: Session = Depends(get_db),
):
    return city_service.get_available_dates(db, from_city, to_city)


@router.get("/alternatives/{from_city_id}", response_model=list[CityDTO])
def get_alternative_destinations(
    from_city_id: int,
    db: Session = Depends(get_db),
):
    return city_service.get_alternative_destinations(db, from_city_id)

