from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import flight_crew_service

router = APIRouter(prefix="/crew", tags=["Crew CRUD"])


class CrewCreateDTO(BaseModel):
    firstName:       str
    lastName:        str
    positionId:      int
    licenseTypeId:   int
    experienceYears: int


class CrewUpdateDTO(BaseModel):
    firstName:       Optional[str] = None
    lastName:        Optional[str] = None
    positionId:      Optional[int] = None
    licenseTypeId:   Optional[int] = None
    experienceYears: Optional[int] = None


@router.get("/positions")
def get_positions(
    db:   Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_positions(db)


@router.get("/license-types")
def get_license_types(
    db:   Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_license_types(db)


@router.get("")
def get_all(
    search:   Optional[str] = Query(default=None),
    position: Optional[str] = Query(default=None),
    db:       Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_all_crew(db, search, position)


@router.post("", status_code=201)
def create(
    body: CrewCreateDTO,
    db:   Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.create_crew(
        db,
        first_name=       body.firstName,
        last_name=        body.lastName,
        position_id=      body.positionId,
        license_type_id=  body.licenseTypeId,
        experience_years= body.experienceYears,
    )


@router.put("/{crew_id}")
def update(
    crew_id: int,
    body:    CrewUpdateDTO,
    db:      Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.update_crew(
        db,
        crew_id=          crew_id,
        first_name=       body.firstName,
        last_name=        body.lastName,
        position_id=      body.positionId,
        license_type_id=  body.licenseTypeId,
        experience_years= body.experienceYears,
    )


@router.delete("/{crew_id}", status_code=204)
def delete(
    crew_id: int,
    db:      Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    flight_crew_service.delete_crew(db, crew_id)