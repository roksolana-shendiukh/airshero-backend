from sqlalchemy.orm import Session
from app.models.passenger_model import Passenger, PassengerDocument
from app.models.passenger import (
    PassengerDTO,
    PassengerDocumentDTO,
    PassengerCreateDTO,
    PassengerUpdateDTO,
)

import logging

logger = logging.getLogger(__name__)

def _build_doc_dto(d) -> PassengerDocumentDTO:
    return PassengerDocumentDTO(
        document_id=d.passenger_document_id,
        citizenship_id=d.citizenship_id,
        citizenship_name=getattr(d.citizenship, "citizenship_name", None),
        document_type_id=d.document_type_id,
        document_type_name=getattr(d.document_type, "document_type_name", None),
        document_number=d.document_number,
        document_date_of_issue=d.document_date_of_issue,
        document_date_of_expire=d.document_date_of_expire,
    )


def _build_passenger_dto(p) -> PassengerDTO | None:
    if not p.documents:
        return None
    return PassengerDTO(
        passenger_id=p.passenger_id,
        first_name=p.passenger_first_name,
        last_name=p.passenger_last_name,
        sex=p.passenger_sex,
        email=p.passenger_email,
        date_of_birth=p.passenger_date_of_birth,
        documents=[_build_doc_dto(d) for d in p.documents],
    )


def get_all_passengers(db: Session, skip: int = 0, limit: int = 50):
    passengers = db.query(Passenger).offset(skip).limit(limit).all()
    return [dto for p in passengers if (dto := _build_passenger_dto(p))]


def get_passenger_by_id(db: Session, passenger_id: int) -> PassengerDTO | None:
    passenger = (
        db.query(Passenger)
        .filter_by(passenger_id=passenger_id)
        .join(PassengerDocument)
        .first()
    )
    if not passenger:
        return None
    return _build_passenger_dto(passenger)


def get_passenger_by_document_number(db: Session, document_number: str) -> PassengerDTO | None:
    doc = db.query(PassengerDocument).filter(
        PassengerDocument.document_number == document_number
    ).first()
    if not doc:
        return None
    passenger = doc.passenger
    return _build_passenger_dto(passenger)

def search_documents_partial(db: Session, query: str, limit: int = 10) -> list[dict]:
    if not query:
        return []

    passengers = (
        db.query(Passenger)
        .join(Passenger.documents)
        .filter(PassengerDocument.document_number.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )

    result = []
    for p in passengers:
        for doc in p.documents:
            if query.lower() in doc.document_number.lower():
                result.append({
                    "passenger_id": p.passenger_id,
                    "first_name": p.passenger_first_name,
                    "last_name": p.passenger_last_name,
                    "document_number": doc.document_number,
                    "document_type_name": getattr(doc.document_type, "document_type_name", None),
                    "citizenship_name": getattr(doc.citizenship, "citizenship_name", None),
                    "document_date_of_issue": doc.document_date_of_issue,
                    "document_date_of_expire": doc.document_date_of_expire,
                })
    return result

def search_passengers_partial(db: Session, query: str, limit: int = 10) -> list[PassengerDTO]:
    passengers = (
        db.query(Passenger)
        .join(Passenger.documents)
        .filter(
            (Passenger.passenger_first_name.ilike(f"%{query}%"))
            | (Passenger.passenger_last_name.ilike(f"%{query}%"))
            | (PassengerDocument.document_number.ilike(f"%{query}%"))
        )
        .limit(limit)
        .all()
    )
    return [dto for p in passengers if (dto := _build_passenger_dto(p))]

def create_passenger(db: Session, data: PassengerCreateDTO) -> int:
    passenger = Passenger(
        passenger_first_name=data.first_name,
        passenger_last_name=data.last_name,
        passenger_sex=data.sex,
        passenger_email=data.email,
        passenger_date_of_birth=data.date_of_birth,
    )
    db.add(passenger)
    db.flush()

    document = PassengerDocument(
        passenger_id=passenger.passenger_id,
        document_number=data.document_number,
        document_type_id=data.document_type_id,
        citizenship_id=data.citizenship_id,
        document_date_of_issue=data.document_date_of_issue,
        document_date_of_expire=data.document_date_of_expire,
    )
    db.add(document)
    db.commit()
    return passenger.passenger_id

def get_document_by_number(db: Session, document_number: str):
    return db.query(PassengerDocument).filter(
        PassengerDocument.document_number == document_number
    ).first()

def update_passenger(db: Session, passenger_id: int, data: PassengerUpdateDTO):
    passenger = db.query(Passenger).filter(Passenger.passenger_id == passenger_id).first()
    if not passenger:
        return None

    if data.first_name: passenger.passenger_first_name = data.first_name
    if data.last_name: passenger.passenger_last_name = data.last_name
    
    if data.sex is not None:
        passenger.passenger_sex = data.sex 

def delete_passenger(db: Session, passenger_id: int) -> bool:
    passenger = db.query(Passenger).filter_by(passenger_id=passenger_id).first()
    if not passenger:
        return False
    db.delete(passenger)
    db.commit()
    return True


