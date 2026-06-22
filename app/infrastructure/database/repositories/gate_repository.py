from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from app.infrastructure.database.models.gate_model import Gate
from app.infrastructure.database.models.terminal_model import Terminal, TerminalType
from app.infrastructure.database.models.flight_operation_model import FlightOperation
from app.infrastructure.database.models.flight_model import Flight
from app.infrastructure.database.models.flight_schedule_model import FlightSchedule
from app.infrastructure.database.models.route_model import Route


def get_all_for_flight(
    db: Session,
    flight_id: int,
    airport_id: int,
    terminal_type_name: str,
) -> list[tuple[Gate, bool]]:
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    schedule = getattr(flight, 'flight_schedule', None) if flight else None
    from sqlalchemy.orm import joinedload as jl
    flight = (
        db.query(Flight)
        .options(
            jl(Flight.flight_schedule)
        )
        .filter(Flight.flight_id == flight_id)
        .first()
    )
    dep_dt = getattr(flight, 'departs_datetime', None) if flight else None
    arr_dt = getattr(flight, 'arrives_datetime', None) if flight else None

    busy_gate_ids: set[int] = set()
    if dep_dt and arr_dt:
        conflicts = (
            db.query(FlightOperation.gate_id)
            .filter(
                FlightOperation.gate_id.isnot(None),
                FlightOperation.actual_departure_date_time.isnot(None),
                FlightOperation.actual_departure_date_time < arr_dt,
                or_(
                    FlightOperation.actual_arrival_date_time > dep_dt,
                    FlightOperation.actual_arrival_date_time.is_(None),
                ),
            )
            .all()
        )
        busy_gate_ids = {r.gate_id for r in conflicts if r.gate_id}

    allowed = _allowed_terminal_types(terminal_type_name)

    gates = (
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

    return [(g, g.gate_id not in busy_gate_ids) for g in gates]


def get_available_for_operation(
    db: Session,
    operation_id: int,
    airport_id: int,
    terminal_type_name: str,
) -> list[tuple[Gate, bool]]:
    current_op = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()

    busy_gate_ids: set[int] = set()
    if current_op and current_op.actual_departure_date_time:
        dep = current_op.actual_departure_date_time
        arr = current_op.actual_arrival_date_time

        conflict_query = (
            db.query(FlightOperation.gate_id)
            .filter(
                FlightOperation.flight_operation_id != operation_id,
                FlightOperation.gate_id.isnot(None),
                FlightOperation.actual_departure_date_time.isnot(None),
                FlightOperation.actual_departure_date_time < (arr or dep),
                or_(
                    FlightOperation.actual_arrival_date_time > dep,
                    FlightOperation.actual_arrival_date_time.is_(None),
                ),
            )
        )
        busy_gate_ids = {r.gate_id for r in conflict_query.all() if r.gate_id}

    allowed = _allowed_terminal_types(terminal_type_name)

    gates = (
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



