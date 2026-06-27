from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time as time_type

from app.core.services import flight_crew_service, flight_operation_service, gate_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role, require_any_role
from app.interfaces.schemas.flight_operation_schema import (
    FlightOperationCreateDTO,
    FlightOperationUpdateDTO,
    OperationStateRequestDTO,
)

router = APIRouter(prefix="/flight-operations", tags=["Flight Operations"])

_TIMELINE_FIELDS = {
    "boarding-start": "boarding_start_time",
    "boarding-end":   "boarding_end_time",
    "baggage-start":  "baggage_loading_start_time",
    "baggage-end":    "baggage_loading_end_time",
    "departure":      "actual_departure_date_time",
    "arrival":        "actual_arrival_date_time",
}


@router.get("")
def get_all(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_operation_service.get_all(db)


@router.get("/statuses")
def get_statuses(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_operation_service.get_statuses(db)


@router.get("/states")
def get_states(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return flight_operation_service.get_states(db)


@router.post("", status_code=201)
def create(
    data: FlightOperationCreateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    try:
        return flight_operation_service.create(db, data, uid=user["uid"])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/{operation_id}/gates")
def get_available_gates(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return gate_service.get_available_gates(db, operation_id)


@router.post("/{operation_id}/timeline/{step}", status_code=200)
def set_timeline_step(
    operation_id: int,
    step: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("flightOperator", "checkInAgent")),
):
    if step not in _TIMELINE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Unknown step '{step}'")
    try:
        return flight_operation_service.set_timeline_step(db, operation_id, step)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{operation_id}/timeline/{step}/force", status_code=200)
def set_timeline_step_force(
    operation_id: int,
    step: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("flightOperator", "checkInAgent")),
):
    if step not in _TIMELINE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Unknown step '{step}'")
    try:
        return flight_operation_service.set_timeline_step(db, operation_id, step, force=True)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{operation_id}")
def get_by_id(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    op = flight_operation_service.get_by_id(db, operation_id, uid=user["uid"])
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


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


@router.put("/{operation_id}/gate/{gate_id}")
def update_operation_gate(
    operation_id: int,
    gate_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    try:
        result = flight_operation_service.change_gate(db, operation_id, gate_id)
        if not result:
            raise HTTPException(status_code=404, detail="Operation not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{operation_id}/cancel", status_code=200)
def cancel_operation(
    operation_id: int,
    body: OperationStateRequestDTO = OperationStateRequestDTO(),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    op = flight_operation_service.cancel(
        db, operation_id,
        uid=user["uid"],
        state_id=body.state_id,
        custom_reason=body.custom_reason,
    )
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


@router.post("/{operation_id}/complete", status_code=200)
def complete_operation(
    operation_id: int,
    body: OperationStateRequestDTO = OperationStateRequestDTO(),
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    op = flight_operation_service.complete(
        db, operation_id,
        uid=user["uid"],
        state_id=body.state_id,
        custom_reason=body.custom_reason,
    )
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
    
    