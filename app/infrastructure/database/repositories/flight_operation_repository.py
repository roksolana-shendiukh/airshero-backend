from sqlalchemy.orm import Session, joinedload
from app.infrastructure.database.models.flight_operation_model import FlightOperation, FlightOperationStatus
from app.interfaces.schemas.flight_operation_schema import FlightOperationCreateDTO, FlightOperationUpdateDTO
from sqlalchemy import text


def _get_waiting_status_id(db: Session) -> int:
    status = db.query(FlightOperationStatus)\
        .filter(FlightOperationStatus.flight_operation_status_name == "Waiting")\
        .first()
    if not status:
        raise ValueError("FlightOperationStatus 'Waiting' not found")
    return status.flight_operation_status_id


def _with_relations(query):
    return query.options(
        joinedload(FlightOperation.flight),
        joinedload(FlightOperation.status),
        joinedload(FlightOperation.airfleet),
        joinedload(FlightOperation.gate),
        joinedload(FlightOperation.state), 
    )


def get_all(db: Session) -> list[FlightOperation]:
    return _with_relations(db.query(FlightOperation)).all()


def get_by_id(db: Session, operation_id: int) -> FlightOperation | None:
    return _with_relations(db.query(FlightOperation))\
        .filter(FlightOperation.flight_operation_id == operation_id)\
        .first()


def create(db: Session, data: FlightOperationCreateDTO) -> FlightOperation:
    waiting_status_id = _get_waiting_status_id(db)
 
    db.execute(text("""
        INSERT INTO FlightOperation
            (flight_id, flight_operation_status_id, airfleet_id, gate_id)
        VALUES
            (:flight_id, :status_id, :airfleet_id, :gate_id)
    """), {
        "flight_id":   data.flight_id,
        "status_id":   waiting_status_id,
        "airfleet_id": data.airfleet_id,
        "gate_id":     data.gate_id,
    })
 
    op = _with_relations(db.query(FlightOperation))\
        .filter(FlightOperation.flight_id == data.flight_id)\
        .order_by(FlightOperation.flight_operation_id.desc())\
        .first()
 
    return op
 

def update(db: Session, op: FlightOperation, data: FlightOperationUpdateDTO) -> FlightOperation:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(op, field, value)
    db.flush()
    return op


def delete(db: Session, op: FlightOperation) -> None:
    db.delete(op)
    db.flush()