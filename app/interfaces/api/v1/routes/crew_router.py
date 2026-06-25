from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.crew_schema import CrewCreateDTO, CrewUpdateDTO
from app.core.services import flight_crew_service

router = APIRouter(prefix="/crew", tags=["Crew"])


@router.get("/positions")
def get_positions(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_positions(db)


@router.get("/license-types")
def get_license_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_license_types(db)


@router.get("")
def get_all_crew(
    search:   Optional[str] = Query(default=None),
    position: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_all_crew(db, search, position)


@router.post("", status_code=201)
def create_crew(
    body: CrewCreateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.create_crew(
        db,
        first_name=      body.first_name,
        last_name=       body.last_name,
        position_id=     body.position_id,
        license_type_id= body.license_type_id,
        experience_years=body.experience_years,
    )


@router.put("/{crew_id}")
def update_crew(
    crew_id: int,
    body: CrewUpdateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.update_crew(
        db,
        crew_id=         crew_id,
        first_name=      body.first_name,
        last_name=       body.last_name,
        position_id=     body.position_id,
        license_type_id= body.license_type_id,
        experience_years=body.experience_years,
    )


@router.delete("/{crew_id}", status_code=204)
def delete_crew(
    crew_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    flight_crew_service.delete_crew(db, crew_id)