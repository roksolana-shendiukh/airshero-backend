from sqlalchemy.orm import Session

from app.infrastructure.database.repositories import reference_repository


def get_citizenships(db: Session, query: str | None = None) -> list[dict]:
    rows = reference_repository.get_citizenships(db, query)
    return [
        {"citizenship_id": r.citizenship_id, "citizenship_name": r.citizenship_name}
        for r in rows
    ]


def get_document_types(db: Session, flight_id: int | None = None) -> list[dict]:
    rows = reference_repository.get_document_types(db, flight_id)
    return [
        {
            "document_type_id":   r.document_type_id,
            "document_type_name": r.document_type_name,
            "document_type_code": r.document_type_code,
        }
        for r in rows
    ]


def get_payment_methods(db: Session) -> list[dict]:
    rows = reference_repository.get_payment_methods(db)
    return [
        {"payment_method_id": r.payment_method_id, "payment_method_name": r.payment_method_name}
        for r in rows
    ]


def get_payment_statuses(db: Session) -> list[dict]:
    rows = reference_repository.get_payment_statuses(db)
    return [
        {"payment_status_id": r.payment_status_id, "payment_status_name": r.payment_status_name}
        for r in rows
    ]


def get_sexes() -> list[dict]:
    return [{"id": 0, "name": "Female"}, {"id": 1, "name": "Male"}]


def get_all_baggage_types(db: Session) -> list[dict]:
    rows = reference_repository.get_baggage_types(db)
    return [
        {"baggage_type_id": r.baggage_type_id, "baggage_type_name": r.baggage_type_name}
        for r in rows
    ]