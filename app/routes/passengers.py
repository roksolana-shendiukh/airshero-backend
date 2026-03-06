from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
import re

from app.repositories.passenger_repository import search_passengers_partial
from app.database import get_db
from app.dependencies.auth import require_role
from app.models.passenger import (
    PassengerDTO,
    PassengerDocumentDTO,
    PassengerCreateDTO,
    PassengerUpdateDTO,
    DOC_FORMATS,
)
from app.repositories import passenger_repository
from app.repositories.queries.passenger_queries import GET_DOCUMENT_TYPE_CODE

router = APIRouter(prefix="/passengers", tags=["Passengers"])


def _validate_document(
    db,
    document_type_id,
    document_number,
    document_date_of_issue,
    document_date_of_expire,
    date_of_birth=None,
):
    if document_type_id is None or document_number is None:
        return

    row = db.execute(
        GET_DOCUMENT_TYPE_CODE,
        {"document_type_id": document_type_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=422, detail="Invalid document type")

    doc_code = row[0]

    pattern = DOC_FORMATS.get(doc_code)
    if pattern and not re.match(pattern, document_number.upper()):
        formats = {
            'PAS': 'AB1234567 (2 letters + 7 digits)',
            'INT': 'AB1234567 (2 letters + 7 digits)',
            'OFF': 'A1234567 (1 letter + 7 digits)',
            'ID':  '123456789 (9 digits)',
        }
        raise HTTPException(
            status_code=422,
            detail=f"Invalid document number format for {doc_code}. Expected: {formats.get(doc_code, 'unknown')}"
        )

    today = date.today()

    if document_date_of_issue and date_of_birth:
        min_issue = date(date_of_birth.year + 1, 1, 1)
        if document_date_of_issue < min_issue:
            raise HTTPException(
                status_code=422,
                detail="Document issue date must be at least 1 year after date of birth"
            )

    if document_date_of_issue and document_date_of_issue > today:
        raise HTTPException(
            status_code=422,
            detail="Document issue date cannot be in the future"
        )

    if document_date_of_issue and document_date_of_expire:
        if document_date_of_expire <= document_date_of_issue:
            raise HTTPException(
                status_code=422,
                detail="Document expiry date must be after issue date"
            )


@router.get("/search", response_model=PassengerDTO)
def search_passenger(
    document_number: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    passenger = passenger_repository.get_passenger_by_document_number(db, document_number)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return passenger


@router.get("/search/suggestions")
def search_document_suggestions(q: str, db: Session = Depends(get_db)):
    return passenger_repository.search_documents_partial(db, q)

@router.get("", response_model=list[PassengerDTO])
def get_passengers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return passenger_repository.get_all_passengers(db, skip=skip, limit=limit)


@router.get("/{passenger_id}", response_model=PassengerDTO)
def get_passenger(
    passenger_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    passenger = passenger_repository.get_passenger_by_id(db, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return passenger


@router.post("", response_model=PassengerDTO, status_code=201)
def create_passenger(
    data: PassengerCreateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    _validate_document(
        db,
        document_type_id=data.document_type_id,
        document_number=data.document_number,
        document_date_of_issue=data.document_date_of_issue,
        document_date_of_expire=data.document_date_of_expire,
        date_of_birth=data.date_of_birth,
    )
    try:
        passenger_id = passenger_repository.create_passenger(db, data)
        return passenger_repository.get_passenger_by_id(db, passenger_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Document number already exists")


@router.put("/{passenger_id}", response_model=PassengerDTO)
def update_passenger(
    passenger_id: int,
    data: PassengerUpdateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    date_of_birth = data.date_of_birth
    if date_of_birth is None:
        existing = passenger_repository.get_passenger_by_id(db, passenger_id)
        if existing:
            date_of_birth = existing.date_of_birth

    _validate_document(
        db,
        document_type_id=data.document_type_id,
        document_number=data.document_number,
        document_date_of_issue=data.document_date_of_issue,
        document_date_of_expire=data.document_date_of_expire,
        date_of_birth=date_of_birth,
    )
    try:
        ok = passenger_repository.update_passenger(db, passenger_id, data)
        if not ok:
            raise HTTPException(status_code=404, detail="Passenger not found")
        return passenger_repository.get_passenger_by_id(db, passenger_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Document number already exists")


@router.delete("/{passenger_id}", response_model=dict)
def delete_passenger(
    passenger_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    ok = passenger_repository.delete_passenger(db, passenger_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return {"success": True}