from sqlalchemy.orm import Session, joinedload
from app.infrastructure.database.repositories import gate_repository
from app.interfaces.schemas.gate_schema import GateDTO
from app.infrastructure.database.models.flight_model import Flight
from app.infrastructure.database.models.flight_schedule_model import FlightSchedule
from app.infrastructure.database.models.route_model import Route
from app.infrastructure.database.models.airport_model import Airport
from app.infrastructure.database.models.city_model import City


def _get_route_info(db: Session, flight_id: int) -> tuple[int | None, str]:
    flight = (
        db.query(Flight)
        .options(
            joinedload(Flight.flight_schedule)
            .joinedload(FlightSchedule.route)
            .joinedload(Route.departs_airport)
            .joinedload(Airport.city)
            .joinedload(City.country),
            joinedload(Flight.flight_schedule)
            .joinedload(FlightSchedule.route)
            .joinedload(Route.arrives_airport)
            .joinedload(Airport.city)
            .joinedload(City.country),
        )
        .filter(Flight.flight_id == flight_id)
        .first()
    )

    if not flight:
        return None, 'domestic'

    schedule    = getattr(flight, 'flight_schedule', None)
    route       = getattr(schedule, 'route', None)
    dep_airport = getattr(route, 'departs_airport', None)
    arr_airport = getattr(route, 'arrives_airport', None)
    dep_country = getattr(getattr(dep_airport, 'city', None), 'country_id', None)
    arr_country = getattr(getattr(arr_airport, 'city', None), 'country_id', None)
    airport_id  = getattr(dep_airport, 'airport_id', None)
    range_km    = float(getattr(route, 'flight_range', 0) or 0)

    print(f"[gate_service] flight_id={flight_id}, airport_id={airport_id}, dep_country={dep_country}, arr_country={arr_country}, range_km={range_km}")

    if dep_country == arr_country:
        return airport_id, 'Domestic'
    elif range_km <= 4000:
        return airport_id, 'International Short-Haul'
    else:
        return airport_id, 'International Long-Haul'


def get_gates_for_flight(db: Session, flight_id: int) -> list[GateDTO]:
    airport_id, route_type = _get_route_info(db, flight_id)
    if not airport_id:
        return []

    results = gate_repository.get_all_for_flight(
        db,
        flight_id=flight_id,
        airport_id=airport_id,
        terminal_type_name=route_type,
    )
    return [_to_dto(g, available) for g, available in results]


def get_available_gates(db: Session, operation_id: int) -> list[GateDTO]:
    from app.infrastructure.database.models.flight_operation_model import FlightOperation
    op = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()
    if not op or not op.flight_id:
        return []

    airport_id, route_type = _get_route_info(db, op.flight_id)
    if not airport_id:
        return []

    results = gate_repository.get_available_for_operation(
        db,
        operation_id=operation_id,
        airport_id=airport_id,
        terminal_type_name=route_type,
    )
    return [_to_dto(g, available) for g, available in results]


def get_all_gates(
    db: Session,
    airport_id: int | None = None,
    min_capacity: int | None = None,
) -> list[GateDTO]:
    return [
        _to_dto(g, True)
        for g in gate_repository.get_all(
            db, airport_id=airport_id, min_capacity=min_capacity)
    ]


def _to_dto(g, is_available: bool = True) -> GateDTO:
    return GateDTO(
        gateId=g.gate_id,
        gateCode=g.gate_code,
        terminalId=g.terminal_id,
        terminalCode=getattr(g.terminal, 'terminal_code', None),
        terminalSize=float(getattr(g.terminal, 'terminal_size', None) or 0) or None,
        terminalType=getattr(
            getattr(g.terminal, 'terminal_type', None),
            'terminal_type_name', None),
        isAvailable=is_available,
    )