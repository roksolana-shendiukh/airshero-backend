from sqlalchemy.orm import Session
from datetime import datetime, time as time_type
import logging

from firebase_admin import auth as firebase_auth, firestore

from app.infrastructure.database.repositories import flight_operation_repository
from app.interfaces.schemas.flight_operation_schema import (
    FlightOperationCreateDTO,
    FlightOperationUpdateDTO,
    FlightOperationDTO,
)
from app.core.services import flight_crew_service

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {"Completed", "Cancelled"}

_TIMELINE_FIELDS = {
    "boarding-start": "boarding_start_time",
    "boarding-end":   "boarding_end_time",
    "baggage-start":  "baggage_loading_start_time",
    "baggage-end":    "baggage_loading_end_time",
    "departure":      "actual_departure_date_time",
    "arrival":        "actual_arrival_date_time",
}

_STEP_TO_STATUS = {
    "boarding-start": "Boarding",
    "boarding-end":   "Boarding",
    "baggage-start":  "Baggage Loading",
    "baggage-end":    "Baggage Loading",
    "departure":      "Departed",
    "arrival":        "Arrived",
}

_MIN_BAGGAGE_MINUTES  = 15
_ARRIVAL_WARN_MINUTES = 60


def get_statuses(db: Session) -> list[dict]:
    return flight_operation_repository.get_statuses(db)


def get_states(db: Session) -> list[dict]:
    return flight_operation_repository.get_states(db)


def set_timeline_step(
    db: Session,
    operation_id: int,
    step:         str,
    force:        bool = False,
) -> dict | None:
    now = datetime.now()
    op  = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return None

    if not force:
        if step == "boarding-start":
            validation = flight_crew_service.validate_crew(db, operation_id)
            if not validation.get("valid"):
                missing     = validation.get("missing", {})
                missing_str = ", ".join(f"{v}x {k}" for k, v in missing.items())
                raise ValueError(f"Crew is not complete. Missing: {missing_str}")

        if step == "baggage-end" and op.baggage_loading_start_time:
            start = op.baggage_loading_start_time
            if isinstance(start, time_type):
                start = datetime.combine(now.date(), start)
            diff = (now - start).total_seconds() / 60
            if diff < _MIN_BAGGAGE_MINUTES:
                raise ValueError(
                    f"Baggage loading duration is only {int(diff)} min. "
                    f"Minimum is {_MIN_BAGGAGE_MINUTES} min."
                )

        if step == "arrival" and op.actual_departure_date_time:
            flight = flight_operation_repository.get_flight_for_operation(db, op.flight_id)
            if flight:
                scheduled_duration = (
                    flight.arrives_datetime - flight.departs_datetime
                ).total_seconds() / 60
                actual_duration = (now - op.actual_departure_date_time).total_seconds() / 60
                min_duration    = scheduled_duration * 0.8

                if actual_duration < min_duration:
                    raise ValueError(
                        f"Flight duration is only {int(actual_duration)} min, "
                        f"but scheduled is {int(scheduled_duration)} min "
                        f"(minimum 80% = {int(min_duration)} min)."
                    )

                delay = (now - flight.arrives_datetime).total_seconds() / 60
                if abs(delay) > _ARRIVAL_WARN_MINUTES:
                    direction = "late" if delay > 0 else "early"
                    raise ValueError(
                        f"Arrival is {int(abs(delay))} min {direction} "
                        f"compared to schedule."
                    )

    status_name = _STEP_TO_STATUS.get(step)
    status_id   = None
    if status_name:
        status = flight_operation_repository.get_status_by_name(db, status_name)
        if status:
            status_id = status.flight_operation_status_id

    field = _TIMELINE_FIELDS[step]
    data  = FlightOperationUpdateDTO(**{field: now}, flight_operation_status_id=status_id)
    return update(db, operation_id, data)


def _map(op) -> FlightOperationDTO:
    flight   = op.flight
    schedule = getattr(flight, 'flight_schedule', None)
    route    = getattr(schedule, 'route', None)
    dep      = getattr(route, 'departs_airport', None)
    arr      = getattr(route, 'arrives_airport', None)

    def to_time_str(t):
        if t is None:
            return None
        if hasattr(t, 'strftime'):
            return t.strftime('%H:%M:%S')
        return str(t)

    def to_datetime_str(t):
        if t is None:
            return None
        return t.isoformat()

    return FlightOperationDTO(
        flight_operation_id=       op.flight_operation_id,
        schedule_flight_id=        op.schedule_flight_id,
        flight_number=             getattr(route, 'flight_number', None),
        departs_code=              getattr(dep, 'airport_code', None),
        arrives_code=              getattr(arr, 'airport_code', None),
        departs_datetime=          getattr(flight, 'departs_datetime', None),
        arrives_datetime=          getattr(flight, 'arrives_datetime', None),
        status_id=                 op.flight_operation_status_id,
        status_name=               getattr(op.status, 'flight_operation_status_name', None),
        airfleet_id=               op.airfleet_id,
        aircraft_model=            getattr(op.airfleet, 'aircraft_model', None),
        gate_id=                   op.gate_id,
        gate_code=                 getattr(op.gate, 'gate_code', None),
        state_description=         getattr(op.state, 'flight_operation_state_description', None),
        actual_departure_datetime= to_datetime_str(op.actual_departure_date_time),
        actual_arrival_datetime=   to_datetime_str(op.actual_arrival_date_time),
        boarding_start_time=       to_time_str(op.boarding_start_time),
        boarding_end_time=         to_time_str(op.boarding_end_time),
        baggage_loading_start_time=to_time_str(op.baggage_loading_start_time),
        baggage_loading_end_time=  to_time_str(op.baggage_loading_end_time),
    )


