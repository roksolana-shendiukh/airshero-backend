from sqlalchemy.orm import Session, joinedload
from app.models.flight_crew_model import (
    FlightCrew, AirfleetFlightCrew, FlightCrewFlightOperation, FlightCrewPosition
)
from app.models.flight_operation_model import FlightOperation
from app.repositories import flight_crew_repository

from app.models.flight_model import Flight
from app.models.flight_schedule_model import FlightSchedule
from app.models.route_model import Route
from app.models.airport_model import Airport
from app.models.city_model import City

PILOT_POSITION            = "Pilot"
CO_PILOT_POSITION         = "Co-Pilot"
FLIGHT_ATTENDANT_POSITION = "Flight Attendant"
ENGINEER_POSITION         = "Engineer"


def _crew_dto(crew: FlightCrew) -> dict:
    return {
        "flightCrewId":    crew.flight_crew_id,
        "firstName":       crew.flight_crew_first_name,
        "lastName":        crew.flight_crew_last_name,
        "position":        getattr(crew.position, "flight_crew_position_name", None),
        "licenseType":     getattr(crew.license_type, "flight_crew_license_type_name", None),
        "experienceYears": crew.flight_crew_experience_years,
    }



def _get_operation_with_relations(db: Session, operation_id: int) -> FlightOperation | None:
    return (
        db.query(FlightOperation)
        .options(
            joinedload(FlightOperation.flight)
            .joinedload(Flight.flight_schedule)
            .joinedload(FlightSchedule.route)
            .joinedload(Route.departs_airport)
            .joinedload(Airport.city)
            .joinedload(City.country),
            joinedload(FlightOperation.flight)
            .joinedload(Flight.flight_schedule)
            .joinedload(FlightSchedule.route)
            .joinedload(Route.arrives_airport)
            .joinedload(Airport.city)
            .joinedload(City.country),
            joinedload(FlightOperation.airfleet),
        )
        .filter(FlightOperation.flight_operation_id == operation_id)
        .first()
    )


def _get_required_positions(op: FlightOperation, db: Session) -> dict:
    flight    = op.flight
    schedule  = getattr(flight, "flight_schedule", None)
    route     = getattr(schedule, "route", None)

    flight_range  = float(getattr(route, "flight_range", 0) or 0)
    airfleet      = op.airfleet
    seat_capacity = getattr(airfleet, "seat_capacity", 0) or 0

    dep_airport = getattr(route, "departs_airport", None)
    arr_airport = getattr(route, "arrives_airport", None)
    dep_country = getattr(getattr(dep_airport, "city", None), "country_id", None)
    arr_country = getattr(getattr(arr_airport, "city", None), "country_id", None)

    is_international = dep_country != arr_country

    required = {}

    # Пілоти
    if is_international or flight_range > 500:
        required[PILOT_POSITION]    = 1
        required[CO_PILOT_POSITION] = 1
    else:
        required[PILOT_POSITION] = 1

    # Бортпровідники
    attendants = seat_capacity // 50
    if attendants > 0:
        required[FLIGHT_ATTENDANT_POSITION] = attendants

    return required


def _has_certified_engineers(db: Session, airfleet_id: int) -> bool:
    result = (
        db.query(AirfleetFlightCrew)
        .join(FlightCrew,
              FlightCrew.flight_crew_id == AirfleetFlightCrew.flight_crew_id)
        .join(FlightCrewPosition,
              FlightCrewPosition.flight_crew_position_id == FlightCrew.flight_crew_position_id)
        .filter(
            AirfleetFlightCrew.airfleet_id == airfleet_id,
            FlightCrewPosition.flight_crew_position_name == ENGINEER_POSITION,
        )
        .first()
    )
    return result is not None


def get_crew(db: Session, operation_id: int) -> list[dict]:
    crew = flight_crew_repository.get_crew_for_operation(db, operation_id)
    return [_crew_dto(c) for c in crew]


