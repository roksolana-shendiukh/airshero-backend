from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.flight_operation_schema import FlightOperationCreateDTO, FlightOperationUpdateDTO
from app.services import flight_operation_service

router = APIRouter(prefix="/flight-operations", tags=["Flight Operations"])


@router.get("")
def get_all(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_operation_service.get_all(db)


@router.get("/{operation_id}")
def get_by_id(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    op = flight_operation_service.get_by_id(db, operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


@router.post("", status_code=201)
def create(
    data: FlightOperationCreateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    try:
        return flight_operation_service.create(db, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.put("/{operation_id}")
def update(
    operation_id: int,
    data: FlightOperationUpdateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    op = flight_operation_service.update(db, operation_id, data)
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


@router.delete("/{operation_id}", status_code=204)
def delete(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    if not flight_operation_service.delete(db, operation_id):
        raise HTTPException(status_code=404, detail="Flight operation not found")