def _save_to_firestore(uid: str, operation_id: int) -> None:
    db_fs = firestore.client()
    db_fs.collection("operators").document(uid)\
        .collection("operations").document(str(operation_id))\
        .set({"operation_id": operation_id})


def _clear_active_operation(uid: str, operation_id: int) -> None:
    _save_to_firestore(uid, operation_id)
    user   = firebase_auth.get_user(uid)
    claims = user.custom_claims or {}
    logger.info(f"[CLAIMS] Terminal status, clearing operation_id for uid={uid}")
    claims.pop("operation_id", None)  # виправлено: "operationId" → "operation_id"
    firebase_auth.set_custom_user_claims(uid, claims)
    logger.info(f"[CLAIMS] Cleared successfully for uid={uid}")


def get_all(db: Session) -> list[FlightOperationDTO]:
    return [_map(op) for op in flight_operation_repository.get_all(db)]


def get_by_id(
    db: Session,
    operation_id: int,
    uid: str | None = None,
) -> FlightOperationDTO | None:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        if uid:
            try:
                user   = firebase_auth.get_user(uid)
                claims = user.custom_claims or {}
                claims.pop("operation_id", None)  # виправлено: "operationId" → "operation_id"
                firebase_auth.set_custom_user_claims(uid, claims)
                logger.info(f"[CLAIMS] Operation {operation_id} not found, cleared for uid={uid}")
            except Exception as e:
                logger.error(f"[CLAIMS] Error clearing: {e}")
        return None

    mapped = _map(op)
    if uid and mapped.status_name in _TERMINAL_STATUSES:
        try:
            _clear_active_operation(uid, operation_id)
        except Exception as e:
            logger.error(f"[CLAIMS] Error clearing: {e}")

    return mapped


def create(db: Session, data: FlightOperationCreateDTO, uid: str) -> FlightOperationDTO:
    firebase_user = firebase_auth.get_user(uid)
    claims        = firebase_user.custom_claims or {}
    if claims.get("operation_id") is not None:  # виправлено: "operationId" → "operation_id"
        raise ValueError("You already have an active operation assigned")

    op = flight_operation_repository.create(db, data)
    db.commit()

    claims["operation_id"] = op.flight_operation_id  # виправлено: "operationId" → "operation_id"
    firebase_auth.set_custom_user_claims(uid, claims)

    return _map(flight_operation_repository.get_by_id(db, op.flight_operation_id))


def update(
    db: Session,
    operation_id:      int,
    data:              FlightOperationUpdateDTO,
    uid:               str | None = None,
    clear_on_terminal: bool = False,
) -> FlightOperationDTO | None:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return None
    flight_operation_repository.update(db, op, data)
    db.commit()

    updated     = flight_operation_repository.get_by_id(db, operation_id)
    status_name = getattr(updated.status, 'flight_operation_status_name', None)

    if uid and clear_on_terminal and status_name in _TERMINAL_STATUSES:
        _clear_active_operation(uid, operation_id)

    return _map(updated)


def delete(db: Session, operation_id: int) -> bool:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return False
    flight_operation_repository.delete(db, op)
    db.commit()
    return True


def cancel(
    db: Session,
    operation_id:  int,
    uid:           str | None = None,
    state_id:      int | None = None,
    custom_reason: str | None = None,
) -> FlightOperationDTO | None:
    cancelled_status = flight_operation_repository.get_status_by_name(db, "Cancelled")
    if not cancelled_status:
        return None

    actual_state_id = _resolve_state_id(db, state_id, custom_reason)
    data = FlightOperationUpdateDTO(
        flight_operation_status_id=cancelled_status.flight_operation_status_id,
        flight_operation_state_id= actual_state_id,
    )
    return update(db, operation_id, data, uid=uid, clear_on_terminal=True)


def complete(
    db: Session,
    operation_id:  int,
    uid:           str | None = None,
    state_id:      int | None = None,
    custom_reason: str | None = None,
) -> FlightOperationDTO | None:
    completed_status = flight_operation_repository.get_status_by_name(db, "Completed")
    if not completed_status:
        return None

    actual_state_id = _resolve_state_id(db, state_id, custom_reason)
    data = FlightOperationUpdateDTO(
        flight_operation_status_id=completed_status.flight_operation_status_id,
        flight_operation_state_id= actual_state_id,
    )
    return update(db, operation_id, data, uid=uid, clear_on_terminal=True)


def _resolve_state_id(
    db:            Session,
    state_id:      int | None,
    custom_reason: str | None,
) -> int | None:
    if custom_reason and not state_id:
        return flight_operation_repository.create_custom_state(db, custom_reason)
    return state_id


def change_gate(db: Session, operation_id: int, new_gate_id: int):
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return None
    if op.boarding_start_time is not None:
        raise ValueError("Cannot change gate: boarding has already started")
    flight_operation_repository.update(db, op, FlightOperationUpdateDTO(gate_id=new_gate_id))
    db.commit()
    return _map(flight_operation_repository.get_by_id(db, operation_id))