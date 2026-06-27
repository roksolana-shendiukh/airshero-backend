from sqlalchemy.orm import Session, joinedload
from app.infrastructure.database.models.flight_operation_model import (
    FlightOperation, FlightOperationStatus
)
from app.interfaces.schemas.flight_operation_schema import (
    FlightOperationCreateDTO, FlightOperationUpdateDTO
)


def _get_waiting_status_id(db: Session) -> int:
    status = (
        db.query(FlightOperationStatus)
        .filter(FlightOperationStatus.flight_operation_status_name == "Waiting")
        .first()
    )
    if not status:
        raise ValueError("FlightOperationStatus 'Waiting' not found")
    return status.flight_operation_status_id


def _with_relations(query):
    return query.options(
        joinedload(FlightOperation.schedule_flight),      
        joinedload(FlightOperation.flight_operation_status),  
        joinedload(FlightOperation.flight_operation_state),   
        joinedload(FlightOperation.airfleet),
        joinedload(FlightOperation.gate),
    )


def get_all(db: Session) -> list[FlightOperation]:
    return _with_relations(db.query(FlightOperation)).all()


def get_by_id(db: Session, operation_id: int) -> FlightOperation | None:
    return (
        _with_relations(db.query(FlightOperation))
        .filter(FlightOperation.flight_operation_id == operation_id)
        .first()
    )


def create(db: Session, data: FlightOperationCreateDTO) -> FlightOperation:
    waiting_status_id = _get_waiting_status_id(db)

    op = FlightOperation(
        schedule_flight_id=data.schedule_flight_id,
        flight_operation_status_id=waiting_status_id,
        airfleet_id=data.airfleet_id,
        gate_id=data.gate_id,
    )
    db.add(op)
    db.commit()  

    db.refresh(op)
    return get_by_id(db, op.flight_operation_id)


def update(db: Session, op: FlightOperation, data: FlightOperationUpdateDTO) -> FlightOperation:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(op, field, value)
    db.commit()
    return op


def delete(db: Session, op: FlightOperation) -> None:
    db.delete(op)
    db.commit()

def get_statuses(db: Session) -> list[dict]:
    from app.infrastructure.database.models.flight_operation_model import FlightOperationStatus
    statuses = db.query(FlightOperationStatus).all()
    return [
        {
            "flight_operation_status_id":   s.flight_operation_status_id,
            "flight_operation_status_name": s.flight_operation_status_name,
        }
        for s in statuses
    ]

def get_states(db: Session) -> list[dict]:
    from app.infrastructure.database.models.flight_operation_model import FlightOperationState
    states = db.query(FlightOperationState).all()
    return [
        {
            "state_id":    s.flight_operation_state_id,
            "description": s.flight_operation_state_description,
        }
        for s in states
    ]

def get_status_by_name(db: Session, name: str):
    from app.infrastructure.database.models.flight_operation_model import FlightOperationStatus
    return db.query(FlightOperationStatus).filter(
        FlightOperationStatus.flight_operation_status_name == name
    ).first()

def get_flight_for_operation(db: Session, flight_id: int):
    from app.infrastructure.database.models.flight_model import Flight
    return db.query(Flight).filter(Flight.flight_id == flight_id).first()

def create_custom_state(db: Session, custom_reason: str) -> int:
    from app.infrastructure.database.models.flight_operation_model import FlightOperationState
    new_state = FlightOperationState(
        flight_operation_state_description=custom_reason
    )
    db.add(new_state)
    db.flush()
    return new_state.flight_operation_state_id
