import re
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.passenger_model import Passenger
from app.models.document_model import PassengerDocument
from app.schemas.passenger_schema import PassengerDTO, PassengerCreateDTO, PassengerUpdateDTO
from app.schemas.document_schema import PassengerDocumentDTO
from app.repositories import passenger_repository
from dateutil.relativedelta import relativedelta


DOC_FORMATS = {
    'PAS': r'^[A-Z]{2}\d{7}$',
    'INT': r'^[A-Z]{2}\d{7}$',
    'OFF': r'^[A-Z]{1}\d{7}$',
    'ID':  r'^\d{9}$',
}

DOC_FORMAT_LABELS = {
    'PAS': 'AB1234567 (2 letters + 7 digits)',
    'INT': 'AB1234567 (2 letters + 7 digits)',
    'OFF': 'A1234567 (1 letter + 7 digits)',
    'ID':  '123456789 (9 digits)',
}


# ── Mappers ───────────────────────────────────────────────────────────────────

def _map_document(d: PassengerDocument) -> PassengerDocumentDTO:
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


def _map_passenger(p: Passenger) -> PassengerDTO | None:
    if not p.documents:
        return None
    return PassengerDTO(
        passenger_id=p.passenger_id,
        first_name=p.passenger_first_name,
        last_name=p.passenger_last_name,
        sex=p.passenger_sex,
        email=p.passenger_email,
        date_of_birth=p.passenger_date_of_birth,
        documents=[_map_document(d) for d in p.documents],
    )


def validate_document(
    db: Session,
    document_type_id: int | None,
    document_number: str | None,
    document_date_of_issue: date | None,
    document_date_of_expire: date | None,
    date_of_birth: date | None = None,
) -> None:
    if document_type_id is None or document_number is None:
        return

    row = db.execute(
        text("SELECT document_type_code FROM DocumentType WHERE document_type_id = :id"),
        {"id": document_type_id},
    ).fetchone()

    if not row:
        raise ValueError("Invalid document type")

    doc_code = row[0]
    pattern = DOC_FORMATS.get(doc_code)
    if pattern and not re.match(pattern, document_number.upper()):
        raise ValueError(
            f"Invalid document number format for {doc_code}. "
            f"Expected: {DOC_FORMAT_LABELS.get(doc_code, 'unknown')}"
        )

    today = date.today()

    if document_date_of_issue and date_of_birth:
        min_issue = date(date_of_birth.year + 1, 1, 1)
        if document_date_of_issue < min_issue:
            raise ValueError("Document issue date must be at least 1 year after date of birth")

    if document_date_of_issue and document_date_of_issue > today:
        raise ValueError("Document issue date cannot be in the future")

    if document_date_of_issue and document_date_of_expire:
        if document_date_of_expire <= document_date_of_issue:
            raise ValueError("Document expiry date must be after issue date")

def get_all(db: Session, skip: int = 0, limit: int = 50) -> list[PassengerDTO]:
    passengers = passenger_repository.get_all(db, skip, limit)
    return [dto for p in passengers if (dto := _map_passenger(p))]


def get_by_id(db: Session, passenger_id: int) -> PassengerDTO | None:
    p = passenger_repository.get_by_id(db, passenger_id)
    return _map_passenger(p) if p else None


def get_by_document_number(db: Session, document_number: str) -> PassengerDTO | None:
    p = passenger_repository.get_by_document_number(db, document_number)
    return _map_passenger(p) if p else None


def search_passengers(
    db: Session,
    query: str,
    limit: int = 10,
    passenger_type: str | None = None,
    depart_date: date | None = None,
) -> list[PassengerDTO]:
    passengers = passenger_repository.search_partial(db, query, limit * 5)
    
    result =[]
    p_type = passenger_type.lower() if passenger_type else None
    ref_date = depart_date or date.today()
    
    for p in passengers:
        dto = _map_passenger(p)
        if dto is None:
            continue
        
        if p_type:
            if not dto.date_of_birth:
                continue
            
            dob = dto.date_of_birth if isinstance(dto.date_of_birth, date) \
                else date.fromisoformat(str(dto.date_of_birth))
            age = relativedelta(ref_date, dob).years
            
            if p_type == 'adult' and age < 12:
                continue
            elif p_type == 'child' and not (3 <= age <= 11):
                continue
            elif p_type == 'infant' and age > 2: 
                continue
        
        result.append(dto)
        if len(result) >= limit:
            break
    
    return result


