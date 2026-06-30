from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.infrastructure.database.models.crew_model import (
    FlightCrew, FlightCrewFlightOperation,
    FlightCrewPosition, FlightCrewLicenseType
)
from app.infrastructure.database.models.airfleet_model import AirfleetFlightCrew
from app.infrastructure.database.models.airline_model import AirlineAirfleet
from app.infrastructure.database.models.flight_operation_model import (
    FlightOperation, FlightOperationStatus, ScheduledFlight
)
from app.infrastructure.database.models.flight_model import Flight, Route
from app.infrastructure.database.models.airport_model import Airport


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
        .join(Flight, Flight.route_id == Route.route_id)
        .join(ScheduledFlight, ScheduledFlight.flight_id == Flight.flight_id)
        .join(FlightOperation, 
              FlightOperation.schedule_flight_id == ScheduledFlight.schedule_flight_id)
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
    position: str | None = 'Pilot',
) -> list[tuple[FlightCrew, bool]]:
    
    departs_airport_id: int | None = None
    current_op = (
        db.query(FlightOperation)
        .filter(FlightOperation.flight_operation_id == operation_id)
        .first()
    )
    if current_op:
        row = (
            db.query(Route.departs_airport_id)
            .join(Flight, Flight.route_id == Route.route_id)
            .join(ScheduledFlight, ScheduledFlight.flight_id == Flight.flight_id)
            .filter(ScheduledFlight.schedule_flight_id == current_op.schedule_flight_id)
            .first()
        )
        if row:
            departs_airport_id = row[0]

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
    busy_ids = {
        r.flight_crew_id
        for r in db.query(FlightCrewFlightOperation.flight_crew_id)
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
    }

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

    if position:
        query = query.join(
            FlightCrewPosition,
            FlightCrewPosition.flight_crew_position_id == FlightCrew.flight_crew_position_id
        ).filter(FlightCrewPosition.flight_crew_position_name == position)

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
    db.commit()
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
    db.commit()
    return True


def get_all_crew(
    db: Session,
    search: str | None = None,
    position: str | None = None,
) -> list[FlightCrew]:
    query = db.query(FlightCrew).options(
        joinedload(FlightCrew.position),
        joinedload(FlightCrew.license_type),
    )
    if search:
        p = f"%{search.strip()}%"
        query = query.filter(or_(
            FlightCrew.flight_crew_first_name.ilike(p),
            FlightCrew.flight_crew_last_name.ilike(p),
        ))
    if position:
        query = query.join(FlightCrewPosition).filter(
            FlightCrewPosition.flight_crew_position_name == position
        )
    return query.order_by(FlightCrew.flight_crew_last_name).all()


def get_crew_by_id(db: Session, crew_id: int) -> FlightCrew | None:
    return (
        db.query(FlightCrew)
        .options(
            joinedload(FlightCrew.position),
            joinedload(FlightCrew.license_type),
        )
        .filter(FlightCrew.flight_crew_id == crew_id)
        .first()
    )


def create_crew(
    db: Session,
    first_name: str,
    last_name: str,
    position_id: int,
    license_type_id: int,
    experience_years: int,
) -> FlightCrew:
    crew = FlightCrew(
        flight_crew_first_name       = first_name,
        flight_crew_last_name        = last_name,
        flight_crew_position_id      = position_id,
        flight_crew_license_type     = license_type_id,
        flight_crew_experience_years = experience_years,
    )
    db.add(crew)
    db.commit()
    return crew


def update_crew(
    db: Session,
    crew: FlightCrew,
    first_name: str | None,
    last_name: str | None,
    position_id: int | None,
    license_type_id: int | None,
    experience_years: int | None,
) -> FlightCrew:
    if first_name       is not None: crew.flight_crew_first_name       = first_name
    if last_name        is not None: crew.flight_crew_last_name        = last_name
    if position_id      is not None: crew.flight_crew_position_id      = position_id
    if license_type_id  is not None: crew.flight_crew_license_type     = license_type_id
    if experience_years is not None: crew.flight_crew_experience_years = experience_years
    db.commit()
    return crew


def delete_crew(db: Session, crew: FlightCrew) -> None:
    db.delete(crew)
    db.commit()


def get_positions(db: Session):
    return db.query(FlightCrewPosition).all()


def get_license_types(db: Session):
    from app.infrastructure.database.models.crew_model import FlightCrewLicenseType
    return db.query(FlightCrewLicenseType).all()


def crew_to_dto(c: FlightCrew) -> dict:
    return {
        "flightCrewId":    c.flight_crew_id,
        "firstName":       c.flight_crew_first_name,
        "lastName":        c.flight_crew_last_name,
        "position":        c.position.flight_crew_position_name         if c.position     else None,
        "positionId":      c.flight_crew_position_id,
        "licenseType":     c.license_type.flight_crew_license_type_name if c.license_type else None,
        "licenseTypeId":   c.flight_crew_license_type,
        "experienceYears": c.flight_crew_experience_years,
    }


def get_operation(db: Session, operation_id: int):
    from app.infrastructure.database.models.flight_operation_model import FlightOperation
    return db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()

def get_position_by_id(db: Session, position_id: int):
    return db.query(FlightCrewPosition).filter(
        FlightCrewPosition.flight_crew_position_id == position_id
    ).first()

def get_license_type_by_id(db: Session, license_type_id: int):
    return db.query(FlightCrewLicenseType).filter(
        FlightCrewLicenseType.flight_crew_license_type_id == license_type_id
    ).first()
