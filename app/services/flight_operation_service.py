from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth, firestore
from app.models.flight_operation_model import FlightOperation, FlightOperationStatus
from app.repositories import flight_operation_repository
from app.schemas.flight_operation_schema import (
    FlightOperationCreateDTO,
    FlightOperationUpdateDTO,
    FlightOperationDTO,
)

_TERMINAL_STATUSES = {"Completed", "Cancelled"}


def _map(op: FlightOperation) -> FlightOperationDTO:
    flight   = op.flight
    schedule = getattr(flight, 'flight_schedule', None)
    route    = getattr(schedule, 'route', None)
    dep      = getattr(route, 'departs_airport', None)
    arr      = getattr(route, 'arrives_airport', None)

    def to_time_str(t):
        if t is None:
            return None
        print(f"[to_time_str] type={type(t)}, value={t}")
        if hasattr(t, 'strftime'):
            return t.strftime('%H:%M:%S')
        return str(t)
    
    def to_datetime_str(t):
        if t is None:
            return None
        return t.isoformat()

    return FlightOperationDTO(
        flightOperationId        = op.flight_operation_id,
        flightId                 = op.flight_id,
        flightNumber             = getattr(route, 'flight_number', None),
        departsCode              = getattr(dep, 'airport_code', None),
        arrivesCode              = getattr(arr, 'airport_code', None),
        departsDatetime          = getattr(flight, 'departs_datetime', None),
        arrivesDatetime          = getattr(flight, 'arrives_datetime', None),
        statusId                 = op.flight_operation_status_id,
        statusName               = getattr(op.status, 'flight_operation_status_name', None),
        airfleetId               = op.airfleet_id,
        aircraftModel            = getattr(op.airfleet, 'aircraft_model', None),
        gateId                   = op.gate_id,
        gateCode                 = getattr(op.gate, 'gate_code', None),
        stateDescription         = getattr(op.state, 'flight_operation_state_description', None),
        actualDepartureDatetime  = to_datetime_str(op.actual_departure_date_time),
        actualArrivalDatetime    = to_datetime_str(op.actual_arrival_date_time),
        boardingStartTime        = to_time_str(op.boarding_start_time),
        boardingEndTime          = to_time_str(op.boarding_end_time),
        baggageLoadingStartTime  = to_time_str(op.baggage_loading_start_time),
        baggageLoadingEndTime    = to_time_str(op.baggage_loading_end_time),
    )


def _save_to_firestore(uid: str, operation_id: int) -> None:
    db_fs = firestore.client()
    db_fs.collection("operators").document(uid)\
        .collection("operations").document(str(operation_id))\
        .set({"operationId": operation_id})


def _clear_active_operation(uid: str, operation_id: int) -> None:
    _save_to_firestore(uid, operation_id)
    user   = firebase_auth.get_user(uid)
    claims = user.custom_claims or {}
    print(f"[CLAIMS] Terminal status, clearing operationId for uid={uid}")
    claims.pop("operationId", None)
    firebase_auth.set_custom_user_claims(uid, claims)
    print(f"[CLAIMS] Cleared successfully")


def get_all(db: Session) -> list[FlightOperationDTO]:
    return [_map(op) for op in flight_operation_repository.get_all(db)]


def get_by_id(db: Session, operation_id: int, uid: str | None = None) -> FlightOperationDTO | None:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        if uid:
            try:
                user   = firebase_auth.get_user(uid)
                claims = user.custom_claims or {}
                claims.pop("operationId", None)
                firebase_auth.set_custom_user_claims(uid, claims)
                print(f"[CLAIMS] Operation {operation_id} not found, cleared for uid={uid}")
            except Exception as e:
                print(f"[CLAIMS] Error clearing: {e}")
        return None

    mapped = _map(op)
    if uid and mapped.statusName in _TERMINAL_STATUSES:
        try:
            _clear_active_operation(uid, operation_id)
        except Exception as e:
            print(f"[CLAIMS] Error clearing: {e}")

    return mapped


def create(db: Session, data: FlightOperationCreateDTO, uid: str) -> FlightOperationDTO:
    firebase_user = firebase_auth.get_user(uid)
    claims        = firebase_user.custom_claims or {}
    if claims.get("operationId") is not None:
        raise ValueError("You already have an active operation assigned")

    op = flight_operation_repository.create(db, data)
    db.commit()

    claims["operationId"] = op.flight_operation_id
    firebase_auth.set_custom_user_claims(uid, claims)

    return _map(flight_operation_repository.get_by_id(db, op.flight_operation_id))


def update(
    db: Session,
    operation_id: int,
    data: FlightOperationUpdateDTO,
    uid: str | None = None,
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
    operation_id: int,
    uid: str | None = None,
    state_id: int | None = None,
    custom_reason: str | None = None,
) -> FlightOperationDTO | None:
    cancelled_status = db.query(FlightOperationStatus)\
        .filter(FlightOperationStatus.flight_operation_status_name == "Cancelled")\
        .first()
    if not cancelled_status:
        return None

    actual_state_id = state_id
    if custom_reason and not state_id:
        from app.models.flight_operation_model import FlightOperationState
        new_state = FlightOperationState(
            flight_operation_state_description=custom_reason
        )
        db.add(new_state)
        db.flush()
        actual_state_id = new_state.flight_operation_state_id

    data = FlightOperationUpdateDTO(
        flight_operation_status_id=cancelled_status.flight_operation_status_id,
        flight_operation_state_id=actual_state_id,
    )
    return update(db, operation_id, data, uid=uid, clear_on_terminal=True)


def complete(
    db: Session,
    operation_id: int,
    uid: str | None = None,
    state_id: int | None = None,
    custom_reason: str | None = None,
) -> FlightOperationDTO | None:
    completed_status = db.query(FlightOperationStatus)\
        .filter(FlightOperationStatus.flight_operation_status_name == "Completed")\
        .first()
    if not completed_status:
        return None

    actual_state_id = state_id
    if custom_reason and not state_id:
        from app.models.flight_operation_model import FlightOperationState
        new_state = FlightOperationState(
            flight_operation_state_description=custom_reason
        )
        db.add(new_state)
        db.flush()
        actual_state_id = new_state.flight_operation_state_id

    data = FlightOperationUpdateDTO(
        flight_operation_status_id=completed_status.flight_operation_status_id,
        flight_operation_state_id=actual_state_id,
    )
    return update(db, operation_id, data, uid=uid, clear_on_terminal=True)