def search_documents(
    db: Session,
    query: str,
    limit: int = 10,
    depart_date: date | None = None,
    passenger_type: str | None = None,
) -> list[dict]:
    if not query:
        return[]
        
    docs = passenger_repository.search_documents_partial(db, query, limit * 5)

    min_expire = None
    if depart_date:
        min_expire = depart_date + relativedelta(months=2)

    p_type = passenger_type.lower() if passenger_type else None
    result =[]

    for d in docs:
        if min_expire and (
            d.document_date_of_expire is None or
            d.document_date_of_expire < min_expire
        ):
            continue

        if p_type:
            if not d.passenger.passenger_date_of_birth:
                continue
                
            dob = d.passenger.passenger_date_of_birth
            if not isinstance(dob, date):
                dob = date.fromisoformat(str(dob))
                
            ref_date = depart_date or date.today()
            age = relativedelta(ref_date, dob).years

            if p_type == 'adult' and age < 12:
                continue
            elif p_type == 'child' and not (3 <= age <= 11):
                continue
            elif p_type == 'infant' and age > 2:  
                continue

        result.append({
            "passenger_id":            d.passenger.passenger_id,
            "first_name":              d.passenger.passenger_first_name,
            "last_name":               d.passenger.passenger_last_name,
            "document_number":         d.document_number,
            "document_type_name":      getattr(d.document_type, "document_type_name", None),
            "citizenship_name":        getattr(d.citizenship, "citizenship_name", None),
            "document_date_of_issue":  d.document_date_of_issue,
            "document_date_of_expire": d.document_date_of_expire,
        })
        
        if len(result) >= limit:
            break

    return result

def create_passenger(db: Session, data: PassengerCreateDTO) -> PassengerDTO:
    validate_document(
        db,
        document_type_id=data.document_type_id,
        document_number=data.document_number,
        document_date_of_issue=data.document_date_of_issue,
        document_date_of_expire=data.document_date_of_expire,
        date_of_birth=data.date_of_birth,
    )
    passenger = passenger_repository.create(db, data)
    db.commit()
    return _map_passenger(passenger_repository.get_by_id(db, passenger.passenger_id))


def update_passenger(db: Session, passenger_id: int, data: PassengerUpdateDTO) -> PassengerDTO | None:
    p = passenger_repository.get_by_id(db, passenger_id)
    if not p:
        return None

    date_of_birth = data.date_of_birth or p.passenger_date_of_birth
    validate_document(
        db,
        document_type_id=data.document_type_id,
        document_number=data.document_number,
        document_date_of_issue=data.document_date_of_issue,
        document_date_of_expire=data.document_date_of_expire,
        date_of_birth=date_of_birth,
    )
    passenger_repository.update(db, p, data)
    db.commit()
    return _map_passenger(passenger_repository.get_by_id(db, passenger_id))


def delete_passenger(db: Session, passenger_id: int) -> bool:
    p = passenger_repository.get_by_id(db, passenger_id)
    if not p:
        return False
    passenger_repository.delete(db, p)
    return True


def get_or_create_document_id(db: Session, p_data) -> int:
    def _parse_date(value) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None

    passenger_fields = dict(
        first_name=p_data.first_name,
        last_name=p_data.last_name,
        sex=p_data.sex,
        date_of_birth=_parse_date(p_data.date_of_birth),
        citizenship_id=p_data.citizenship_id,
        document_type_id=p_data.document_type_id,
        document_number=p_data.document_number,
        document_date_of_issue=_parse_date(p_data.document_date_of_issue),
        document_date_of_expire=_parse_date(p_data.document_date_of_expire),
    )

    existing_doc = passenger_repository.get_document_by_number(db, p_data.document_number)
    if existing_doc:
        update_dto = PassengerUpdateDTO(**passenger_fields)
        p = passenger_repository.get_by_id(db, existing_doc.passenger_id)
        if p:
            passenger_repository.update(db, p, update_dto)
        return existing_doc.passenger_document_id

    create_dto = PassengerCreateDTO(**passenger_fields)
    passenger_repository.create(db, create_dto)

    new_doc = passenger_repository.get_document_by_number(db, p_data.document_number)
    if not new_doc:
        raise ValueError(f"Document not found after creation: {p_data.document_number}")
    return new_doc.passenger_document_id
