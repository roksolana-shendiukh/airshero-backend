from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time as time_type

from app.database import get_db
from app.dependencies.auth import require_role, require_any_role
from app.schemas.flight_operation_schema import FlightOperationCreateDTO, FlightOperationUpdateDTO, OperationStateRequestDTO
from app.services import flight_operation_service, gate_service, flight_crew_service
from app.models.flight_operation_model import FlightOperationStatus
from app.models.flight_operation_model import FlightOperation
from app.models.flight_model import Flight

router = APIRouter(prefix="/flight-operations", tags=["Flight Operations"])

_TIMELINE_FIELDS = {
    "boarding-start":  "boarding_start_time",
    "boarding-end":    "boarding_end_time",
    "baggage-start":   "baggage_loading_start_time",
    "baggage-end":     "baggage_loading_end_time",
    "departure":       "actual_departure_date_time",
    "arrival":         "actual_arrival_date_time",
}

_STEP_TO_STATUS = {
    "boarding-start":  "Boarding",
    "boarding-end":    "Boarding",
    "baggage-start":   "Baggage Loading",
    "baggage-end":     "Baggage Loading",
    "departure":       "Departed",
    "arrival":         "Arrived",
}

_MIN_BOARDING_MINUTES = 20
_MIN_BAGGAGE_MINUTES  = 15
_ARRIVAL_WARN_MINUTES = 60


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
    statuses = db.query(FlightOperationStatus).all()
    return [
        {
            "flightOperationStatusId":   s.flight_operation_status_id,
            "flightOperationStatusName": s.flight_operation_status_name,
        }
        for s in statuses
    ]


@router.get("/states")
def get_states(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    from app.models.flight_operation_model import FlightOperationState
    states = db.query(FlightOperationState).all()
    return [
        {
            "stateId": s.flight_operation_state_id,
            "description": s.flight_operation_state_description,
        }
        for s in states
    ]


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


@router.put("/{operation_id}")
def update(
    operation_id: int,
    data: FlightOperationUpdateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    # PUT не очищає claims — тільки оновлює дані
    op = flight_operation_service.update(db, operation_id, data)
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


@router.post("/{operation_id}/timeline/{step}", status_code=200)
def set_timeline_step(
    operation_id: int,
    step: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("flightOperator", "checkInAgent")),
):
    if step not in _TIMELINE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Unknown step '{step}'")

    now = datetime.now()
    op  = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")

    if step == "boarding-start":
        validation = flight_crew_service.validate_crew(db, operation_id)
        if not validation.get("valid"):
            missing     = validation.get("missing", {})
            missing_str = ", ".join(f"{v}x {k}" for k, v in missing.items())
            raise HTTPException(
                status_code=422,
                detail=f"Crew is not complete. Missing: {missing_str}"
            )

    if step == "baggage-end" and op.baggage_loading_start_time:
        start = op.baggage_loading_start_time
        if isinstance(start, time_type):
            start = datetime.combine(now.date(), start)
        diff = (now - start).total_seconds() / 60
        if diff < _MIN_BAGGAGE_MINUTES:
            raise HTTPException(
                status_code=422,
                detail=f"Baggage loading duration is only {int(diff)} min. Minimum is {_MIN_BAGGAGE_MINUTES} min. Are you sure?"
            )

    if step == "arrival" and op.actual_departure_date_time:
        flight = db.query(Flight).filter(
            Flight.flight_id == op.flight_id
        ).first()
        if flight:
            scheduled_duration = (
                flight.arrives_datetime - flight.departs_datetime
            ).total_seconds() / 60

            dep = op.actual_departure_date_time
            actual_duration = (now - dep).total_seconds() / 60
            min_duration = scheduled_duration * 0.8

            if actual_duration < min_duration:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Flight duration is only {int(actual_duration)} min, "
                        f"but scheduled is {int(scheduled_duration)} min "
                        f"(minimum 80% = {int(min_duration)} min). "
                        f"Are you sure the flight has arrived?"
                    )
                )
            scheduled_arrival = flight.arrives_datetime
            scheduled_arrival = flight.arrives_datetime
            delay = (now - scheduled_arrival).total_seconds() / 60
            if abs(delay) > _ARRIVAL_WARN_MINUTES:
                direction = "late" if delay > 0 else "early"
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Arrival is {int(abs(delay))} min {direction} "
                        f"compared to schedule. Are you sure?"
                    )
                )

    status_name = _STEP_TO_STATUS.get(step)
    status_id   = None
    if status_name:
        status = db.query(FlightOperationStatus)\
            .filter(FlightOperationStatus.flight_operation_status_name == status_name)\
            .first()
        if status:
            status_id = status.flight_operation_status_id

    field  = _TIMELINE_FIELDS[step]
    data   = FlightOperationUpdateDTO(**{field: now}, flight_operation_status_id=status_id)
    result = flight_operation_service.update(db, operation_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return result


@router.post("/{operation_id}/timeline/{step}/force", status_code=200)
def set_timeline_step_force(
    operation_id: int,
    step: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    if step not in _TIMELINE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Unknown step '{step}'")

    now = datetime.now()
    field       = _TIMELINE_FIELDS[step]
    status_name = _STEP_TO_STATUS.get(step)

    status_id = None
    if status_name:
        status = db.query(FlightOperationStatus)\
            .filter(FlightOperationStatus.flight_operation_status_name == status_name)\
            .first()
        if status:
            status_id = status.flight_operation_status_id

    data = FlightOperationUpdateDTO(
        **{field: now},
        flight_operation_status_id=status_id,
    )
    op = flight_operation_service.update(db, operation_id, data)
    if not op:
        raise HTTPException(status_code=404, detail="Flight operation not found")
    return op


@router.get("/{operation_id}/gates")
def get_available_gates(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return gate_service.get_available_gates(db, operation_id)


@router.delete("/{operation_id}", status_code=204)
def delete(
    operation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    if not flight_operation_service.delete(db, operation_id):
        raise HTTPException(status_code=404, detail="Flight operation not found")




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





