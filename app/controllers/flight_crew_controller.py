from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import flight_crew_service

router = APIRouter(prefix="/flight-operations", tags=["Flight Crew"])


class AssignCrewRequest(BaseModel):
    crewId: int


@router.get("/{operation_id}/crew")
def get_crew(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_crew(db, operation_id)


@router.get("/{operation_id}/crew/available")
def get_available_crew(
    operation_id: int,
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="airlineId not found in token")
    return flight_crew_service.get_available_crew(
        db, operation_id, airline_id, search=search
    )


@router.get("/{operation_id}/crew/required")
def get_required_positions(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.get_required_positions(db, operation_id)


@router.get("/{operation_id}/crew/validate")
def validate_crew(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_crew_service.validate_crew(db, operation_id)


@router.post("/{operation_id}/crew", status_code=201)
def assign_crew(
    operation_id: int,
    body: AssignCrewRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="airlineId not found in token")
    try:
        return flight_crew_service.assign_crew(
            db, operation_id, body.crewId, airline_id
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{operation_id}/crew/{crew_id}", status_code=204)
def remove_crew(
    operation_id: int,
    crew_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    if not flight_crew_service.remove_crew(db, operation_id, crew_id):
        raise HTTPException(status_code=404, detail="Crew member not found")