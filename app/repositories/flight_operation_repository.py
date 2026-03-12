from sqlalchemy.orm import Session, joinedload
from app.models.flight_operation_model import FlightOperation
from app.schemas.flight_operation_schema import FlightOperationCreateDTO, FlightOperationUpdateDTO


def get_all(db: Session) -> list[FlightOperation]:
    return (
        db.query(FlightOperation)
        .options(
            joinedload(FlightOperation.flight),
            joinedload(FlightOperation.status),
            joinedload(FlightOperation.airfleet),
            joinedload(FlightOperation.gate),
        )
        .all()
    )


def get_by_id(db: Session, operation_id: int) -> FlightOperation | None:
    return (
        db.query(FlightOperation)
        .options(
            joinedload(FlightOperation.flight),
            joinedload(FlightOperation.status),
            joinedload(FlightOperation.airfleet),
            joinedload(FlightOperation.gate),
        )
        .filter(FlightOperation.flight_operation_id == operation_id)
        .first()
    )


def create(db: Session, data: FlightOperationCreateDTO) -> FlightOperation:
    op = FlightOperation(**data.model_dump())
    db.add(op)
    db.flush()
    return op


def update(db: Session, op: FlightOperation, data: FlightOperationUpdateDTO) -> FlightOperation:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(op, field, value)
    db.flush()
    return op


def delete(db: Session, op: FlightOperation) -> None:
    db.delete(op)
    db.flush()