def get_available_crew(
    db: Session,
    operation_id: int,
    airline_id: int,
    search: str | None = None,
) -> list[dict]:
    op = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()
    if not op or not op.airfleet_id:
        return []

    results = flight_crew_repository.get_available_crew(
        db, operation_id, op.airfleet_id, airline_id, search=search
    )

    return [
        {
            **_crew_dto(c),
            "locationKnown": location_known,
        }
        for c, location_known in results
    ]

def get_required_positions(db: Session, operation_id: int) -> dict:
    op = _get_operation_with_relations(db, operation_id)
    if not op:
        return {}
    return _get_required_positions(op, db)


def validate_crew(db: Session, operation_id: int) -> dict:
    op = _get_operation_with_relations(db, operation_id)
    if not op:
        return {"valid": False, "missing": {}, "warnings": []}

    required = _get_required_positions(op, db)
    current  = flight_crew_repository.get_crew_for_operation(db, operation_id)

    current_counts: dict[str, int] = {}
    for c in current:
        pos = getattr(c.position, "flight_crew_position_name", None)
        if pos:
            current_counts[pos] = current_counts.get(pos, 0) + 1

    missing = {
        pos: needed - current_counts.get(pos, 0)
        for pos, needed in required.items()
        if current_counts.get(pos, 0) < needed
    }

    warnings = []
    if op.airfleet_id and _has_certified_engineers(db, op.airfleet_id):
        has_engineer = current_counts.get(ENGINEER_POSITION, 0) > 0
        if not has_engineer:
            warnings.append(
                "This aircraft type supports engineers — consider assigning one"
            )

    return {
        "valid":    len(missing) == 0,
        "missing":  missing,
        "warnings": warnings,
        "required": required,
    }


def assign_crew(db: Session, operation_id: int, crew_id: int, airline_id: int) -> dict:
    existing = flight_crew_repository.get_crew_for_operation(db, operation_id)
    if any(c.flight_crew_id == crew_id for c in existing):
        raise ValueError("Crew member already assigned to this operation")

    op = db.query(FlightOperation).filter(
        FlightOperation.flight_operation_id == operation_id
    ).first()
    if not op:
        raise ValueError("Operation not found")

    available = flight_crew_repository.get_available_crew(
        db, operation_id, op.airfleet_id, airline_id
    )
    if not any(c.flight_crew_id == crew_id for c, _ in available):
        raise ValueError(
            "Crew member is not certified for this aircraft, "
            "does not belong to this airline, or has a schedule conflict"
        )

    new_member = next((c for c, _ in available if c.flight_crew_id == crew_id), None)
    if new_member:
        new_pos = getattr(new_member.position, "flight_crew_position_name", None)
        if new_pos:
            current_counts: dict[str, int] = {}
            for c in existing:
                pos = getattr(c.position, "flight_crew_position_name", None)
                if pos:
                    current_counts[pos] = current_counts.get(pos, 0) + 1

            op_with_rel = _get_operation_with_relations(db, operation_id)
            required    = _get_required_positions(op_with_rel, db) if op_with_rel else {}

            current_count = current_counts.get(new_pos, 0)

            if new_pos == PILOT_POSITION and current_count >= 1:
                raise ValueError("Only 1 Pilot allowed per operation")
            elif new_pos == CO_PILOT_POSITION and current_count >= 1:
                raise ValueError("Only 1 Co-Pilot allowed per operation")
            elif new_pos == ENGINEER_POSITION and current_count >= 1:
                raise ValueError("Only 1 Engineer allowed per operation")
            elif new_pos == FLIGHT_ATTENDANT_POSITION:
                max_attendants = required.get(FLIGHT_ATTENDANT_POSITION, 0) + 1
                if current_count >= max_attendants:
                    raise ValueError(
                        f"Maximum Flight Attendants reached "
                        f"({required.get(FLIGHT_ATTENDANT_POSITION, 0)} required, +1 allowed)"
                    )

    flight_crew_repository.assign_crew_member(db, operation_id, crew_id)
    db.commit()
    return {"ok": True}

def remove_crew(db: Session, operation_id: int, crew_id: int) -> bool:
    result = flight_crew_repository.remove_crew_member(db, operation_id, crew_id)
    if result:
        db.commit()
    return result