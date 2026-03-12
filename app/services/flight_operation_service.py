from sqlalchemy.orm import Session
from app.models.flight_operation_model import FlightOperation
from app.repositories import flight_operation_repository
from app.schemas.flight_operation_schema import (
    FlightOperationCreateDTO,
    FlightOperationUpdateDTO,
    FlightOperationDTO,
)


def _map(op: FlightOperation) -> FlightOperationDTO:
    flight   = op.flight
    schedule = getattr(flight, 'flight_schedule', None)
    route    = getattr(schedule, 'route', None)
    dep      = getattr(route, 'departs_airport', None)
    arr      = getattr(route, 'arrives_airport', None)

    return FlightOperationDTO(
        flightOperationId=op.flight_operation_id,
        flightId=op.flight_id,
        flightNumber=getattr(route, 'flight_number', None),
        departsCode=getattr(dep, 'airport_code', None),
        arrivesCode=getattr(arr, 'airport_code', None),
        departsDatetime=getattr(flight, 'departs_datetime', None),
        arrivesDdatetime=getattr(flight, 'arrives_datetime', None),
        statusId=op.flight_operation_status_id,
        statusName=getattr(op.status, 'flight_operation_status_name', None),
        airfleetId=op.airfleet_id,
        aircraftModel=getattr(op.airfleet, 'aircraft_model', None),
        gateId=op.gate_id,
        gateCode=getattr(op.gate, 'gate_code', None),
        actualDepartureDatetime=op.actual_departure_date_time,
        actualArrivalDatetime=op.actual_arrival_date_time,
        boardingStartTime=op.boarding_start_time,
        boardingEndTime=op.boarding_end_time,
        baggageLoadingStartTime=op.baggage_loading_start_time,
        baggageLoadingEndTime=op.baggage_loading_end_time,
    )


def get_all(db: Session) -> list[FlightOperationDTO]:
    return [_map(op) for op in flight_operation_repository.get_all(db)]


def get_by_id(db: Session, operation_id: int) -> FlightOperationDTO | None:
    op = flight_operation_repository.get_by_id(db, operation_id)
    return _map(op) if op else None


def create(db: Session, data: FlightOperationCreateDTO) -> FlightOperationDTO:
    op = flight_operation_repository.create(db, data)
    db.commit()
    return _map(flight_operation_repository.get_by_id(db, op.flight_operation_id))


def update(db: Session, operation_id: int, data: FlightOperationUpdateDTO) -> FlightOperationDTO | None:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return None
    flight_operation_repository.update(db, op, data)
    db.commit()
    return _map(flight_operation_repository.get_by_id(db, operation_id))


def delete(db: Session, operation_id: int) -> bool:
    op = flight_operation_repository.get_by_id(db, operation_id)
    if not op:
        return False
    flight_operation_repository.delete(db, op)
    db.commit()
    return True