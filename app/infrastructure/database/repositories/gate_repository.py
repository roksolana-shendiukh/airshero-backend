from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.infrastructure.database.models.airfleet_model import Gate
from app.infrastructure.database.models.airfleet_model import Terminal, TerminalType
from app.infrastructure.database.models.flight_operation_model import (
    FlightOperation, ScheduledFlight
)
from app.infrastructure.database.models.flight_model import Flight


def _get_busy_gate_ids(
    db: Session,
    dep_dt,
    arr_dt,
    exclude_operation_id: int | None = None,
) -> set[int]:
    if not dep_dt:
        return set()

    q = (
        db.query(FlightOperation.gate_id)
        .filter(
            FlightOperation.gate_id.isnot(None),
            FlightOperation.actual_departure_date_time.isnot(None),
            FlightOperation.actual_departure_date_time < (arr_dt or dep_dt),
            or_(
                FlightOperation.actual_arrival_date_time > dep_dt,
                FlightOperation.actual_arrival_date_time.is_(None),
            ),
        )
    )
    if exclude_operation_id is not None:
        q = q.filter(
            FlightOperation.flight_operation_id != exclude_operation_id
        )

    return {r.gate_id for r in q.all() if r.gate_id}


def _get_gates_for_airport(
    db: Session,
    airport_id: int,
    terminal_type_name: str,
) -> list[Gate]:
    allowed = _allowed_terminal_types(terminal_type_name)
    return (
        db.query(Gate)
        .options(
            joinedload(Gate.terminal)
            .joinedload(Terminal.terminal_type)
        )
        .join(Gate.terminal)
        .join(Terminal.terminal_type)
        .filter(
            Terminal.airport_id == airport_id,
            TerminalType.terminal_type_name.in_(allowed),
        )
        .all()
    )


def get_all_for_flight(
    db: Session,
    flight_id: int,
    airport_id: int,
    terminal_type_name: str,
) -> list[tuple[Gate, bool]]:
    existing_op = (
        db.query(FlightOperation)
        .join(ScheduledFlight,
              ScheduledFlight.schedule_flight_id == FlightOperation.schedule_flight_id)
        .filter(ScheduledFlight.flight_id == flight_id)
        .order_by(FlightOperation.flight_operation_id.desc())
        .first()
    )

    dep_dt = existing_op.actual_departure_date_time if existing_op else None
    arr_dt = existing_op.actual_arrival_date_time   if existing_op else None

    busy_gate_ids = _get_busy_gate_ids(db, dep_dt, arr_dt)
    gates = _get_gates_for_airport(db, airport_id, terminal_type_name)

    return [(g, g.gate_id not in busy_gate_ids) for g in gates]


def get_available_for_operation(
    db: Session,
    operation_id: int,
    airport_id: int,
    terminal_type_name: str,
) -> list[tuple[Gate, bool]]:
    current_op = (
        db.query(FlightOperation)
        .filter(FlightOperation.flight_operation_id == operation_id)
        .first()
    )

    dep_dt = current_op.actual_departure_date_time if current_op else None
    arr_dt = current_op.actual_arrival_date_time   if current_op else None

    busy_gate_ids = _get_busy_gate_ids(
        db, dep_dt, arr_dt,
        exclude_operation_id=operation_id,
    )
    gates = _get_gates_for_airport(db, airport_id, terminal_type_name)

    return [(g, g.gate_id not in busy_gate_ids) for g in gates]


def get_all(
    db: Session,
    airport_id: int | None = None,
    min_capacity: int | None = None,
) -> list[Gate]:
    query = (
        db.query(Gate)
        .options(joinedload(Gate.terminal))
        .join(Gate.terminal)
    )
    if airport_id is not None:
        query = query.filter(Terminal.airport_id == airport_id)
    if min_capacity is not None:
        query = query.filter(Terminal.terminal_size >= min_capacity)
    return query.all()


def _allowed_terminal_types(route_type: str) -> list[str]:
    rt = route_type.lower()
    if rt == 'domestic':
        return ['Domestic', 'International', 'International Short-Haul', 'International Long-Haul']
    elif rt == 'international_short':
        return ['International', 'International Short-Haul']
    else:
        return ['International', 'International Long-Haul']