from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from app.models.flight_crew_model import (
    FlightCrew, AirfleetFlightCrew, FlightCrewFlightOperation
)
from app.models.airline_airfleet_model import AirlineAirfleet
from app.models.flight_operation_model import FlightOperation, FlightOperationStatus
from app.models.flight_model import Flight
from app.models.flight_schedule_model import FlightSchedule
from app.models.route_model import Route
from app.models.airport_model import Airport


def get_crew_for_operation(db: Session, operation_id: int) -> list[FlightCrew]:
    rows = (
        db.query(FlightCrewFlightOperation)
        .options(
            joinedload(FlightCrewFlightOperation.crew)
            .joinedload(FlightCrew.position),
            joinedload(FlightCrewFlightOperation.crew)
            .joinedload(FlightCrew.license_type),
        )
        .filter(FlightCrewFlightOperation.flight_operation_id == operation_id)
        .all()
    )
    return [r.crew for r in rows]


def _get_crew_current_airport(db: Session, crew_id: int) -> int | None:
    result = (
        db.query(Airport.airport_id)
        .join(Route, Route.arrives_airport_id == Airport.airport_id)
        .join(FlightSchedule, FlightSchedule.route_id == Route.route_id)
        .join(Flight, Flight.flight_schedule_id == FlightSchedule.flight_schedule_id)
        .join(FlightOperation, FlightOperation.flight_id == Flight.flight_id)
        .join(FlightCrewFlightOperation,
              FlightCrewFlightOperation.flight_operation_id == FlightOperation.flight_operation_id)
        .join(FlightOperationStatus,
              FlightOperationStatus.flight_operation_status_id == FlightOperation.flight_operation_status_id)
        .filter(
            FlightCrewFlightOperation.flight_crew_id == crew_id,
            FlightOperationStatus.flight_operation_status_name == 'Completed',
            FlightOperation.actual_arrival_date_time.isnot(None),
        )
        .order_by(FlightOperation.actual_arrival_date_time.desc())
        .first()
    )
    return result[0] if result else None


def get_available_crew(
    db: Session,
    operation_id: int,
    airfleet_id: int,
    airline_id: int,
    search: str | None = None,
) -> list[tuple[FlightCrew, bool]]:
    current_op = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()

    departs_airport_id: int | None = None
    if current_op:
        flight = (
            db.query(Flight)
            .options(
                joinedload(Flight.flight_schedule)
                .joinedload(FlightSchedule.route)
            )
            .filter(Flight.flight_id == current_op.flight_id)
            .first()
        )
        if flight:
            schedule           = getattr(flight, 'flight_schedule', None)
            route              = getattr(schedule, 'route', None)
            departs_airport_id = getattr(route, 'departs_airport_id', None)

    assigned_ids = {
        r.flight_crew_id
        for r in db.query(FlightCrewFlightOperation.flight_crew_id)
        .filter(FlightCrewFlightOperation.flight_operation_id == operation_id)
        .all()
    }

    certified_ids = {
        r.flight_crew_id
        for r in db.query(AirfleetFlightCrew.flight_crew_id)
        .join(AirlineAirfleet,
              AirlineAirfleet.airfleet_id == AirfleetFlightCrew.airfleet_id)
        .filter(
            AirfleetFlightCrew.airfleet_id == airfleet_id,
            AirlineAirfleet.airline_id == airline_id,
        )
        .all()
    }

    if not certified_ids:
        return []

    active_statuses = {'Waiting', 'Boarding', 'Baggage Loading', 'Departed', 'Arrived'}
    conflicts = (
        db.query(FlightCrewFlightOperation.flight_crew_id)
        .join(FlightOperation,
              FlightOperation.flight_operation_id ==
              FlightCrewFlightOperation.flight_operation_id)
        .join(FlightOperationStatus,
              FlightOperationStatus.flight_operation_status_id ==
              FlightOperation.flight_operation_status_id)
        .filter(
            FlightCrewFlightOperation.flight_operation_id != operation_id,
            FlightOperationStatus.flight_operation_status_name.in_(active_statuses),
        )
        .all()
    )
    busy_ids = {r.flight_crew_id for r in conflicts}

    available_ids = certified_ids - assigned_ids - busy_ids
    if not available_ids:
        return []

    query = (
        db.query(FlightCrew)
        .options(
            joinedload(FlightCrew.position),
            joinedload(FlightCrew.license_type),
        )
        .filter(FlightCrew.flight_crew_id.in_(available_ids))
    )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                FlightCrew.flight_crew_first_name.ilike(pattern),
                FlightCrew.flight_crew_last_name.ilike(pattern),
            )
        )

    crew_list = query.all()

    result: list[tuple[FlightCrew, bool]] = []
    for c in crew_list:
        current_airport = _get_crew_current_airport(db, c.flight_crew_id)
        if current_airport is None:
            result.append((c, False))
        elif departs_airport_id and current_airport != departs_airport_id:
            continue
        else:
            result.append((c, True))

    return result

def assign_crew_member(
    db: Session, operation_id: int, crew_id: int
) -> FlightCrewFlightOperation:
    row = FlightCrewFlightOperation(
        flight_operation_id=operation_id,
        flight_crew_id=crew_id,
    )
    db.add(row)
    db.flush()
    return row


def remove_crew_member(
    db: Session, operation_id: int, crew_id: int
) -> bool:
    row = (
        db.query(FlightCrewFlightOperation)
        .filter(
            FlightCrewFlightOperation.flight_operation_id == operation_id,
            FlightCrewFlightOperation.flight_crew_id == crew_id,
        )
        .first()
    )
    if not row:
        return False
    db.delete(row)
    db.flush()
    return True