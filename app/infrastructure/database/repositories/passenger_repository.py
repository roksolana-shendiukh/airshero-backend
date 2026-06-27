from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text
from app.infrastructure.database.models.passenger_model import Passenger
from app.infrastructure.database.models.passenger_model import PassengerDocument
from app.interfaces.schemas.passenger_schema import PassengerCreateDTO, PassengerUpdateDTO


def get_document_type_code(db: Session, document_type_id: int) -> str | None:
    row = db.execute(
        text("SELECT document_type_code FROM DocumentType WHERE document_type_id = :id"),
        {"id": document_type_id},
    ).fetchone()
    return row[0] if row else None

def get_by_id(db: Session, passenger_id: int) -> Passenger | None:
    return (
        db.query(Passenger)
        .options(joinedload(Passenger.documents))
        .filter(Passenger.passenger_id == passenger_id)
        .first()
    )


def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[Passenger]:
    return (
        db.query(Passenger)
        .options(joinedload(Passenger.documents))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_document_number(db: Session, document_number: str) -> Passenger | None:
    doc = (
        db.query(PassengerDocument)
        .options(joinedload(PassengerDocument.passenger))
        .filter(PassengerDocument.document_number == document_number)
        .first()
    )
    return doc.passenger if doc else None


def get_document_by_number(db: Session, document_number: str) -> PassengerDocument | None:
    return (
        db.query(PassengerDocument)
        .filter(PassengerDocument.document_number == document_number)
        .first()
    )


def search_partial(db: Session, query: str, limit: int = 10) -> list[Passenger]:
    # ✅ outerjoin щоб пасажири без документів теж потрапляли в результат
    return (
        db.query(Passenger)
        .options(joinedload(Passenger.documents))
        .outerjoin(Passenger.documents)
        .filter(
            or_(
                Passenger.passenger_first_name.ilike(f"%{query}%"),
                Passenger.passenger_last_name.ilike(f"%{query}%"),
                PassengerDocument.document_number.ilike(f"%{query}%"),
            )
        )
        .distinct()  # outerjoin може дати дублікати
        .limit(limit)
        .all()
    )


def search_documents_partial(
    db: Session, query: str, limit: int = 10
) -> list[PassengerDocument]:
    return (
        db.query(PassengerDocument)
        .options(
            joinedload(PassengerDocument.passenger),
            joinedload(PassengerDocument.citizenship),
            joinedload(PassengerDocument.document_type),
        )
        .filter(PassengerDocument.document_number.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )


def create(db: Session, data: PassengerCreateDTO) -> Passenger:
    passenger = Passenger(
        passenger_first_name    = data.first_name,
        passenger_last_name     = data.last_name,
        passenger_sex           = data.sex,
        passenger_email         = data.email,
        passenger_date_of_birth = data.date_of_birth,
    )
    db.add(passenger)
    db.commit()

    document = PassengerDocument(
        passenger_id              = passenger.passenger_id,
        document_number           = data.document_number,
        document_type_id          = data.document_type_id,
        citizenship_id            = data.citizenship_id,
        document_date_of_issue    = data.document_date_of_issue,
        document_date_of_expire   = data.document_date_of_expire,
    )
    db.add(document)
    db.commit()
    return passenger


def update(db: Session, passenger: Passenger, data: PassengerUpdateDTO) -> Passenger:
    if data.first_name is not None:
        passenger.passenger_first_name = data.first_name
    if data.last_name is not None:
        passenger.passenger_last_name = data.last_name
    if data.sex is not None:
        passenger.passenger_sex = data.sex  
    if data.email is not None:
        passenger.passenger_email = data.email
    db.commit()  
    return passenger



def delete(db: Session, passenger: Passenger) -> None:
    db.delete(passenger)
    db.flush()  