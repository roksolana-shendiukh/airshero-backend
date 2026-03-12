from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.passenger_schema import PassengerDTO, PassengerCreateDTO, PassengerUpdateDTO
from app.services import passenger_service

router = APIRouter(prefix="/passengers", tags=["Passengers"])


@router.get("/search", response_model=PassengerDTO)
def search_passenger(
    document_number: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    passenger = passenger_service.get_by_document_number(db, document_number)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return passenger


@router.get("/search/suggestions")
def search_document_suggestions(q: str, db: Session = Depends(get_db)):
    return passenger_service.search_documents(db, q)


@router.get("", response_model=list[PassengerDTO])
def get_passengers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return passenger_service.get_all(db, skip=skip, limit=limit)


@router.get("/{passenger_id}", response_model=PassengerDTO)
def get_passenger(
    passenger_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    passenger = passenger_service.get_by_id(db, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return passenger


@router.post("", response_model=PassengerDTO, status_code=201)
def create_passenger(
    data: PassengerCreateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        return passenger_service.create_passenger(db, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Document number already exists")


@router.put("/{passenger_id}", response_model=PassengerDTO)
def update_passenger(
    passenger_id: int,
    data: PassengerUpdateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = passenger_service.update_passenger(db, passenger_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Passenger not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Document number already exists")


@router.delete("/{passenger_id}", response_model=dict)
def delete_passenger(
    passenger_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    ok = passenger_service.delete_passenger(db, passenger_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return {"success": True}